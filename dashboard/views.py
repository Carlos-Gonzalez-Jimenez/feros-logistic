from datetime import timedelta
from decimal import Decimal

from django.db.models import (
    Count,
    F,
    Sum,
)
from django.utils.timezone import now
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from core import models, serializers
from core.models import Booking
from core.permissions import CustomPermissionFactory, ReadOnlyPermission
from dashboard.serializers import DashboardDatesSerializer, DashboardBookingMetricSerializer, \
    DashboardDaysRangeSerializer, \
    DashboardBookingDaysSerializer


def alert_level(variation_pct: Decimal) -> str:
    """Clasifica la variación."""

    if variation_pct >= Decimal("15"):
        return "critical"
    if variation_pct >= Decimal("5"):
        return "warning"
    if variation_pct <= Decimal("-5"):
        return "favorable"
    return "normal"


def _get_request_date(request):
    _serializer = DashboardDaysRangeSerializer(data=request.GET)
    _serializer.is_valid(raise_exception=True)
    validated_data = _serializer.validated_data
    return now().date() - timedelta(days=(validated_data["days"] * -1))


def _get_request_dates(request):
    _serializer = DashboardDatesSerializer(data=request.GET)
    _serializer.is_valid(raise_exception=True)
    validated_data = _serializer.validated_data
    return validated_data["start_date"], validated_data["end_date"]


class DashboardBookingViewSet(viewsets.GenericViewSet):
    """
    View to handle all booking-containers related actions in dashboard.

    All reports are handled via methods with @action decorator in which Bookings can be filtered
    by start_date, end_date aand shipping_company.
    """

    permission_classes = [
        ReadOnlyPermission
        | CustomPermissionFactory(["user.show_all_boards", "user.show_own_board"])
    ]

    def __get_start_date_and_shipping_company(self, request):
        _serializer = DashboardBookingDaysSerializer(data=request.GET)
        _serializer.is_valid(raise_exception=True)
        validated_data = _serializer.validated_data
        return (now().date() - timedelta(days=validated_data["days"])), validated_data['shipping_company']

    @action(methods=["GET"], detail=False, url_path="booking-metrics")
    def get_booking_metrics(self, request):
        """
        Dashboard operativo : bookings activos, contenedores en tránsito, próximas salidas, próximos arribos
        """

        start_date, shipping_company_id = self.__get_start_date_and_shipping_company(request)

        bookings = (
            models.Booking.objects.select_related("port_loading", "port_discharge", "shipping_company", "vessel")
            .prefetch_related("sale_orders")
            .exclude(status__in=[models.Booking.BookingStatus.Canceled, models.Booking.BookingStatus.Arrived])
            .annotate(containers_count=Count("containers", distinct=True))
        )
        if shipping_company_id is not None:
            bookings = bookings.filter(shipping_company_id=shipping_company_id)

        containers = models.Container.objects.select_related("booking", "booking__shipping_company", "container_type")

        if shipping_company_id is not None:
            containers = containers.filter(booking__shipping_company_id=shipping_company_id)

        active_bookings = bookings.all()

        containers_in_transit = containers.filter(
            booking__status=models.Booking.BookingStatus.In_Transit,
            booking__eta__gte=start_date,
            # booking__cancelled_at__isnull=True,
            # discharge_date__isnull=True,
        ).order_by("booking__eta")

        upcoming_departures = bookings.filter(ets__gte=start_date).order_by("ets")

        upcoming_arrivals = bookings.filter(eta__gte=start_date).order_by("eta")

        data = {
            "active_bookings": active_bookings,
            "containers_in_transit": containers_in_transit,
            "upcoming_departures": upcoming_departures,
            "upcoming_arrivals": upcoming_arrivals,
        }

        return Response(DashboardBookingMetricSerializer(data).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["GET"], url_path="freight-variation-analysis")
    def freight_variation_analysis(self, request):
        """
        Compara el flete cotizado en Booking vs. el flete realmente facturado en Invoice.amount e identifica recargos no previstos
        """

        start_date, shipping_company_id = self.__get_start_date_and_shipping_company(request)

        bookings = (
            models.Booking.objects.select_related("shipping_company", "port_loading", "port_discharge")
            .annotate(
                invoiced_amount=Sum("invoices__amount"),
                charges_amount=Sum("invoices__other_charges_amount"),
                invoices_count=Count("invoices", distinct=True),
            )
            .filter(invoices_count__gt=0).all()
        )

        if start_date:
            bookings = bookings.filter(ets__gte=start_date)
        if shipping_company_id:
            bookings = bookings.filter(shipping_company_id=shipping_company_id)

        results = []
        totals = {
            "quoted_total": Decimal("0.00"),
            "invoiced_total": Decimal("0.00"),
            "variation_total": Decimal("0.00"),
            "others_charges_total": Decimal("0.00"),
        }

        for booking in bookings:
            quoted = booking.quoted_amount or Decimal("0.00")
            invoiced = booking.invoiced_amount or Decimal("0.00")
            charges = booking.charges_amount or Decimal("0.00")

            variation = invoiced - quoted
            variation_pct = (
                (variation / quoted * 100) if quoted > 0 else Decimal("0.00")
            )

            item = {
                "booking_number": booking.booking_number,
                "shipping_company": (booking.shipping_company.name if booking.shipping_company else None),
                "port_loading": (booking.port_loading.name if booking.port_loading else None),
                "port_discharge": (booking.port_discharge.name if booking.port_discharge else None),
                "ets": booking.ets,
                "eta": booking.eta,
                "quoted_amount": Decimal(quoted),
                "invoiced_amount": Decimal(invoiced),
                "others_charges": Decimal(charges),
                "variation_amount": Decimal(variation),
                "variation_percentage": Decimal(round(variation_pct, 2)),
                "invoices_count": booking.invoices_count,
                "has_variation": variation != Decimal("0.00"),
                "alert_level": alert_level(variation_pct),
            }

            if not item["has_variation"]:
                continue

            results.append(item)

            totals["quoted_total"] += quoted
            totals["invoiced_total"] += invoiced
            totals["variation_total"] += variation
            totals["others_charges_total"] += charges

        avg_variation_pct = (
            totals["variation_total"] / totals["quoted_total"] * 100
            if totals["quoted_total"] > 0
            else Decimal("0.00")
        )

        summary = {
            "bookings_analyzed": len(results),
            "quoted_total": Decimal(totals["quoted_total"]),
            "invoiced_total": Decimal(totals["invoiced_total"]),
            "variation_total": Decimal(totals["variation_total"]),
            "others_charges_total": float(totals["others_charges_total"]),
            "avg_variation_percentage": Decimal(round(avg_variation_pct, 2)),
        }

        return Response({"summary": summary, "details": results}, status=status.HTTP_200_OK)


