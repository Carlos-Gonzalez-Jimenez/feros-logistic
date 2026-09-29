from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from core import models
from core.serializers import BookingMinimalSerializer, ContainerMinimalSerializer


class DashboardDatesSerializer(serializers.Serializer):
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(default=timezone.now)

    def validate(self, data):
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError(
                {"start_date": _("The start date cannot be later than the end date.")}
            )

        if start_date and end_date:
            delta = (end_date - start_date).days
            if delta > 90:
                raise serializers.ValidationError(
                    {"date_range": _("The date range cannot exceed 90 days.")}
                )

        return data


class DashboardDaysRangeSerializer(serializers.Serializer):
    days = serializers.IntegerField(min_value=1, default=365, max_value=365)


class DashboardBookingDaysSerializer(DashboardDaysRangeSerializer):
    shipping_company = serializers.PrimaryKeyRelatedField(
        queryset=models.ShippingCompany.objects.all(),
        allow_null=True)


class DashboardBookingMetricSerializer(serializers.Serializer):
    active_bookings = BookingMinimalSerializer(many=True)
    containers_in_transit = ContainerMinimalSerializer(many=True)
    upcoming_departures = BookingMinimalSerializer(many=True)
    upcoming_arrivals = BookingMinimalSerializer(many=True)
    totals = serializers.SerializerMethodField()

    def get_totals(self, obj):
        totals = dict()
        for key, val in obj.items():
            totals[key] = val.count()
        return totals