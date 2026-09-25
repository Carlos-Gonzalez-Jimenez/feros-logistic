from django.db.models import Q
from django_filters import (
    ModelChoiceFilter,
    ModelMultipleChoiceFilter,
)
from django_filters import rest_framework as filters

from core.models import (
    Product,
    Category,
    Brand,
    Country,
    NotificationUser, Provider, ProductProviderPresentation, Invoice, InvoicePayment, Booking, Container,
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


class NotificationUserFilter(filters.FilterSet):
    user = ModelChoiceFilter(queryset=User.objects.all(), field_name="user")

    class Meta:
        model = NotificationUser
        fields = ["user"]


class ProductProviderPresentationFilter(filters.FilterSet):
    provider = ModelChoiceFilter(queryset=Provider.objects.all(), field_name="product_provider__provider")

    class Meta:
        model = ProductProviderPresentation
        fields = ['provider']


class InvoicePaymentFilter(filters.FilterSet):
    invoice = ModelChoiceFilter(queryset=Invoice.objects.all(), field_name="invoice")

    class Meta:
        model = InvoicePayment
        fields = ['invoice']


class ContainerFilter(filters.FilterSet):
    booking = ModelChoiceFilter(queryset=Booking.objects.all(), field_name="booking")

    class Meta:
        model = Container
        fields = ['booking']