class DashboardContainerViewSet(viewsets.GenericViewSet):

    def __get_request_dates(self, request):
        _serializer = DashboardDatesSerializer(data=self.request.GET)
        _serializer.is_valid(raise_exception=True)
        validated_data = _serializer.validated_data
        return validated_data["start_date"], validated_data["end_date"]

    @action(methods=["GET"], detail=False, url_path="without-return")
    def containers_without_return(self, request):
        queryset = (
            models.Container.objects.filter(
                discharge_date__isnull=False, return_date__isnull=True
            )
            .order_by("last_free_day")
            .all()
        )
        return Response(
            serializers.ContainerMinimalSerializer(queryset, many=True).data,
            status=status.HTTP_200_OK,
        )

    @action(
        methods=["GET"],
        detail=False,
        url_path="next-containers-by/(?P<kind>eta|est|cut_off)",
    )
    def next_containers_by_date(self, request, kind):
        filter = {f"container__booking__{kind}__gte": now() - timedelta(days=3)}
        queryset = (
            models.ContainerItem.objects.filter(**filter)
            .values('product_id', date=F(f"container__booking__{kind}"))
            .annotate(
                products_quantity=Sum("quantity"),
                containers_quantity=Count("container", distinct=True),
            )
            .order_by("date")
        )

        products = {}
        result = []
        for row in queryset:
            product = products.get(
                row['product_id'],
                models.ProductProviderPresentation.objects.get(pk=row['product_id'])
            )
            result.append({'product_name': str(product), **row})
            products[row['product_id']] = product

        return Response(result, status=status.HTTP_200_OK)

    @action(detail=False, methods=["GET"], url_path="cost-per-container")
    def cost_per_container(self, request):
        """
        Costo por contenedor:
        Costo Total Facturado (flete + recargos) / cantidad de contenedores.
        """

        start_date, end_date = self.__get_request_dates(request)

        shipping_company_id = request.query_params.get("shipping_company_id")

        bookings = Booking.objects.select_related(
            "shipping_company", "port_loading", "port_discharge", "vessel"
        ).annotate(
            invoiced_amount=Sum("invoices__amount"),
            invoiced_charges=Sum("invoices__other_charges_amount"),
            invoiced_total=Sum("invoices__total_amount"),
            invoices_count=Count("invoices", distinct=True),
            containers_count=Count("containers", distinct=True),
        )

        if start_date:
            bookings = bookings.filter(ets__gte=start_date)
        if end_date:
            bookings = bookings.filter(ets__lte=end_date)
        if shipping_company_id:
            bookings = bookings.filter(shipping_company_id=shipping_company_id)

        bookings = bookings.filter(containers_count__gt=0)

        results = []
        totals = {
            "invoiced_total": Decimal("0.00"),
            "quoted_total": Decimal("0.00"),
            "containers_total": 0,
        }

        for booking in bookings:
            invoiced = booking.invoiced_total or Decimal("0.00")
            freight = booking.invoiced_amount or Decimal("0.00")
            charges = booking.invoiced_charges or Decimal("0.00")
            quoted = booking.quoted_amount or Decimal("0.00")
            containers = booking.containers_count or 0

            if containers == 0:
                continue

            cost_per_container = invoiced / containers
            freight_per_container = freight / containers
            charges_per_container = charges / containers
            quoted_per_container = (
                quoted / containers if containers else Decimal("0.00")
            )

            variation = cost_per_container - quoted_per_container
            variation_pct = (
                (variation / quoted_per_container * 100)
                if quoted_per_container > 0
                else Decimal("0.00")
            )

            item = {
                "booking_number": booking.booking_number,
                "shipping_company": (
                    booking.shipping_company.name if booking.shipping_company else None
                ),
                "vessel": booking.vessel.name if booking.vessel else None,
                "port_loading": (
                    booking.port_loading.name if booking.port_loading else None
                ),
                "port_discharge": (
                    booking.port_discharge.name if booking.port_discharge else None
                ),
                "ets": booking.ets,
                "eta": booking.eta,
                "invoiced_total": Decimal(invoiced),
                "freight_amount": Decimal(freight),
                "charges_amount": Decimal(charges),
                "quoted_amount": Decimal(quoted),
                "containers_count": containers,
                "invoices_count": booking.invoices_count,
                "cost_per_container": Decimal(cost_per_container),
                "freight_per_container": Decimal(freight_per_container),
                "charges_per_container": Decimal(charges_per_container),
                "quoted_per_container": Decimal(quoted_per_container),
                "variation_amount": Decimal(variation),
                "variation_percentage": Decimal(round(variation_pct, 2)),
                "alert_level": alert_level(variation_pct),
            }

            results.append(item)

            totals["invoiced_total"] += invoiced
            totals["quoted_total"] += quoted
            totals["containers_total"] += containers

        global_cost_per_container = (
            totals["invoiced_total"] / totals["containers_total"]
            if totals["containers_total"] > 0
            else Decimal("0.00")
        )
        global_quoted_per_container = (
            totals["quoted_total"] / totals["containers_total"]
            if totals["containers_total"] > 0
            else Decimal("0.00")
        )
        global_variation_pct = (
            (
                    (global_cost_per_container - global_quoted_per_container)
                    / global_quoted_per_container
                    * 100
            )
            if global_quoted_per_container > 0
            else Decimal("0.00")
        )

        summary = {
            "bookings_analyzed": len(results),
            "containers_total": totals["containers_total"],
            "invoiced_total": Decimal(totals["invoiced_total"]),
            "quoted_total": Decimal(totals["quoted_total"]),
            "global_cost_per_container": Decimal(global_cost_per_container),
            "global_quoted_per_container": Decimal(global_quoted_per_container),
            "global_variation_percentage": Decimal(round(global_variation_pct, 2)),
            "avg_containers_per_booking": Decimal(
                Decimal(totals["containers_total"]) / len(results)
                if results
                else Decimal("0.00")
            ),
        }

        return Response(
            {
                "summary": summary,
                "details": results,
            },
            status=status.HTTP_200_OK,
        )


