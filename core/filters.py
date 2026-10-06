from django.db.models import Q
from django_filters import (
    ModelChoiceFilter,
    ModelMultipleChoiceFilter,
    CharFilter,
    BooleanFilter,
)
from django_filters import rest_framework as filters

from core.models import (
    Product,
    Category,
    Brand,
    Country,
    NotificationUser,
    Provider,
    ProductProviderPresentation,
    Invoice,
    InvoicePayment,
    Booking,
    Container,
    SaleOrderItems, CustomerInvoice, ContainerType, SaleOrder,
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
    provider = ModelChoiceFilter(
        queryset=Provider.objects.all(), field_name="product_provider__provider"
    )

    class Meta:
        model = ProductProviderPresentation
        fields = ["provider", "active"]


class InvoicePaymentFilter(filters.FilterSet):
    invoice = ModelChoiceFilter(queryset=Invoice.objects.all(), field_name="invoice")

    class Meta:
        model = InvoicePayment
        fields = ["invoice"]


class ContainerFilter(filters.FilterSet):
    booking = ModelChoiceFilter(queryset=Booking.objects.all(), field_name="booking")
    customer_invoice = ModelChoiceFilter(queryset=CustomerInvoice.objects.all(), field_name="customer_invoice")
    container_type = ModelChoiceFilter(queryset=ContainerType.objects.all(), field_name="container_type")
    container_number = CharFilter(lookup_expr="icontains")
    in_transit = BooleanFilter(method="filter_in_transit")

    class Meta:
        model = Container
        fields = ["booking", "container_type", "container_number"]

    def filter_in_transit(self, queryset, name, value):
        if value:
            return queryset.filter(
                booking__cancelled_at__isnull=True,
                discharge_date__isnull=True,
            )
        return queryset


class SaleOrderItemsFilter(filters.FilterSet):
    without_bill = filters.BooleanFilter(field_name="invoices", lookup_expr="isnull")
    booking = ModelChoiceFilter(queryset=Booking.objects.all(), method="filter_by_booking")

    def filter_by_booking(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(sale_order__bookings=value).distinct()

    class Meta:
        model = SaleOrderItems
        fields = ["booking", "without_bill"]


class BookingFilter(filters.FilterSet):
    has_invoice = filters.BooleanFilter(field_name="invoices", lookup_expr="isnull", method="filter_has_invoice",
                                        distinct=True)

    def filter_has_invoice(self, queryset, name, value):
        return queryset.exclude(invoices__isnull=value, status=Booking.BookingStatus.Canceled)

    class Meta:
        model = Booking
        fields = ['has_invoice']


class SaleOrderFilter(filters.FilterSet):
    has_invoice = filters.BooleanFilter(field_name="invoices", lookup_expr="isnull", method="filter_has_invoice",
                                        distinct=True)

    def filter_has_invoice(self, queryset, name, value):
        return queryset.filter(invoices__isnull=not value, invoices__cancelation_date__isnull=True)

    class Meta:
        model = SaleOrder
        fields = ['has_invoice']
