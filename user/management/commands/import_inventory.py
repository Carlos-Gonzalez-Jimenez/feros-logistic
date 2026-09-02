from django.db import transaction

from decimal import Decimal
import requests
import pandas as pd
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from core.models import (
    Measurement_Unit,
    Product,
    Brand,
    Provider,
    Country,
    Category,
    Cart,
)
from .settings import APPLICATION_DATA_PATH

# python manage.py import_inventory


class Command(BaseCommand):
    """script to import full inventory

    Args:
        BaseCommand (_type_): _description_
    """

    help = "import full inventory for production release."

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("importing full inventory..."))
        self.run_import_inventory()
        self.stdout.write(self.style.WARNING("done."))

    def check_provider_existence(self, provider_name: str) -> Provider:
        """_summary_

        Args:
            provider (str): _description_

        Returns:
            Provider: _description_
        """
        try:
            provider = Provider.objects.get(name=provider_name)
        except Provider.DoesNotExist:
            provider = Provider(name=provider_name)
            provider.save()
        return provider

    def check_brand_existence(self, brand_name: str) -> Brand:
        """_summary_

        Args:
            brand_name (str): _description_

        Returns:
            Brand: _description_
        """
        try:
            brand = Brand.objects.get(name=brand_name)
        except Brand.DoesNotExist:
            brand = Brand(name=brand_name)
            brand.save()
        return brand

    def check_product_category_existence(self, product_category: str) -> Category:
        """check for a product category existence

        Args:
            product_category (str): category name

        Returns:
            Category: an existence category
        """
        try:
            category = Category.objects.get(name=product_category)
        except Category.DoesNotExist:
            category = Category(name=product_category)
            category.save()
        return category

    def check_measurement_unit_existence(
        self, measurement_unit_name: str
    ) -> Measurement_Unit:
        """check for a measurement unit existence

        Args:
            measurement_unit_name (str): measurement unit name

        Returns:
            Measument_Unit: an existence measurement unit
        """
        try:
            measurement_unit = Measurement_Unit.objects.get(name=measurement_unit_name)
        except Measurement_Unit.DoesNotExist:
            measurement_unit = Measurement_Unit(name=measurement_unit_name)
            measurement_unit.save()
        return measurement_unit

    def clean_related_data(self):
        Cart.objects.all().delete()
        Product.objects.all().delete()
        Category.objects.filter(parent__isnull=False).delete()
        Category.objects.all().delete()
        Measurement_Unit.objects.all().delete()
        # Brand.objects.all().delete()
        Provider.objects.all().delete()

    def create_products(self):
        """Create products"""

        self.stdout.write(self.style.NOTICE("start importing full inventory"))

        excel = pd.read_excel(
            APPLICATION_DATA_PATH + "Productos.xlsx",
            engine="openpyxl",
        ).fillna("")

        # .clean_related_data()

        consecutive_number = 1
        for index, _ in excel.iterrows():
            # provider_name = excel.at[index, excel.columns[0]].strip()
            # brand_name = excel.at[index, excel.columns[1]].strip()
            name = excel.at[index, excel.columns[1]].strip()
            part_code = str(excel.at[index, excel.columns[2]]).strip()
            product_category = excel.at[index, excel.columns[6]].strip()
            measurement_unit_name = "UNIDAD"
            # country_name = excel.at[index, excel.columns[6]].strip()
            code_sku = f"SM-{consecutive_number:04d}"
            # net_content = excel.at[index, excel.columns[7]].strip()
            box_quantity = excel.at[index, excel.columns[3]]
            quantity = excel.at[index, excel.columns[4]]
            unit_price = excel.at[index, excel.columns[5]]

            description = ""
            measurement_unit = self.check_measurement_unit_existence(
                measurement_unit_name
            )
            category = self.check_product_category_existence(product_category)
            # provider = self.check_provider_existence(provider_name)
            # brand = self.check_brand_existence(brand_name)
            # country = Country.objects.get(code_alpha3=country_name)

            products = Product.objects.filter(code_sku=code_sku)
            if products.exists():
                product = products.first()
            else:
                product = Product(
                    code_sku=code_sku,
                    name=f"{name} [{part_code}]",
                    slug=slugify(f"{name}-{part_code}"),
                    quantity=Decimal(str(quantity)),
                    unit_price=Decimal(str(unit_price)),
                    measurement_unit=measurement_unit,
                    # net_content=net_content,
                    category=category,
                    quantity_per_box=Decimal(str(box_quantity)),
                    # brand=brand,
                    # provider=provider,
                    # country=country,
                    description=description,
                )
                product.save()
                consecutive_number += 1

    def ODOO_integration(self):
        _headers = {"X-Api-Key": "XfmV9SbZsm5pKaE9mgagJQjpQThnqaA9TxJpAQb9"}
        _api_url = "https://osmel810807f-odooferoz.odoo.com/api/v1"
        try:
            response = requests.get(
                f"{_api_url}/products",
                headers=_headers,
                # params={"state": "completed"},
            )
            response.raise_for_status()
            print(response.json())
        except requests.exceptions.RequestException as exception:
            print(exception)

    def run_import_inventory(self):
        """import full inventory"""
        with transaction.atomic():
            # self.create_products()
            self.ODOO_integration()