class DashboardInvoiceViewSet(viewsets.GenericViewSet):
    types_queryset = {
        "provider": models.ProviderInvoice.objects,
        "shipping-company": models.ShippingCompanyInvoice.objects,
    }
    types_serializers = {
        "provider": serializers.ProviderInvoiceSerializer,
        "shipping-company": serializers.ShippingCompanyInvoiceSerializer,
    }

    @action(
        methods=["GET"],
        detail=False,
        url_path="(?P<type>provider|shipping-company)/expired",
    )
    def expired_invoices(self, request, type):
        queryset = (
            self.types_queryset[type]
            .filter(status=models.Invoice.InvoiceStatus.Expired)
            .order_by("-expiration_date")
        )
        return Response(
            self.types_serializers[type](
                queryset, many=True, context=self.get_serializer_context()
            ).data,
            status=status.HTTP_200_OK,
        )

    @action(
        methods=["GET"],
        detail=False,
        url_path="(?P<type>provider|shipping-company)/unpaid",
    )
    def unpaid_invoices(self, request, type):
        queryset = (
            self.types_queryset[type]
            .exclude(status=models.Invoice.InvoiceStatus.Canceled)
            .filter(pending_amount=F("total_amount"))
            .order_by("-expiration_date")
            .all()
        )
        return Response(
            self.types_serializers[type](
                queryset, many=True, context=self.get_serializer_context()
            ).data,
            status=status.HTTP_200_OK,
        )
