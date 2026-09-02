from django.core.management.base import BaseCommand

from core.services import WAHAService


class Command(BaseCommand):
    """script to seed database

    Args:
        BaseCommand (_type_): _description_
    """

    help = "Upgrade the database with data for fix and generate information."

    def handle(self, *args, **options):
        chat_id = "5354266836@c.us"
        message = """
         *Nueva solicitud de compra*\nSe ha creado una solicitud de compra *39* desde el punto de venta para el cliente *Cliente Feros Grupo S.U.R.L.*"""
        WAHAService.dev_initialized()
        WAHAService.send_text(chat_id, message)
