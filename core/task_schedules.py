from django.utils.timezone import now

from core import models
from core.status_manager import BookingStatusManager


def update_invoice_status():
    models.Invoice.objects \
        .filter(status=models.Invoice.InvoiceStatus.Pending, expiration_date__lte=now()) \
        .update(status=models.Invoice.InvoiceStatus.Expired)


def update_booking_status():
    statues = models.Booking.BookingStatus
    bookings = models.Booking.objects.prefetch_related('containers') \
        .exclude(status__in=[statues.Canceled, statues.Arrived]).all()
    for booking in bookings:
        BookingStatusManager(booking).change_status()
