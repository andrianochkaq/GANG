from django.core.management.base import BaseCommand, CommandError

from apps.products.services.catalog_loader import (
    DEFAULT_CATALOG_PATH,
    CatalogFileError,
    load_catalog_file,
)


class Command(BaseCommand):
    help = (
        "Load the product catalog (categories, about 500 products with "
        "nutrition). Safe to run again: it updates rows and never duplicates."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            default=str(DEFAULT_CATALOG_PATH),
            help="Catalog JSON file. Default: the bundled catalog_uk.json.",
        )

    def handle(self, *args, **options):
        try:
            result = load_catalog_file(options["file"])
        except CatalogFileError as error:
            raise CommandError(str(error)) from error
        self.stdout.write(
            self.style.SUCCESS(
                f"Categories: {result.categories_created} created, "
                f"{result.categories_updated} updated. "
                f"Products: {result.products_created} created, "
                f"{result.products_updated} updated, "
                f"{result.products_unchanged} unchanged."
            )
        )
