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
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from core import models, serializers
from core.permissions import CustomPermissionFactory, ReadOnlyPermission
from dashboard.serializers import DashboardDatesSerializer
from payments.models import Payment
from user.models import User
from user.serializers import UserMinimalSerializer


class DashboardProductsViewSet(viewsets.GenericViewSet):
    """
    View to handle all product-related actions in dashboard.

    """

    permission_classes = [
        ReadOnlyPermission
        | CustomPermissionFactory(["user.show_all_boards", "user.show_own_board"])
    ]
    queryset = models.Product.objects.filter(active=True)
    serializer_class = serializers.ProductReadSerializer

    @action(methods=["get"], detail=False, url_path="current-inventory")
    def get_products_current_inventory(self, request):
        parent_categories = (
            models.Category.objects.filter(active=True, parent__isnull=True)
            .prefetch_related(
                Prefetch(
                    "category",
                    queryset=models.Category.objects.filter(active=True)
                    .annotate(
                        products_count=Count(
                            "products", filter=Q(products__active=True)
                        )
                    )
                    .prefetch_related(
                        Prefetch(
                            "products",
                            queryset=models.Product.objects.filter(active=True),
                            to_attr="active_products",
                        )
                    ),
                    to_attr="active_subcategories",
                )
            )
            .annotate(
                total_products=Count(
                    "category__products", filter=Q(category__products__active=True)
                )
            )
            .prefetch_related(
                Prefetch(
                    "products",
                    queryset=models.Product.objects.filter(active=True),
                    to_attr="direct_active_products",
                )
            )
        )

        current_inventory_data = []

        for category in parent_categories:
            subcategories_data = []

            for subcategory in category.active_subcategories:
                products = getattr(subcategory, "active_products", [])

                subcategories_data.append(
                    {
                        "id": subcategory.id,
                        "name": subcategory.name,
                        "products_count": len(products),
                        "products": serializers.ProductReadMinimalSerializer(
                            products, many=True, context=self.get_serializer_context()
                        ).data,
                    }
                )

            direct_products = getattr(category, "direct_active_products", [])

            current_inventory_data.append(
                {
                    "id": category.id,
                    "name": category.name,
                    "total_products": len(direct_products) if direct_products else category.total_products,
                    "products": (
                        serializers.ProductReadMinimalSerializer(
                            direct_products,
                            many=True,
                            context=self.get_serializer_context(),
                        ).data
                        if direct_products
                        else None
                    ),
                    "subcategories": subcategories_data,
                }
            )

        return Response(current_inventory_data, status=status.HTTP_200_OK)


