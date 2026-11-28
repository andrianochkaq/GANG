"""Stock rules: add, change, consume and remove fridge items.

Every function that changes stock runs in one transaction and locks the
fridge row first, so two people changing the same fridge at once wait for
each other and the quantities add up. The rules:

* a quantity is never zero or negative: an item that is used up is removed;
* every change of quantity writes exactly one ``StockMovement``;
* adding a product that is already in the fridge with the same unit and
  expiry date raises its quantity instead of making a second item.
"""

from dataclasses import dataclass

from django.db import transaction

from apps.fridges.models import Fridge
from apps.products.models import Category, FridgeItem, StockMovement, StockReason
from apps.products.services.units import UnitConversionError, convert_quantity

OTHER_CATEGORY_SLUG = "other"


class QuantityBelowZeroError(Exception):
    """More was taken out than the fridge holds."""

    def __init__(self, available):
        super().__init__(f"Only {available} is left.")
        self.available = available


class CategoryRequiredError(Exception):
    """No category was given and none can be worked out."""


class ItemNotFoundError(Exception):
    """The item is gone: someone removed it a moment ago."""


@dataclass(frozen=True)
class AddedItem:
    """An item after an add, and whether the add made it or raised it."""

    item: FridgeItem
    is_new: bool


def filter_items(items, category_slug=None, search=None):
    """Narrow a queryset of fridge items by category slug and name text."""
    if category_slug:
        items = items.filter(category__slug=category_slug)
    if search and search.strip():
        items = items.filter(name__icontains=search.strip())
    return items


def add_item(
    fridge,
    user,
    *,
    name,
    quantity,
    unit,
    catalog_product=None,
    category=None,
    expires_at=None,
    opened_at=None,
    reason=StockReason.MANUAL,
):
    """Add a product to the fridge; see the module text for merging."""
    with transaction.atomic():
        _lock_fridge(fridge)
        return _add_locked(
            fridge,
            user,
            reason,
            name=name,
            quantity=quantity,
            unit=unit,
            catalog_product=catalog_product,
            category=category,
            expires_at=expires_at,
            opened_at=opened_at,
        )


def add_items(fridge, user, lines, reason=StockReason.MANUAL):
    """Add several products in one transaction: all of them or none.

    Each line is a dict with the arguments of ``add_item`` (without
    ``reason``). Two lines that match merge into one item.
    """
    with transaction.atomic():
        _lock_fridge(fridge)
        added = [_add_locked(fridge, user, reason, **line) for line in lines]
        # An item that several lines touched must show its final quantity.
        final_items = FridgeItem.objects.select_related("category").in_bulk(
            [entry.item.pk for entry in added]
        )
        return [
            AddedItem(item=final_items[entry.item.pk], is_new=entry.is_new)
            for entry in added
        ]


def update_item(item, user, *, reason=StockReason.MANUAL, **changes):
    """Change fields of an item; a new quantity writes one movement.

    ``changes`` may hold name, catalog_product, category, quantity,
    expires_at and opened_at. The unit cannot change here (see FC-306).
    """
    with transaction.atomic():
        _lock_fridge(item.fridge)
        locked_item = _lock_item(item)
        old_quantity = locked_item.quantity
        for field_name, value in changes.items():
            setattr(locked_item, field_name, value)
        locked_item.save()
        delta = locked_item.quantity - old_quantity
        if delta != 0:
            _record_movement(locked_item, user, delta, locked_item.quantity, reason)
        return locked_item


def consume_item(item, user, amount, reason=StockReason.MANUAL, unit=None):
    """Take an amount out of an item.

    ``unit`` is the unit of ``amount``; it defaults to the item's own unit
    and any unit that converts to it is accepted (``UnitConversionError``
    otherwise). The movement is written in the item's unit.

    Returns the item, or ``None`` when nothing is left and the item was
    removed. Asking for more than the item holds raises
    ``QuantityBelowZeroError`` and changes nothing.
    """
    with transaction.atomic():
        _lock_fridge(item.fridge)
        locked_item = _lock_item(item)
        if unit is not None:
            amount = convert_quantity(
                amount, unit, locked_item.unit, locked_item.catalog_product
            )
            if amount <= 0:
                raise UnitConversionError(unit, locked_item.unit)
        if amount > locked_item.quantity:
            raise QuantityBelowZeroError(locked_item.quantity)
        locked_item.quantity -= amount
        _record_movement(locked_item, user, -amount, locked_item.quantity, reason)
        if locked_item.quantity == 0:
            locked_item.delete()
            return None
        locked_item.save(update_fields=["quantity"])
        return locked_item


def delete_item(item, user):
    """Remove an item and whatever is left of it, and record that."""
    with transaction.atomic():
        _lock_fridge(item.fridge)
        locked_item = _lock_item(item)
        _record_movement(
            locked_item, user, -locked_item.quantity, 0, StockReason.MANUAL
        )
        locked_item.delete()


def _lock_fridge(fridge):
    Fridge.objects.select_for_update().get(pk=fridge.pk)


def _lock_item(item):
    try:
        return FridgeItem.objects.select_for_update().get(pk=item.pk)
    except FridgeItem.DoesNotExist as error:
        raise ItemNotFoundError from error


def _add_locked(
    fridge,
    user,
    reason,
    *,
    name,
    quantity,
    unit,
    catalog_product=None,
    category=None,
    expires_at=None,
    opened_at=None,
):
    existing_item = _find_same_item(fridge, name, catalog_product, unit, expires_at)
    if existing_item is not None:
        existing_item.quantity += quantity
        existing_item.save(update_fields=["quantity"])
        _record_movement(existing_item, user, quantity, existing_item.quantity, reason)
        return AddedItem(item=existing_item, is_new=False)
    item = FridgeItem.objects.create(
        fridge=fridge,
        name=name,
        catalog_product=catalog_product,
        category=_resolve_category(category, catalog_product),
        quantity=quantity,
        unit=unit,
        expires_at=expires_at,
        opened_at=opened_at,
        added_by=user,
    )
    _record_movement(item, user, quantity, item.quantity, reason)
    return AddedItem(item=item, is_new=True)


def _find_same_item(fridge, name, catalog_product, unit, expires_at):
    """Find the item a new product would merge into, if there is one."""
    items = FridgeItem.objects.select_for_update().filter(
        fridge=fridge,
        unit=unit,
        expires_at=expires_at,
    )
    if catalog_product is not None:
        items = items.filter(catalog_product=catalog_product)
    else:
        items = items.filter(catalog_product__isnull=True, name__iexact=name)
    return items.order_by("created_at", "id").first()


def _resolve_category(category, catalog_product):
    """Use the category given, else the product's, else «Інше»."""
    if category is not None:
        return category
    if catalog_product is not None:
        return catalog_product.category
    other_category = Category.objects.filter(slug=OTHER_CATEGORY_SLUG).first()
    if other_category is None:
        raise CategoryRequiredError
    return other_category


def _record_movement(item, user, delta, quantity_after, reason):
    return StockMovement.objects.create(
        fridge_id=item.fridge_id,
        item=item,
        item_name=item.name,
        unit=item.unit,
        delta=delta,
        quantity_after=quantity_after,
        reason=reason,
        user=user,
    )
