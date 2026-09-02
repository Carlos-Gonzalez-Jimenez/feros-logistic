from django_filters import (
    ModelMultipleChoiceFilter,
)
from django_filters import rest_framework as filters
from delivery.models import ShippingRate, ShippingMethod


class ShippingRateFilter(filters.FilterSet):
    shipping_method = ModelMultipleChoiceFilter(
        queryset=ShippingMethod.objects.all(),
    )

    class Meta:
        model = ShippingRate
        fields = ["shipping_method"]
