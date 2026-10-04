from django.utils.timezone import now

from core import models


class BookingStatusManager:
    status_order = [
        models.Booking.BookingStatus.Canceled,
        models.Booking.BookingStatus.Active,
        models.Booking.BookingStatus.ReadyToShip,
        models.Booking.BookingStatus.In_Transit,
        models.Booking.BookingStatus.Arrived,
    ]

    booking: models.Booking

    def __init__(self, booking):
        self.booking = booking

    def get_next_statues(self):
        statues = []
        found = False
        for status in self.status_order:
            if found:
                statues.append(status)
            if status in self.booking.status:
                found = True
        return statues

    def _ready_to_ship_status(self):
        return bool(self.booking.containers.count())

    def _in_transit_status(self):
        today = now().date()
        return self.booking.ets <= today and today <= self.booking.eta

    def _arrived_status(self):
        return self.booking.containers.filter(discharge_date__isnull=False).exists()

    def change_status(self):
        initial_status = self.booking.status
        for status in self.get_next_statues():
            call = getattr(self, f'_{status}_status', None)
            if callable(call) and call():
                self.booking.status = status

        if self.booking.status != initial_status:
            self.booking.save()
