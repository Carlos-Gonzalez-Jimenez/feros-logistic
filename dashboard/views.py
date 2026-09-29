from datetime import timedelta
from decimal import Decimal
from django.db.models import (
    Count,
    F,
    Sum,
    Value,
)
from django.db.models.functions import Concat
from django.utils.timezone import now
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from core import models, serializers
from core.permissions import CustomPermissionFactory, ReadOnlyPermission
from dashboard.serializers import DashboardDatesSerializer, DashboardSummarySerializer

# Reporte de estado de bookings vs. ejecución real
# Compara lo reservado (booking) contra lo efectivamente embarcado, facturado y contenerizado.

# Utilización de contenedores
# Peso y volumen cargado vs. capacidad nominal. Detecta contenedores subutilizados o sobrecargados.

# Conciliación Booking vs. Factura de Naviera
# Verifica que lo facturado coincida con lo cotizado/reservado

# Análisis de variaciones de flete
# Compara tarifa cotizada en booking vs. factura final. Identifica recargos no previstos.

# Costo por contenedor
# Costo total facturado dividido entre contenedores

# Cuentas por pagar por naviera
# Consolidado de facturas pendientes, vencidas y pagadas por proveedor y naviera


class DashboardBookingViewSet(viewsets.GenericViewSet):
    """
    View to handle all booking-containers related actions in dashboard.

    All reports are handled via methods with @action decorator in which Users can be filtered
    by start_date, end_date.
    """

    permission_classes = [
        ReadOnlyPermission
        | CustomPermissionFactory(["user.show_all_boards", "user.show_own_board"])
    ]
    queryset = models.Booking.objects.all()
    serializer_class = serializers.BookingSerializer

    def __get_request_dates(self, request):
        _serializer = DashboardDatesSerializer(data=self.request.GET)
        _serializer.is_valid(raise_exception=True)
        validated_data = _serializer.validated_data
        return validated_data["start_date"], validated_data["end_date"]

    @action(methods=["get"], detail=False, url_path="booking-metrics")
    def get_booking_metrics(self, request):
        """
        Dashboard operativo : bookings activos, contenedores en tránsito, próximas salidas, próximos arribos
        """

        start_date, end_date = self.__get_request_dates(request)

        shipping_company_id = request.query_params.get("shipping_company_id")

        bookings = (
            models.Booking.objects.select_related(
                "port_loading", "port_discharge", "shipping_company", "vessel"
            )
            .prefetch_related("sale_orders")
            .annotate(containers_count=Count("containers", distinct=True))
        )
        if shipping_company_id is not None:
            bookings = bookings.filter(shipping_company_id=shipping_company_id)

        containers = models.Container.objects.select_related(
            "booking", "booking__shipping_company", "container_type"
        ).prefetch_related("sale_orders", "items__product")

        if shipping_company_id is not None:
            containers = containers.filter(shipping_company_id=shipping_company_id)

        active_bookings = bookings.filter(
            confirmed_at__date__gte=start_date,
            confirmed_at__date__lte=end_date,
            cancelled_at__isnull=True,
        ).order_by("-confirmed_at")

        containers_in_transit = containers.filter(
            booking__confirmed_at__isnull=False,
            booking__cancelled_at__isnull=True,
            discharge_date__isnull=True,
            booking__eta__gte=start_date,
            booking__eta__lte=end_date,
        ).order_by("booking__eta")

        upcoming_departures = bookings.filter(
            cancelled_at__isnull=True,
            ets__gte=start_date,
            ets__lte=end_date,
        ).order_by("ets")

        upcoming_arrivals = bookings.filter(
            cancelled_at__isnull=True,
            eta__gte=start_date,
            eta__lte=end_date,
        ).order_by("eta")

        totals = {
            "active_bookings": bookings.filter(
                confirmed_at__date__gte=start_date,
                confirmed_at__date__lte=end_date,
                cancelled_at__isnull=True,
            ).count(),
            "containers_in_transit": containers.filter(
                booking__confirmed_at__isnull=False,
                booking__cancelled_at__isnull=True,
                discharge_date__isnull=True,
                booking__eta__gte=start_date,
                booking__eta__lte=end_date,
            ).count(),
            "upcoming_departures": bookings.filter(
                cancelled_at__isnull=True,
                ets__gte=start_date,
                ets__lte=end_date,
            ).count(),
            "upcoming_arrivals": bookings.filter(
                cancelled_at__isnull=True,
                eta__gte=start_date,
                eta__lte=end_date,
            ).count(),
        }

        response = {
            "range": {"start_date": start_date, "end_date": end_date},
            "shipping_company_id": shipping_company_id,
            "active_bookings": active_bookings,
            "containers_in_transit": containers_in_transit,
            "upcoming_departures": upcoming_departures,
            "upcoming_arrivals": upcoming_arrivals,
            "totals": totals,
        }
        return Response(
            DashboardSummarySerializer(response).data, status=status.HTTP_200_OK
        )

    def _alert_level(self, variation_pct: Decimal) -> str:
        """Clasifica la variación."""
        
        if variation_pct >= Decimal("15"):
            return "critical"
        if variation_pct >= Decimal("5"):
            return "warning"
        if variation_pct <= Decimal("-5"):
            return "favorable"
        return "normal"
    
    @action(detail=False, methods=["get"], url_path="freight-variation-analysis")
    def freight_variation_analysis(self, request):
        """
        Compara el flete cotizado en Booking vs. el flete realmente facturado en Invoice.amount e identifica recargos no previstos
        """

        start_date, end_date = self.__get_request_dates(request)

        shipping_company_id = request.query_params.get("shipping_company_id")

        bookings = (
            Booking.objects.select_related(
                "shipping_company", "port_loading", "port_discharge"
            )
            .annotate(
                invoiced_amount=Sum("invoices__amount"),
                charges_amount=Sum("invoices__other_charges_amount"),
                invoices_count=Count("invoices", distinct=True),
            )
            .filter(invoices_count__gt=0)
        )

        if start_date:
            bookings = bookings.filter(ets__gte=start_date)
        if end_date:
            bookings = bookings.filter(ets__lte=end_date)
        if shipping_company_id:
            bookings = bookings.filter(shipping_company_id=shipping_company_id)

        results = []
        totals = {
            "quoted_total": Decimal("0.00"),
            "invoiced_total": Decimal("0.00"),
            "variation_total": Decimal("0.00"),
            "unexpected_charges_total": Decimal("0.00"),
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
                "shipping_company": (
                    booking.shipping_company.name if booking.shipping_company else None
                ),
                "port_loading": (
                    booking.port_loading.name if booking.port_loading else None
                ),
                "port_discharge": (
                    booking.port_discharge.name if booking.port_discharge else None
                ),
                "ets": booking.ets,
                "eta": booking.eta,
                "quoted_amount": Decimal(quoted),
                "invoiced_amount": Decimal(invoiced),
                "others_charges": Decimal(charges),
                "variation_amount": Decimal(variation),
                "variation_percentage": Decimal(round(variation_pct, 2)),
                "invoices_count": booking.invoices_count,
                "has_variation": variation != Decimal("0.00"),
                "alert_level": self._alert_level(variation_pct),
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

        return Response(
            {
                "summary": summary,
                "details": results,
            },
            status=status.HTTP_200_OK,
        )


class DashboardContainerViewSet(viewsets.GenericViewSet):

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
            serializers.ContainerMinimalSerializer(queryset, many=True).data
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
            .values(
                product_name=Concat(
                    "product__product_provider__product__name",
                    Value(" - "),
                    "product__presentation__name",
                ),
                date=F(f"container__booking__{kind}"),
            )
            .annotate(
                products_quantity=Sum("quantity"),
                containers_quantity=Count("container", distinct=True),
            )
            .order_by("date")
        )

        result = list(queryset)

        return Response(result)


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
            ).data
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
            ).data
        )
