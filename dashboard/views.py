import datetime
from decimal import Decimal

from django.db import models as output_field
from django.db.models import (
    Sum,
    Count,
    Max,
    Subquery,
    OuterRef,
    F,
    Value,
    Q,
    Prefetch,
)
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.translation import get_language_from_request
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from core import models, serializers
from core.permissions import CustomPermissionFactory, ReadOnlyPermission
from dashboard.serializers import DashboardDatesSerializer, DashboardSummarySerializer
from user.models import User
from user.serializers import UserMinimalSerializer

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
        return Response(DashboardSummarySerializer(response).data)
