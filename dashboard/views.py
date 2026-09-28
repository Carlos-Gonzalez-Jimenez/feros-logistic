from django.db.models import (
    Count,
)
from django.utils.timezone import now
from rest_framework import viewsets
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
        return Response(DashboardSummarySerializer(response).data)

    @action(methods=["GET"], detail=False, url_path="nexts/<str:date>")
    def get_next_booking_dates(self, request, date):
        filter = {f"{date}__gte": now()}
        queryset = models.Booking.objects.filter(**filter).order_by(f"-{date}")
        return self.get_serializer(queryset, many=True)


# @action(
#         detail=False,
#         methods=["get"],
#         url_path="container-cost",
#         url_name="container-cost",
#     )
#     def container_cost(self, request):
#         """
#         Reporte de costo por contenedor.

#         Toma el total facturado por la naviera y lo divide entre los  contenedores del booking.
#         """

#         start_date, end_date = self.__get_request_dates(request)

#         invoices = models.ShippingCompanyInvoice.objects.select_related(
#             "payment_agreement"
#         ).order_by("-emission_date")

#         bookings = (
#             models.Booking.objects
#             .select_related(
#                 "shipping_company",
#                 "vessel",
#                 "port_loading",
#                 "port_discharge",
#             )
#             .prefetch_related(
#                 Prefetch(
#                     "shipping_company_invoice",
#                     queryset=invoices,
#                     to_attr="_prefetched_invoices",
#                 ),
#                 "containers__container_type",
#             )
#             .filter(
#                 shipping_company_invoice__emission_date__gte=start_date,
#                 shipping_company_invoice__emission_date__lte=end_date,
#             )
#             .distinct()
#         )
#         if shipping_company_id is not None:
#             bookings = bookings.filter(shipping_company_id=shipping_company_id)

#         summary, by_company, by_type_global = build_container_cost(queryset)

#         payload = {
#             "range": {"start_date": start_date, "end_date": end_date},
#             "filters": {
#                 "shipping_company": request.query_params.get("shipping_company"),
#                 "shipping_companies": request.query_params.get("shipping_companies"),
#                 "container_type": request.query_params.get("container_type"),
#                 "only_invoiced": request.query_params.get("only_invoiced"),
#                 "active": request.query_params.get("active"),
#                 "status": pending_status,
#                 "min_cost_per_container": min_cpc,
#             },
#             **summary,
#             "by_type_global": by_type_global,
#             "by_shipping_company": by_company,
#         }

#         serializer = ContainerCostSummarySerializer(payload)
#         return Response(serializer.data)


class DashboardInvoiceViewSet(viewsets.GenericViewSet):
    types_queryset = {
        'provider': models.ProviderInvoice.objects.all(),
        'shipping-company': models.ShippingCompanyInvoice.objects.all()
    }
    types_serializers = {
        'provider': serializers.ProviderInvoiceSerializer,
        'shipping-company': serializers.ShippingCompanyInvoiceSerializer
    }

    @action(methods=["GET"], detail=False, url_path="<str:type>/expired", )
    def expired_invoices(self, request, type):
        queryset = self.types_queryset[type].filter(status=models.Invoice.InvoiceStatus.Expired).all()
        return self.types_serializers[type](queryset, many=True, **self.get_serializer_context()).data

    @action(methods=["GET"], detail=False, url_path="<str:type>/expired", )
    def unpaid_invoices(self, request, type):
        queryset = self.types_queryset[type].exclude(status=models.Invoice.InvoiceStatus.Canceled).all()
        return self.types_serializers[type](queryset, many=True, **self.get_serializer_context()).data
