from delivery import models, serializers, filters
from core.views import ProtectedResourceViewSet
from core.permissions import (
    CustomPermissionFactory,
    ReadOnlyPermission,
    ClientPermission,
)
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.permissions import (
    AllowAny,
)
from core.models import Order, OrderTracking
from core.serializers import OrderSerializer
from django.db.models import OuterRef, Subquery
from core.tasks import NomenclatorCacheManager


class ShippingZoneViewSet(ProtectedResourceViewSet):
    """
    Shipping Zone model\n
    GET: Shows all Shipping Zone created.\n
    POST: Adds a new Shipping Zone.\n
    GET{id}: Retrieves a specific Shipping Zone determined by id.\n
    PUT{id}: Modifies all fields of a specific Shipping Zone determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific Shipping Zone determined by id.\n
    DELETE{id}: Deletes a specific Shipping Zone determined by id.\n
    """

    permission_classes = [ReadOnlyPermission| CustomPermissionFactory(["delivery.manage_shipping_zones"])]
    queryset = models.ShippingZone.objects.all()
    serializer_class = serializers.ShippingZoneSerializer
    search_fields = ["name"]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(active=True)

    def list(self, request, *args, **kwargs):
        page = request.query_params.get("page")
        page_size = request.query_params.get("page_size")
        search_term = request.query_params.get("search", "")

        if search_term and search_term.strip():
            return super().list(request, *args, **kwargs)

        cache_kwargs = {"page": page, "page_size": page_size, "search": search_term}

        cached_data = NomenclatorCacheManager.get_cached_data(
            "shippingzone", "list", request.user, **cache_kwargs
        )

        if cached_data is not None:
            return Response(cached_data)

        response = super().list(request, *args, **kwargs)

        if response.status_code == 200:
            NomenclatorCacheManager.set_cached_data(
                response.data,
                "shippingzone",
                "list",
                request.user,
                timeout=60 * 60 * 24,
                **cache_kwargs,
            )

        return response

    def retrieve(self, request, *args, **kwargs):
        cached_data = NomenclatorCacheManager.get_cached_data(
            "shippingzone", "retrieve", request.user, kwargs.get("pk")
        )

        if cached_data is not None:
            return Response(cached_data)

        response = super().retrieve(request, *args, **kwargs)

        if response.status_code == 200:
            NomenclatorCacheManager.set_cached_data(
                response.data,
                "shippingzone",
                "retrieve",
                request.user,
                pk=kwargs.get("pk"),
                timeout=60 * 60 * 24 * 7,
            )

        return response

    def perform_create(self, serializer):
        NomenclatorCacheManager.invalidate_model_cache("shippingzone")
        response = super().perform_create(serializer)
        return response

    def perform_update(self, serializer):
        NomenclatorCacheManager.invalidate_model_cache("shippingzone")
        response = super().perform_update(serializer)
        return response

    def perform_destroy(self, instance):
        NomenclatorCacheManager.invalidate_model_cache("shippingzone")
        response = super().perform_destroy(instance)
        return response


