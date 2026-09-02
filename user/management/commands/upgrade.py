from django.core.management.base import BaseCommand

from core.models import ProductImageOrder


class Command(BaseCommand):
    """script to seed database

    Args:
        BaseCommand (_type_): _description_
    """

    help = "Upgrade the database with data for fix and generate information."

    def handle(self, *args, **options):
        data = [
            {"product_id": 1, "blockmedia_id": 7},
            {"product_id": 1, "blockmedia_id": 90},
            {"product_id": 2, "blockmedia_id": 87},
            {"product_id": 2, "blockmedia_id": 88},
            {"product_id": 2, "blockmedia_id": 89},
            {"product_id": 3, "blockmedia_id": 73},
            {"product_id": 3, "blockmedia_id": 86},
            {"product_id": 4, "blockmedia_id": 74},
            {"product_id": 4, "blockmedia_id": 82},
            {"product_id": 5, "blockmedia_id": 6},
            {"product_id": 6, "blockmedia_id": 21},
            {"product_id": 7, "blockmedia_id": 12},
            {"product_id": 8, "blockmedia_id": 18},
            {"product_id": 9, "blockmedia_id": 20},
            {"product_id": 10, "blockmedia_id": 19},
            {"product_id": 11, "blockmedia_id": 75},
            {"product_id": 11, "blockmedia_id": 85},
            {"product_id": 12, "blockmedia_id": 72},
            {"product_id": 12, "blockmedia_id": 80},
            {"product_id": 13, "blockmedia_id": 78},
            {"product_id": 13, "blockmedia_id": 83},
            {"product_id": 14, "blockmedia_id": 76},
            {"product_id": 14, "blockmedia_id": 81},
            {"product_id": 15, "blockmedia_id": 77},
            {"product_id": 15, "blockmedia_id": 84},
            {"product_id": 16, "blockmedia_id": 71},
            {"product_id": 16, "blockmedia_id": 79},
            {"product_id": 17, "blockmedia_id": 92},
            {"product_id": 17, "blockmedia_id": 93}
        ]

        for d in data:
            ProductImageOrder.objects.create(**d)