class DashboardUsersViewSet(viewsets.GenericViewSet):
    """
    View to handle all user-related actions in dashboard.

    All reports are handled via methods with @action decorator in which Users can be filtered
    by start_date, end_date.
    """

    permission_classes = [
        ReadOnlyPermission
        | CustomPermissionFactory(["user.show_all_boards", "user.show_own_board"])
    ]
    queryset = models.User.objects.filter(is_active=True)
    serializer_class = serializers.UserSerializer

    @action(methods=["get"], detail=False, url_path="metrics")
    def get_user_metrics(self, request):
        cache_key = f"user_metrics_{timezone.now().strftime('%Y-%m-%d')}"
        cached_data = cache.get(cache_key)

        if cached_data is not None:
            return Response(cached_data, status=status.HTTP_200_OK)

        month_ago = timezone.now() - datetime.timedelta(days=30)
        metrics = models.User.objects.filter(is_active=True).aggregate(
            total_users=Count("id"),
            new_users_month=Count("id", filter=Q(date_joined__gte=month_ago)),
            deliverers=Count("id", filter=Q(is_deliverer=True)),
            newsletter_subscribers=Count("id", filter=Q(newsletter=True)),
            unverified_users=Count("id", filter=Q(verified=False)),
        )
        cache.set(cache_key, metrics, 60 * 60)
        return Response(metrics, status=status.HTTP_200_OK)

    def _calculate_percentage(self, part, total):
        """Calcular porcentaje de forma segura"""
        if total == 0:
            return 0
        return round((part / total) * 100, 2)

    @action(detail=False, methods=["get"], url_path="customers-metrics")
    def customers_metrics(self, request):
        cache_key = f"customers_metrics_{timezone.now().strftime('%Y-%m-%d')}"
        cached_data = cache.get(cache_key)

        if cached_data is not None:
            return Response(cached_data, status=status.HTTP_200_OK)

        today = timezone.now().date()
        last_30_days = today - datetime.timedelta(days=30)
        last_90_days = today - datetime.timedelta(days=90)

        customer_metrics = models.User.objects.filter(is_staff=False).aggregate(
            total_customers=Count("id"),
            new_customers_30d=Count("id", filter=Q(date_joined__gte=last_30_days)),
            active_customers_30d=Count(
                "id", filter=Q(orders__creation_date__gte=last_30_days), distinct=True
            ),
            verified_customers=Count("id", filter=Q(verified=True)),
            newsletter_subscribers=Count("id", filter=Q(newsletter=True)),
        )

        top_customers = (
            models.User.objects.filter(
                is_staff=False, orders__creation_date__gte=last_90_days
            )
            .annotate(
                total_orders=Count("orders"),
                total_spent=Coalesce(
                    Sum(
                        F("orders__order_products__price")
                        * F("orders__order_products__quantity")
                    ),
                    Value(0, output_field=output_field.DecimalField()),
                ),
                last_order_date=Max("orders__creation_date"),
            )
            .filter(total_spent__isnull=False)
            .order_by("-total_spent")[:10]
        )
        response_data = {
            "acquisition": {
                "total_customers": customer_metrics["total_customers"],
                "new_customers_30d": customer_metrics["new_customers_30d"],
                "growth_rate": self._calculate_percentage(
                    customer_metrics["new_customers_30d"],
                    customer_metrics["total_customers"],
                ),
            },
            "engagement": {
                "active_customers_30d": customer_metrics["active_customers_30d"],
                "newsletter_subscribers": customer_metrics["newsletter_subscribers"],
                "verified_customers": customer_metrics["verified_customers"],
                "activation_rate": self._calculate_percentage(
                    customer_metrics["verified_customers"],
                    customer_metrics["total_customers"],
                ),
            },
            "value": {
                "top_customers": [
                    {
                        "id": customer.id,
                        "name": f"{customer.first_name} {customer.last_name}",
                        "email": customer.email,
                        "total_orders": customer.total_orders,
                        "total_spent": float(customer.total_spent),
                        "last_order": customer.last_order_date,
                    }
                    for customer in top_customers
                ],
            },
        }
        cache.set(cache_key, response_data, 60 * 60 * 2)
        return Response(response_data, status=status.HTTP_200_OK)


