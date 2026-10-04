from django.core.cache import cache
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Booking, Container
from .status_manager import BookingStatusManager


@receiver(post_save, sender=Booking, dispatch_uid='core.change_booking_status')
def change_booking_status(sender, instance, created, **kwargs):
    if not created and cache.add(f'booking.id.{instance.pk}', instance.pk, timeout=3):
        BookingStatusManager(instance).change_status()


@receiver(post_save, sender=Container, dispatch_uid='core.change_containers_booking_status')
def change_containers_booking_status(sender, instance, created, **kwargs):
    if cache.add(f'booking.id.{instance.pk}', instance.pk, timeout=3):
        BookingStatusManager(instance.booking).change_status()