class ShippingMethodViewSet(ProtectedResourceViewSet):
    """
    Shipping Method model\n
    GET: Shows all Shipping Method created.\n
    POST: Adds a new Shipping Method.\n
    GET{id}: Retrieves a specific Shipping Method determined by id.\n
    PUT{id}: Modifies all fields of a specific Shipping Method determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific Shipping Method determined by id.\n
    DELETE{id}: Deletes a specific Shipping Method determined by id.\n
    """

    permission_classes = [ReadOnlyPermission |CustomPermissionFactory(["delivery.manage_shipping_methods"])]
    queryset = models.ShippingMethod.objects.all()
    serializer_class = serializers.ShippingMethodSerializer
    search_fields = ["name", "shipping_method_type"]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(active=True)

    def list(self, request, *args, **kwargs):
        page = request.query_params.get("page")
        page_size = request.query_params.get("page_size")
        search_term = request.query_params.get("search", "")

        if search_term and search_term.strip():
            return super().list(request, *args, **kwargs)

        cache_kwargs = {"page": page, "page_size": page_size, "search": search_term}

        cached_data = NomenclatorCacheManager.get_cached_data(
            "shippingmethod", "list", request.user, **cache_kwargs
        )

        if cached_data is not None:
            return Response(cached_data)

        response = super().list(request, *args, **kwargs)

        if response.status_code == 200:
            NomenclatorCacheManager.set_cached_data(
                response.data,
                "shippingmethod",
                "list",
                request.user,
                timeout=60 * 60 * 24 * 7,
                **cache_kwargs,
            )

        return response

    def retrieve(self, request, *args, **kwargs):
        cached_data = NomenclatorCacheManager.get_cached_data(
            "shippingmethod", "retrieve", request.user, kwargs.get("pk")
        )

        if cached_data is not None:
            return Response(cached_data)

        response = super().retrieve(request, *args, **kwargs)

        if response.status_code == 200:
            NomenclatorCacheManager.set_cached_data(
                response.data,
                "shippingmethod",
                "retrieve",
                request.user,
                pk=kwargs.get("pk"),
                timeout=60 * 60 * 24 * 30,
            )

        return response

    def perform_create(self, serializer):
        NomenclatorCacheManager.invalidate_model_cache("shippingmethod")
        response = super().perform_create(serializer)
        return response

    def perform_update(self, serializer):
        NomenclatorCacheManager.invalidate_model_cache("shippingmethod")
        response = super().perform_update(serializer)
        return response

    def perform_destroy(self, instance):
        NomenclatorCacheManager.invalidate_model_cache("shippingmethod")
        response = super().perform_destroy(instance)
        return response


class ShippingRateViewSet(ProtectedResourceViewSet):
    """
    Shipping Rate model\n
    GET: Shows all Shipping Rate created.\n
    POST: Adds a new Shipping Rate.\n
    GET{id}: Retrieves a specific Shipping Rate determined by id.\n
    PUT{id}: Modifies all fields of a specific Shipping Rate determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific Shipping Rate determined by id.\n
    DELETE{id}: Deletes a specific Shipping Rate determined by id.\n
    """

    permission_classes = [CustomPermissionFactory(["delivery.manage_delivery"])]
    queryset = models.ShippingRate.objects.all()
    filterset_class = filters.ShippingRateFilter
    serializer_class = serializers.ShippingRateSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(active=True)


class OrderShippingViewSet(ProtectedResourceViewSet):
    """
    Order Shipping model\n
    GET: Shows all Order Shipping created.\n
    POST: Adds a new Order Shipping.\n
    GET{id}: Retrieves a specific Order Shipping determined by id.\n
    PUT{id}: Modifies all fields of a specific Order Shipping determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific Order Shipping determined by id.\n
    DELETE{id}: Deletes a specific Order Shipping determined by id.\n
    """

    permission_classes = [CustomPermissionFactory(["delivery.manage_delivery"])]
    queryset = models.OrderShipping.objects.all()
    serializer_class = serializers.OrderShippingSerializer


class AssignOrdersToDelivererView(CreateAPIView):
    """_summary_

    Args:
        APIView (_type_): _description_

    Returns:
        _type_: _description_
    """

    permission_classes = [CustomPermissionFactory("delivery.manage_delivery")]
    serializer_class = serializers.AssignOrdersToDelivererSerializer


class OrdersReadyToShipWithoutDelivererView(ListAPIView):
    """_summary_

    Args:
        APIView (_type_): _description_

    Returns:
        _type_: _description_
    """

    permission_classes = [CustomPermissionFactory("delivery.manage_delivery")]
    serializer_class = OrderSerializer

    def get_queryset(self):
        queryset = Order.objects.filter(shipping__deliverer__isnull=True).exclude(shipping__isnull=True)
        latest_tracking = (
            OrderTracking.objects.filter(order=OuterRef("pk"))
            .order_by("-id")
            .values("status__code_name")[:1]
        )
        return queryset.annotate(cur_status=Subquery(latest_tracking)).filter(cur_status="ready_shipping")
