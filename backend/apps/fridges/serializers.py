"""Serializers of the fridges API."""

from rest_framework import serializers

from .models import Fridge, FridgeRole

FRIDGE_NAME_MAX_LENGTH = 100


class FridgeNameSerializer(serializers.Serializer):
    """The name a fridge is created with or renamed to."""

    name = serializers.CharField(max_length=FRIDGE_NAME_MAX_LENGTH)


class FridgeSerializer(serializers.ModelSerializer):
    """A fridge as the signed-in user sees it.

    The queryset must carry ``member_count`` and ``product_count``
    (``annotate_fridge_summary``) and the context must carry the user and
    ``current_fridge_id``.
    """

    role = serializers.SerializerMethodField()
    member_count = serializers.IntegerField(read_only=True)
    product_count = serializers.IntegerField(read_only=True)
    is_current = serializers.SerializerMethodField()

    class Meta:
        model = Fridge
        fields = [
            "id",
            "name",
            "role",
            "member_count",
            "product_count",
            "is_current",
            "created_at",
        ]
        read_only_fields = fields

    def get_role(self, fridge) -> str:
        user = self.context["request"].user
        return FridgeRole.OWNER if fridge.owner_id == user.pk else FridgeRole.MEMBER

    def get_is_current(self, fridge) -> bool:
        return fridge.pk == self.context["current_fridge_id"]
