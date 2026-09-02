from django_filters import rest_framework as filters
from payments import models


class PaymentMethodFilter(filters.FilterSet):
    active = filters.BooleanFilter(field_name="active")
    use_in_pos = filters.BooleanFilter(field_name="use_in_pos")
    use_in_store = filters.BooleanFilter(field_name="use_in_store")

    class Meta:
        model = models.PaymentMethod
        fields = ["active", "use_in_pos", "use_in_store"]
