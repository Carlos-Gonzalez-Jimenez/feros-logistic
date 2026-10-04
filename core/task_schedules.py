from django.utils.timezone import now

from core import models


def update_invoice_status():
    models.Invoice.objects \
        .filter(status=models.Invoice.InvoiceStatus.Pending, expiration_date__lte=now()) \
        .update(status=models.Invoice.InvoiceStatus.Expired)