class DashboardOrdersViewSet(viewsets.GenericViewSet):
    """
    View to handle all order-related actions in dashboard.

    All reports are handled via methods with @action decorator in which Orders can be filtered
    by start_date, end_date.
    """

    permission_classes = [CustomPermissionFactory(["user.show_all_boards", "user.show_own_board"])]
    queryset = models.Order.objects.filter(merge__isnull=True)
    serializer_class = serializers.OrderMinimalSerializer

    def __get_request_dates(self, request):
        _serializer = DashboardDatesSerializer(data=self.request.GET)
        _serializer.is_valid(raise_exception=True)
        validated_data = _serializer.validated_data
        return validated_data['start_date'], validated_data['end_date']

    @action(methods=["get"], detail=False, url_path="daily-amount")
    def order_daily_amount(self, request):
        """Returns the daily amount of the orders registered in the app.

        Args:
            request (GET): Filter by start_date, end_date

        Returns:
            List of daily statistics with orders and amounts
        """
        start_date, end_date = self.__get_request_dates(request)
        filters = {"creation_date__date__gte": start_date, "creation_date__date__lte": end_date}

        cache_key = f"daily_amount__{start_date}__{end_date}"
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data, status=status.HTTP_200_OK)

        latest_status = Subquery(
            models.OrderTracking.objects.filter(order=OuterRef('pk')).order_by('-id') \
                .values('status__code_name')[:1]
        )
        orders = self.get_queryset().annotate(
            latest_status=latest_status
        ).filter(**filters).exclude(latest_status__in=['cancelled', 'returned'])

        daily_stats = (
            orders.values("creation_date__date").annotate(
                total_orders=Count("id"),
                total_amount=Coalesce(
                    Sum(F("order_products__price") * F("order_products__quantity")),
                    Value(0, output_field=output_field.DecimalField()),
                ),
            )
            .order_by("creation_date__date")
        )
        stats_dict = {
            stat["creation_date__date"]: {
                "total_orders": stat["total_orders"],
                "total_amount": float(stat["total_amount"]),
            }
            for stat in daily_stats
        }
        result = []
        current_date = start_date
        while current_date <= end_date:
            daily_data = stats_dict.get(current_date, {"total_orders": 0, "total_amount": 0})
            result.append(
                {
                    "day": int(datetime.datetime.combine(current_date, datetime.time.min).timestamp() * 1000),
                    "total_daily_orders": daily_data["total_orders"],
                    "total_daily_amount": round(daily_data["total_amount"], 2),
                }
            )
            current_date += datetime.timedelta(days=1)
        cache.set(cache_key, result, 5 * 60)
        return Response(result, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="unpaid-report")
    def unpaid_orders_report(self, request):
        """_summary_

        Args:
            request (_type_): _description_

        Returns:
            _type_: Reporte de pedidos no pagados en fecha límite
        """
        today = timezone.now().date()
        cache_key = f"unpaid_report_{today}"
        cached_data = cache.get(cache_key)

        # if cached_data is not None:
        #     return Response(cached_data, status=status.HTTP_200_OK)

        latest_status = Subquery(
            models.OrderTracking.objects.filter(order=OuterRef('pk')).order_by('-id') \
                .values('status__code_name')[:1]
        )
        queryset = (self.get_queryset().annotate(latest_status=latest_status).filter(
            payment_deadline__isnull=False, pending_amount__gt=Decimal("0.00")
        ).exclude(latest_status__in=['cancelled', 'returned']))

        total_stats = queryset.aggregate(
            total_orders=Count("id"),
            total_pending_amount=Sum("pending_amount"),
            total_amount=Sum("total_amount"),
        )

        stats_by_client = (
            User.objects.prefetch_related("orders_client")
            .filter(orders_client__in=queryset, is_staff=False)
            .annotate(
                total_orders=Count("orders_client"),
                total_pending_amount=Sum("orders_client__pending_amount"),
                total_orders_amount=Sum("orders_client__total_amount"),
            )
        )

        result = {
            "statistics": total_stats,
            "clients": [
                {
                    "client": UserMinimalSerializer(instance=stats, context=self.get_serializer_context()).data,
                    "total_orders": stats.total_orders,
                    "total_pending_amount": stats.total_pending_amount,
                    "total_orders_amount": stats.total_orders_amount,
                    "relational_percent": stats.total_pending_amount / stats.total_orders_amount,
                }
                for stats in stats_by_client
            ],
        }

        cache.set(cache_key, result, 60 * 1)

        return Response(result, status=status.HTTP_200_OK)

    @action(methods=["get"], detail=False, url_path="products-amount")
    def order_products_amount(self, request):
        """Returns the total amount by product in a given period.

        Args:
            request (GET): Filter by start_date, end_date

        Returns:
            List of products with their total amounts
        """
        start_date, end_date = self.__get_request_dates(request)
        client_id = request.query_params.get("client_id")
        cache_key = f"products_amount__{start_date}__{end_date}__{client_id or ''}"
        cached_data = cache.get(cache_key)

        if cached_data is not None:
            return Response(cached_data, status=status.HTTP_200_OK)

        filters = {"order__creation_date__date__gte": start_date, "order__creation_date__date__lte": end_date}
        if client_id is not None:
            filters.setdefault('order__client_id', client_id)
        series = (
            models.OrderProducts.objects
            .filter(**filters)
            .values("product_id", "product__name")
            .annotate(total_quantity=Sum("quantity"))
            .order_by("-total_quantity")
        )

        product_ids = [serie["product_id"] for serie in series]

        products_dict = {product.id: product for product in models.Product.objects.filter(id__in=product_ids)}
        result = [
            {
                "total_quantity": serie["total_quantity"],
                "product": serializers.ProductReadSerializer(
                    products_dict.get(serie["product_id"]),
                    context=self.get_serializer_context(),
                ).data,
            }
            for serie in series
            if serie["product_id"] in products_dict
        ]
        cache.set(cache_key, result, 60 * 5)
        return Response(result, status=status.HTTP_200_OK)

    def _calculate_percentage(self, part, total):
        """Calcular porcentaje de forma segura"""
        if total == 0:
            return 0
        return part / total

    @action(methods=["get"], detail=False, url_path="products-metrics")
    def products_metrics(self, request):
        """_summary_

        Args:
            request (_type_): _description_

        Returns:
            _type_: _description_
        """
        cache_key = f"products_metrics"
        cached_data = cache.get(cache_key)

        if cached_data is not None:
            return Response(cached_data, status=status.HTTP_200_OK)

        last_30_days = timezone.now().date() - datetime.timedelta(days=30)
        latest_orders_trackings = Subquery(
            models.OrderTracking.objects.filter(
                order=OuterRef('order__pk')
            ).order_by('-id').values('status__code_name')[:1]
        )

        # TODO AJUSTAR AQUI EL ESTADO CODENAME DADO UN ENUMERADO
        top_products = models.OrderProducts.objects.annotate(
            latest_status=latest_orders_trackings
        ).filter(
            order__creation_date__gte=last_30_days, latest_status='completed'
        ).values("product__id", "product__name").annotate(
            units_sold=Sum("quantity"),
            revenue=Sum(F("price") * F("quantity")),
            orders_count=Count("order", distinct=True),
        ).order_by("-revenue")

        low_stock_products = (
            models.Product.objects.filter(active=True, quantity__lte=F("minimal_stock"))
            .values("id", "name", "code_sku", "quantity", "minimal_stock")
            .order_by("quantity")
        )

        product_metrics = models.Product.objects.aggregate(
            total_products=Count("id"),
            active_products=Count("id", filter=Q(active=True)),
            out_of_stock=Count("id", filter=Q(quantity=0)),
            low_stock=Count("id", filter=Q(quantity__lte=F("minimal_stock"))),
            on_offer=Count("id", filter=Q(on_offer=True)),
        )
        result = {
            "top_products": [
                {
                    "id": item["product__id"],
                    "name": item["product__name"],
                    "units_sold": item["units_sold"],
                    "revenue": float(item["revenue"] or 0),
                    "orders_count": item["orders_count"],
                }
                for item in top_products
            ],
            "inventory_alerts": {
                "low_stock": list(low_stock_products),
                "out_of_stock": product_metrics["out_of_stock"],
                "total_alerts": product_metrics["low_stock"],
            },
            "summary": {
                "total_products": product_metrics["total_products"],
                "active_products": product_metrics["active_products"],
                "products_on_offer": product_metrics["on_offer"],
                "availability_rate": self._calculate_percentage(
                    product_metrics["active_products"] - product_metrics["out_of_stock"],
                    product_metrics["active_products"],
                ),
            },
        }
        cache.set(cache_key, result, 60 * 1)
        return Response(result, status=status.HTTP_200_OK)

    @action(methods=["get"], detail=False, url_path="clients-amount")
    def order_clients_amount(self, request):
        """Returns the total amount by clients in a given period.

        Args:
            request (GET): Filter by start_date, end_date

        Returns:
            List of clients with their total amounts
        """

        start_date, end_date = self.__get_request_dates(request)
        filters = {"creation_date__date__gte": start_date, "creation_date__date__lte": end_date}

        cache_key = f"clients_amount__{start_date}__{end_date}"
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data, status=status.HTTP_200_OK)
        latest_status = Subquery(
            models.OrderTracking.objects.filter(order=OuterRef('pk')).order_by('-id') \
                .values('status__code_name')[:1]
        )
        orders = self.get_queryset().annotate(
            latest_status=latest_status
        ).filter(**filters).exclude(latest_status__in=['cancelled', 'returned'])
        series = (
            orders.values("client")
            .annotate(
                total_amount=Sum(F("order_products__price") * F("order_products__quantity"))
            )
            .order_by("-total_amount")
        )
        result = [
            {
                "client": serializers.UserSerializer(
                    User.objects.get(id=serie["client"]),
                    context={"request": request},
                ).data,
                "total_amount": Decimal(serie["total_amount"] or 0),
            }
            for serie in series
        ]
        cache.set(cache_key, result, 60 * 60)
        return Response(result, status=status.HTTP_200_OK)

    @action(methods=["get"], detail=False, url_path="statuses")
    def orders_by_status(self, request):
        """Returns the total order by statuses in a given period.

        Args:
            request (GET): Filter by start_date, end_date.

        Returns:

        """
        start_date, end_date = self.__get_request_dates(request)
        cache_key = f"order__statuses__{start_date}__{end_date}"
        cached_data = cache.get(cache_key)

        if cached_data is not None:
            return Response(cached_data, status=status.HTTP_200_OK)

        filters = {"creation_date__date__gte": start_date, "creation_date__date__lte": end_date}
        orders = self.get_queryset().filter(**filters)
        orders = orders.annotate(
            status=Subquery(
                models.OrderTracking.objects.filter(
                    order=OuterRef("pk")
                ).order_by("-id").values("status")[:1]
            )
        )
        result = []
        statuses = models.OrderStatus.objects.all().order_by("order")
        for _status in statuses:
            value = orders.filter(status=_status).count()
            result.append({
                "value": value,
                "status": serializers.OrderStatusSerializer(_status).data,
            })
        cache.set(cache_key, result, 60 * 5)
        return Response(result, status=status.HTTP_200_OK)

    @action(methods=["get"], detail=False, url_path="payments")
    def orders_by_payment_status(self, request):
        """Returns the total order by payment statuses in a given period.

        Args:
            request (GET): Filter by start_date, end_date.

        Returns:

        """
        start_date, end_date = self.__get_request_dates(request)
        filters = {"creation_date__date__gte": start_date, "creation_date__date__lte": end_date}
        orders = self.get_queryset().filter(**filters)
        result = []
        for payment_status in Payment.PaymentStatus.values:
            value = orders.filter(payment__status=payment_status).count()
            result.append(
                {
                    "value": value,
                    "payment_status": payment_status,
                }
            )
        return Response(result, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="conversion-rate")
    def conversion_rate(self, request):
        start_date, end_date = self.__get_request_dates(request)
        cache_key = f"conversion_rate_{start_date}__{end_date}"
        cached_data = cache.get(cache_key)

        if cached_data is not None:
            return Response(cached_data, status=status.HTTP_200_OK)

        date_filters = {"date_joined__date__gte": start_date, "date_joined__date__lte": end_date}
        total_users = User.objects.filter(is_staff=False, **date_filters).count()

        users_with_purchases = (
            User.objects.filter(is_staff=False, orders_client__isnull=False, **date_filters)
            .distinct()
            .count()
        )
        conversion_rate = (
            (users_with_purchases / total_users) if total_users > 0 else 0
        )
        result = {
            "total_registered": total_users,
            "users_with_purchases": users_with_purchases,
            "users_without_purchases": total_users - users_with_purchases,
            "conversion_rate": round(conversion_rate, 2),
        }
        cache.set(cache_key, result, 60 * 1)
        return Response(result, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="weekly-conversion-rate")
    def weekly_conversion_rate(self, request):
        start_date, end_date = self.__get_request_dates(request)
        cache_key = f"weekly_conversion_rate_{start_date}__{end_date}"
        cached_data = cache.get(cache_key)

        if cached_data is not None:
            return Response(cached_data, status=status.HTTP_200_OK)

        weeks = []
        current_date = start_date
        while current_date <= end_date:
            week_end = min(current_date + datetime.timedelta(days=6), end_date)
            weeks.append(
                {
                    "week_start": current_date,
                    "week_end": week_end,
                    "week_number": current_date.isocalendar()[1],
                    "year": current_date.year,
                }
            )
            current_date = week_end + datetime.timedelta(days=1)

        weekly_data = []

        for week in weeks:
            week_users = User.objects.filter(
                date_joined__date__gte=week["week_start"],
                date_joined__date__lte=week["week_end"],
                is_staff=False,
            )

            total_users = week_users.count()

            users_with_purchases = (
                User.objects.filter(
                    date_joined__date__gte=week["week_start"],
                    date_joined__date__lte=week["week_end"],
                    is_staff=False,
                    orders_client__isnull=False,
                )
                .distinct()
                .count()
            )

            conversion_rate = (
                (users_with_purchases / total_users) if total_users > 0 else 0
            )

            weekly_data.append(
                {
                    "week": f"Semana {week['week_number']} - {week['year']}",
                    "period": {
                        "start": week["week_start"],
                        "end": week["week_end"],
                    },
                    "total_registered": total_users,
                    "users_with_purchases": users_with_purchases,
                    "users_without_purchases": total_users - users_with_purchases,
                    "conversion_rate": round(conversion_rate, 2),
                }
            )
        cache.set(cache_key, weekly_data, 60 * 60)
        return Response(
            weekly_data,
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"], url_path="weekly-payments")
    def weekly_payments(self, request):
        cache_key = f"weekly_payments_{timezone.now().strftime('%Y-%m-%d')}"
        cached_data = cache.get(cache_key)

        if cached_data is not None:
            return Response(cached_data, status=status.HTTP_200_OK)

        start_date, end_date = self.__get_request_dates(request)

        weeks = []
        current_date = start_date
        while current_date <= end_date:
            week_end = min(current_date + datetime.timedelta(days=6), end_date)
            weeks.append(
                {
                    "week_start": current_date,
                    "week_end": week_end,
                    "week_number": current_date.isocalendar()[1],
                    "year": current_date.year,
                }
            )
            current_date = week_end + datetime.timedelta(days=1)

        weekly_data = []
        latest_tracking = (
            models.OrderTracking.objects.filter(order=OuterRef("pk"))
            .order_by("-id")
            .values("status__code_name")[:1]
        )
        for week in weeks:
            week_payments = Payment.objects.annotate(
                latest_status=Subquery(latest_tracking)
            ).filter(
                status=Payment.PaymentStatus.Completed,
                latest_status="completed",
                created_at__date__gte=week["week_start"],
                created_at__date__lte=week["week_end"],
            )

            aggregates = week_payments.aggregate(
                total_payments=Count("id"),
                total_amount=Sum("amount"),
                total_commission=Sum("ecommerce_commission_amount"),
            )

            weekly_data.append(
                {
                    "week": f"Semana {week['week_number']} - {week['year']}",
                    "total_payments": aggregates["total_payments"] or 0,
                    "total_amount": float(aggregates["total_amount"] or 0),
                    "total_commission": float(aggregates["total_commission"] or 0),
                    "net_amount": float(
                        (aggregates["total_amount"] or 0)
                        - (aggregates["total_commission"] or 0)
                    ),
                }
            )
        cache.set(cache_key, weekly_data, 60 * 30)
        return Response(weekly_data, status=status.HTTP_200_OK)
