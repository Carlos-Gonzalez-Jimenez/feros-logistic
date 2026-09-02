from django.core.management.base import BaseCommand

from core.odoo import OdooAPIServices, sync_inventory


# python manage.py import_inventory


class Command(BaseCommand):
    """script to import full inventory

    Args:
        BaseCommand (_type_): _description_
    """

    help = "import full inventory from odoo."

    def handle(self, *args, **options):
        print(sync_inventory())
