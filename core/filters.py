from django.db.models import Q, OuterRef, Subquery
from django_filters import (
    ModelChoiceFilter,
    ModelMultipleChoiceFilter,
    BooleanFilter,
)
from django_filters import rest_framework as filters

from core.models import (
    Product,
    Category,
    Brand,
    Country,
    NotificationUser,
    Municipality,
    Province,
    Order,
    OrderStatus,
    OrderTracking, Batch,
)
from user.models import User


class ProductFilter(filters.FilterSet):
    category = ModelMultipleChoiceFilter(
        queryset=Category.objects.all(), field_name="category", method="filter_category"
    )

    def filter_category(self, queryset, name, value):
        if len(value) != 0:
            return queryset.filter(
                Q(category__in=value) | Q(category__parent__in=value)
            )
        return queryset

    search = filters.CharFilter(
        method="filter_keyword",
    )

    def filter_keyword(self, queryset, name, value):
        if not value or not value.strip():
            return queryset

        search_term = value.strip()

        return queryset.filter(
            Q(name__icontains=search_term) | Q(description__icontains=search_term)
        ).distinct()

    brand = ModelMultipleChoiceFilter(
        queryset=Brand.objects.all(), field_name="brand", method="filter_brand"
    )

    def filter_brand(self, queryset, name, value):
        if len(value) != 0:
            return queryset.filter(Q(brand__in=value) | Q(brand__parent__in=value))
        return queryset

    country = ModelMultipleChoiceFilter(
        queryset=Country.objects.all(), field_name="country"
    )

    active = filters.BooleanFilter(field_name="active")

    class Meta:
        model = Product
        fields = ["category", "brand", "country", "active"]


class OrderFilter(filters.FilterSet):
    user = filters.NumberFilter(field_name="client_id")

    status = filters.ModelChoiceFilter(
        queryset=OrderStatus.objects.all(),
        method="filter_by_current_status",
    )

    delivery_type = filters.ChoiceFilter(
        choices=[
            ('all', "Todos"),
            ('with_delivery', "Con mensajería"),
            ('pickup', "Recogida en tienda")
        ],
        method="filter_delivery_type",
    )

    class Meta:
        model = Order
        fields = ["user", "status", "delivery_type", "creation_date", "expiration_date"]

    def filter_delivery_type(self, queryset, name, value):
        if value == "with_delivery":
            return queryset.filter(shipping__isnull=False)
        elif value == "pickup":
            return queryset.filter(shipping__isnull=True)
        else:
            return queryset

    def filter_by_current_status(self, queryset, name, value):
        if value is None:
            return queryset
        latest_tracking = Subquery(
            OrderTracking.objects.filter(
                order=OuterRef('pk')
            ).order_by('-id').values('status_id')[:1]
        )

        return queryset.annotate(
            latest_status=latest_tracking
        ).filter(latest_status=value.id)


class PendingOrderFilter(OrderFilter):
    expiration_date = filters.DateFilter(lookup_expr='gte')

    class Meta(OrderFilter.Meta):
        fields = ['expiration_date'] + OrderFilter.Meta.fields


class NotificationUserFilter(filters.FilterSet):
    user = ModelChoiceFilter(queryset=User.objects.all(), field_name="user")

    class Meta:
        model = NotificationUser
        fields = ["user"]


class MunicipalityFilter(filters.FilterSet):
    province = ModelChoiceFilter(
        queryset=Province.objects.all(),
        field_name="province",
    )

    class Meta:
        model = Municipality
        fields = ["province"]


class StatusFilter(filters.FilterSet):
    initial = BooleanFilter(field_name="initial_status")
    final = BooleanFilter(field_name="final_status")
    store = BooleanFilter(field_name="store_status")
    delivery = BooleanFilter(field_name="delivery_status")

    class Meta:
        model = OrderStatus
        fields = [
            "initial",
            "final",
            "store",
            "delivery",
        ]


class BatchFilter(filters.FilterSet):
    class Meta:
        model = Batch
        fields = ['processed', 'completed']
