import datetime
from decimal import Decimal

from django.core.cache import cache
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
from dashboard.serializers import DashboardDatesSerializer
from user.models import User
from user.serializers import UserMinimalSerializer

# Reporte de estado de bookings vs. ejecución real
# Compara lo reservado (booking) contra lo efectivamente embarcado, facturado y contenerizado.

# Trazabilidad por contenedor
# Número de contenedor, tipo (20'/40'/40HC/Reefer), booking asociado, BL, naviera, buque, puerto origen/destino, carga, zarpe y descarga.

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
    View to handle all booking-related actions in dashboard.

    All reports are handled via methods with @action decorator in which Users can be filtered
    by start_date, end_date.
    """

    permission_classes = [
        ReadOnlyPermission
        | CustomPermissionFactory(["user.show_all_boards", "user.show_own_board"])
    ]
    queryset = models.Booking.objects.all()
    serializer_class = serializers.BookingSerializer

    @action(methods=["get"], detail=False, url_path="booking-metrics")
    def get_booking_metrics(self, request):
        """
        Dashboard operativo : bookings activos, contenedores en tránsito, próximas salidas, próximos arribos
        """

        month_ago = timezone.now() - datetime.timedelta(days=30)
        booking_metrics = models.User.objects.filter(is_active=True).aggregate(
            total_users=Count("id"),
            new_users_month=Count("id", filter=Q(date_joined__gte=month_ago)),
            deliverers=Count("id", filter=Q(is_deliverer=True)),
            newsletter_subscribers=Count("id", filter=Q(newsletter=True)),
            unverified_users=Count("id", filter=Q(verified=False)),
        )
        return Response(booking_metrics, status=status.HTTP_200_OK)

    def _calculate_percentage(self, part, total):
        """Calcular porcentaje de forma segura"""
        if total == 0:
            return 0
        return round((part / total) * 100, 2)

    # @action(detail=False, methods=["get"], url_path="customers-metrics")
    # def customers_metrics(self, request):
    #     cache_key = f"customers_metrics_{timezone.now().strftime('%Y-%m-%d')}"
    #     cached_data = cache.get(cache_key)

    #     if cached_data is not None:
    #         return Response(cached_data, status=status.HTTP_200_OK)

    #     today = timezone.now().date()
    #     last_30_days = today - datetime.timedelta(days=30)
    #     last_90_days = today - datetime.timedelta(days=90)

    #     customer_metrics = models.User.objects.filter(is_staff=False).aggregate(
    #         total_customers=Count("id"),
    #         new_customers_30d=Count("id", filter=Q(date_joined__gte=last_30_days)),
    #         active_customers_30d=Count(
    #             "id", filter=Q(orders__creation_date__gte=last_30_days), distinct=True
    #         ),
    #         verified_customers=Count("id", filter=Q(verified=True)),
    #         newsletter_subscribers=Count("id", filter=Q(newsletter=True)),
    #     )

    #     top_customers = (
    #         models.User.objects.filter(
    #             is_staff=False, orders__creation_date__gte=last_90_days
    #         )
    #         .annotate(
    #             total_orders=Count("orders"),
    #             total_spent=Coalesce(
    #                 Sum(
    #                     F("orders__order_products__price")
    #                     * F("orders__order_products__quantity")
    #                 ),
    #                 Value(0, output_field=output_field.DecimalField()),
    #             ),
    #             last_order_date=Max("orders__creation_date"),
    #         )
    #         .filter(total_spent__isnull=False)
    #         .order_by("-total_spent")[:10]
    #     )
    #     response_data = {
    #         "acquisition": {
    #             "total_customers": customer_metrics["total_customers"],
    #             "new_customers_30d": customer_metrics["new_customers_30d"],
    #             "growth_rate": self._calculate_percentage(
    #                 customer_metrics["new_customers_30d"],
    #                 customer_metrics["total_customers"],
    #             ),
    #         },
    #         "engagement": {
    #             "active_customers_30d": customer_metrics["active_customers_30d"],
    #             "newsletter_subscribers": customer_metrics["newsletter_subscribers"],
    #             "verified_customers": customer_metrics["verified_customers"],
    #             "activation_rate": self._calculate_percentage(
    #                 customer_metrics["verified_customers"],
    #                 customer_metrics["total_customers"],
    #             ),
    #         },
    #         "value": {
    #             "top_customers": [
    #                 {
    #                     "id": customer.id,
    #                     "name": f"{customer.first_name} {customer.last_name}",
    #                     "email": customer.email,
    #                     "total_orders": customer.total_orders,
    #                     "total_spent": float(customer.total_spent),
    #                     "last_order": customer.last_order_date,
    #                 }
    #                 for customer in top_customers
    #             ],
    #         },
    #     }
    #     cache.set(cache_key, response_data, 60 * 60 * 2)
    #     return Response(response_data, status=status.HTTP_200_OK)
