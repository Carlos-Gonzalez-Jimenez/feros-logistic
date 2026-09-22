from django.db import transaction
from django.db.models import Prefetch
from django.db.models import ProtectedError
from django.db.models import (
    Q,
)
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.generics import (
    RetrieveUpdateAPIView,
    ListAPIView,
)
from rest_framework.permissions import (
    AllowAny,
)
from rest_framework.response import Response

from core import models, serializers, filters
from core.exceptions import (
    ProtectedInstanceException,
)
from .permissions import (
    CustomPermissionFactory,
    ReadOnlyPermission,
)


class ProtectedResourceViewSet(viewsets.ModelViewSet):
    def destroy(self, request, *args, **kwargs):
        with transaction.atomic():
            instance = self.get_object()
            try:
                self.perform_destroy(instance)
                return Response(status=status.HTTP_204_NO_CONTENT)

            except ProtectedError as exception:
                raise ProtectedInstanceException() from exception


class ShippingCompanyViewSet(ProtectedResourceViewSet):
    """
    Shipping Company model\n
    GET: Shows all Shipping Companies created.\n
    POST: Adds a new Shipping Company.\n
    GET{id}: Retrieves a specific Shipping Company determined by id.\n
    PUT{id}: Modifies all fields of a specific Shipping Company determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific Shipping Company determined by id.\n
    DELETE{id}: Deletes a specific Shipping Company determined by id.\n
    """

    permission_classes = [
        ReadOnlyPermission
        | CustomPermissionFactory(["core.manage_shipping_companies"]),
    ]
    queryset = models.ShippingCompany.objects.all()
    serializer_class = serializers.ShippingCompanySerializer
    search_fields = ["name"]


class VesselViewSet(ProtectedResourceViewSet):
    """
    Vessel model\n
    GET: Shows all Vessels created.\n
    POST: Adds a new Vessel.\n
    GET{id}: Retrieves a specific Vessel determined by id.\n
    PUT{id}: Modifies all fields of a specific Vessel determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific Vessel determined by id.\n
    DELETE{id}: Deletes a specific Vessel determined by id.\n
    """

    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["core.manage_vessels"]),
    ]
    queryset = models.Vessel.objects.all()
    serializer_class = serializers.VesselSerializer
    search_fields = ["name"]


class ContainerTypeViewSet(ProtectedResourceViewSet):
    """
    Container Type model\n
    GET: Shows all Container Types created.\n
    POST: Adds a new Container Type.\n
    GET{id}: Retrieves a specific Container Type determined by id.\n
    PUT{id}: Modifies all fields of a specific Container Type determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific Container Type determined by id.\n
    DELETE{id}: Deletes a specific Container Type determined by id.\n
    """

    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["core.manage_container_types"]),
    ]
    queryset = models.ContainerType.objects.all()
    serializer_class = serializers.ContainerTypeSerializer
    search_fields = ["name"]


class CurrencyViewSet(ProtectedResourceViewSet):
    """
    Currency model\n
    GET: Shows all Currencies created.\n
    POST: Adds a new Currency.\n
    GET{id}: Retrieves a specific Currency determined by id.\n
    PUT{id}: Modifies all fields of a specific Currency determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific Currency determined by id.\n
    DELETE{id}: Deletes a specific Currency determined by id.\n
    """

    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["core.manage_currencies"]),
    ]
    queryset = models.Currency.objects.all()
    serializer_class = serializers.CurrencySerializer
    search_fields = ["name", "initials"]


class CountryViewSet(ProtectedResourceViewSet):
    """
    Country model\n
    GET: Shows all Countries created.\n
    POST: Adds a new Country.\n
    GET{id}: Retrieves a specific Country determined by id.\n
    PUT{id}: Modifies all fields of a specific Country determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific Country determined by id.\n
    DELETE{id}: Deletes a specific Country determined by id.\n
    """

    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["core.manage_country"]),
    ]
    queryset = models.Country.objects.all()
    serializer_class = serializers.CountrySerializer
    search_fields = ["name", "code_alpha3"]


class ProviderViewSet(ProtectedResourceViewSet):
    """
    Provider model\n
    GET: Shows all Providers created.\n
    POST: Adds a new Provider.\n
    GET{id}: Retrieves a specific Provider determined by id.\n
    PUT{id}: Modifies all fields of a specific Provider determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific Provider determined by id.\n
    DELETE{id}: Deletes a specific Provider determined by id.\n
    """

    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["core.manage_provider"]),
    ]
    queryset = models.Provider.objects.all()
    serializer_class = serializers.ProviderSerializer
    search_fields = ["name"]


class NotificationTypeViewSet(ProtectedResourceViewSet):
    """
    NotificationType model\n
    GET: Shows all Notification Types created.\n
    POST: Adds a new Notification Type.\n
    GET{id}: Retrieves a specific Notification Type determined by id.\n
    PUT{id}: Modifies all fields of a specific Notification Type determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific Notification Type determined by id.\n
    DELETE{id}: Deletes a specific Notification Type determined by id.\n
    """

    permission_classes = [
        ReadOnlyPermission,
    ]
    queryset = models.NotificationType.objects.all()
    serializer_class = serializers.NotificationTypeSerializer


class NotificationViewSet(ProtectedResourceViewSet):
    """
    Notification model\n
    GET: Shows all Notifications created.\n
    POST: Adds a new Notification.\n
    GET{id}: Retrieves a specific Notification determined by id.\n
    PUT{id}: Modifies all fields of a specific Notification determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific Notification determined by id.\n
    DELETE{id}: Deletes a specific Notification determined by id.\n
    """

    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["core.manage_notification"])
    ]
    queryset = models.Notification.objects.all()
    serializer_class = serializers.NotificationSerializer
    search_fields = ["title", "message"]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


class NotificationUserViewSet(viewsets.ModelViewSet):
    queryset = models.NotificationUser.objects.all()
    serializer_class = serializers.NotificationUserSerializer
    filterset_class = filters.NotificationUserFilter

    @action(
        methods=["post"],
        detail=True,
        url_path="mark-as-read",
        permission_classes=[AllowAny],
    )
    def mark_notification_as_read(self, request, pk=None):
        with transaction.atomic():
            notification_user = self.get_object()
            if notification_user.user_id == request.user.id:
                notification_user.read = True
                notification_user.save()
                return Response(status=status.HTTP_200_OK)
            return Response(status=status.HTTP_404_NOT_FOUND)

    @action(
        methods=["post"],
        detail=False,
        url_path="mark-all-as-read",
        permission_classes=[AllowAny],
    )
    def mark_all_notifications_as_read(self, request, pk=None):
        with transaction.atomic():
            models.NotificationUser.objects.filter(
                user=request.user, read=False
            ).update(read=True)
            return Response(status=status.HTTP_200_OK)

    @action(
        methods=["get"], detail=False, url_path="status", permission_classes=[AllowAny]
    )
    def user_notifications_status(self, request, pk=None):
        with transaction.atomic():
            notifications_user = models.NotificationUser.objects.filter(
                user=request.user
            )
            data = {"unread": None, "total": notifications_user.count()}
            data["unread"] = notifications_user.filter(read=False).count()
            return Response(data, status=status.HTTP_200_OK)

    @action(
        methods=["get"],
        detail=False,
        url_path="received",
        permission_classes=[AllowAny],
    )
    def user_notifications_received(self, request, pk=None):
        with transaction.atomic():
            received = models.NotificationUser.objects.filter(user=request.user)
            filter_class = filters.NotificationUserFilter(
                request.query_params, queryset=received
            )
            received = filter_class.qs
            paginated = self.paginate_queryset(received)
            serializer = self.get_serializer(paginated, many=True)
            return self.get_paginated_response(serializer.data)


class BrandViewSet(ProtectedResourceViewSet):
    """
    Brand model\n
    GET: Shows all Brands created.\n
    POST: Adds a new Brand.\n
    GET{id}: Retrieves a specific Brand determined by id.\n
    PUT{id}: Modifies all fields of a specific Brand determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific Brand determined by id.\n
    DELETE{id}: Deletes a specific Brand determined by id.\n
    """

    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["core.manage_brand"]),
    ]
    queryset = models.Brand.objects.all()
    serializer_class = serializers.BrandSerializer
    search_fields = ["name", "description"]


class CategoryViewSet(ProtectedResourceViewSet):
    """
    Category model\n
    GET: Shows all Categories created.\n
    POST: Adds a new Category.\n
    GET{id}: Retrieves a specific Category determined by id.\n
    PUT{id}: Modifies all fields of a specific Category determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific Category determined by id.\n
    DELETE{id}: Deletes a specific Category determined by id.\n
    """

    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["core.manage_category"])
    ]
    queryset = models.Category.objects.all()
    serializer_class = serializers.CategorySerializer
    search_fields = ["name"]

    @action(
        detail=True,
        methods=["get"],
        url_path=r"subcategories",
        permission_classes=[AllowAny],
    )
    def sub_categories(self, request, pk=None):
        with transaction.atomic():
            category = self.get_object()
            sub_categories = models.Category.objects.filter(
                parent=category.id, active=True
            )
            return Response(
                serializers.CategorySerializer(
                    sub_categories, many=True, context={"request": request}
                ).data,
                status=status.HTTP_200_OK,
            )


class MeasurementUnitViewSet(ProtectedResourceViewSet):
    """
    Measurement Unit model\n
    GET: Shows all Measurement Units created.\n
    POST: Adds a new Measurement Unit.\n
    GET{id}: Retrieves a specific Measurement Unit determined by id.\n
    PUT{id}: Modifies all fields of a specific Measurement Unit determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific Measurement Unit determined by id.\n
    DELETE{id}: Deletes a specific Measurement Unit determined by id.\n
    """

    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["core.manage_measurement_unit"])
    ]
    queryset = models.Measurement_Unit.objects.all()
    serializer_class = serializers.MeasurementUnitSerializer
    search_fields = ["name", "abbreviation"]


class SpecificationsViewSet(ProtectedResourceViewSet):
    """
    Specification model\n
    GET: Shows all specifications created.\n
    POST: Adds a new specification.\n
    GET{id}: Retrieves a specific specification determined by id.\n
    PUT{id}: Modifies all fields of a specific specification determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific specification determined by id.\n
    DELETE{id}: Deletes a specific specification determined by id.\n
    """

    queryset = models.Specifications.objects.all()
    serializer_class = serializers.SpecificationsSerializer
    search_fields = ["name"]


class SpecificationDetailsViewSet(ProtectedResourceViewSet):
    """
    Specification Detail model\n
    GET: Shows all specification details created.\n
    POST: Adds a new specification detail.\n
    GET{id}: Retrieves a specific specification detail determined by id.\n
    PUT{id}: Modifies all fields of a specific specification detail determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific specification detail determined by id.\n
    DELETE{id}: Deletes a specific specification detail determined by id.\n
    """

    queryset = models.SpecificationDetails.objects.all()
    serializer_class = serializers.SpecificationDetailsSerializer


class ProductViewSet(ProtectedResourceViewSet):
    """
    Product model\n
    GET: Shows all Products created.\n
    POST: Adds a new Product.\n
    GET{id}: Retrieves a specific Product determined by id.\n
    PUT{id}: Modifies all fields of a specific Product determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific Product determined by id.\n
    DELETE{id}: Deletes a specific Product determined by id.\n
    """

    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["core.manage_product"])
    ]
    queryset = models.Product.objects.all()
    filterset_class = filters.ProductFilter
    search_fields = ["code_sku", "name"]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return serializers.ProductWriteSerializer
        if self.action == "list":
            return serializers.ProductReadMinimalSerializer
        return serializers.ProductReadSerializer

    def perform_update(self, serializer):
        with transaction.atomic():
            response = super().perform_update(serializer)
            return response

    def get_category_tree(self):
        categories = models.Category.objects.filter(active=True).prefetch_related(
            Prefetch(
                "products",
                queryset=models.Product.objects.filter(active=True).only(
                    "code_sku",
                    "name",
                    "unit_price",
                    "quantity",
                    "active",
                    "category_id",
                ),
            )
        )
        category_dict = {}
        root_categories = []
        for cat in categories:
            category_dict[cat.id] = {
                "obj": cat,
                "children": [],
                "products": list(cat.products.all()),
                "parent_id": cat.parent_id,
            }
        for _, cat_data in category_dict.items():
            parent_id = cat_data["parent_id"]

            if parent_id and parent_id in category_dict:
                category_dict[parent_id]["children"].append(cat_data)
            else:
                root_categories.append(cat_data)
        return root_categories


class PresentationViewSet(ProtectedResourceViewSet):
    """
    Presentation model\n
    GET: Shows all Presentations created.\n
    POST: Adds a new Presentation.\n
    GET{id}: Retrieves a specific Presentation determined by id.\n
    PUT{id}: Modifies all fields of a specific Presentation determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific Presentation determined by id.\n
    DELETE{id}: Deletes a specific Presentation determined by id.\n
    """

    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["core.manage_presentation"])
    ]
    serializer_class = serializers.PresentationSerializer
    queryset = models.Presentation.objects.all()
    search_fields = ["name"]


class ProductProviderViewSet(ProtectedResourceViewSet):
    """
    Product Presentation model\n
    GET: Shows all Product Presentations created.\n
    POST: Adds a new Product Presentation.\n
    GET{id}: Retrieves a specific Product Presentation determined by id.\n
    PUT{id}: Modifies all fields of a specific Product Presentation determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific Product Presentation determined by id.\n
    DELETE{id}: Deletes a specific Product Presentation determined by id.\n
    """

    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["core.manage_presentation"])
    ]
    queryset = models.ProductProvider.objects.all()

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return serializers.ProductProviderWriteSerializer
        return serializers.ProductProviderReadSerializer


class ProductProviderPresentationsListAPIView(ListAPIView):
    """_summary_

    Args:
        ListAPIView (_type_): _description_
    """

    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["core.manage_presentation"])
    ]
    serializer_class = serializers.ProductProviderPresentationSerializer
    queryset = models.ProductProviderPresentation.objects.filter(active=True).all()
    filterset_class = filters.ProductProviderPresentationFilter
    pagination_class = None


class ProductSlugView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = serializers.ProductReadSerializer

    def get_queryset(self):
        return models.Product.objects.select_related(
            "category",
            "brand",
            "provider",
            "country",
            "measurement_unit",
        ).filter(active=True)

    def get(self, request, slug):
        try:
            product = self.get_queryset().get(slug=slug)
            serializer = self.get_serializer(product)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except models.Product.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


class CategoriesWithProductsView(ListAPIView):
    """_summary_

    Args:
        ListAPIView (_type_): _description_

    Returns:
        _type_: _description_
    """

    permission_classes = [AllowAny]
    queryset = models.Category.objects.all()
    serializer_class = serializers.CategorySerializer

    def list(self, request):
        """_summary_

        Args:
            request (_type_): _description_

        Returns:
            _type_: _description_
        """
        is_active = request.GET.get("active", "false") == "true"
        queryset = models.Product.objects.all()
        if is_active:
            queryset = queryset.filter(active=True)

        categories = models.Category.objects.filter(
            Q(id__in=queryset.values_list("category_id", flat=True)) | Q(parent=None),
            active=True,
        )

        serializer = serializers.CategorySerializer(
            categories,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class CountriesWithProductsView(ListAPIView):
    """_summary_

    Args:
        APIView (_type_): _description_

    Returns:
        _type_: _description_
    """

    permission_classes = [AllowAny]
    queryset = models.Country.objects.all()
    serializer_class = serializers.CountrySerializer

    def list(self, request):
        """_summary_

        Args:
            request (_type_): _description_

        Returns:
            _type_: _description_
        """
        countries = models.Country.objects.filter(product__active=True).distinct()

        serializer = serializers.CountrySerializer(
            countries,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class ConfigAPIView(RetrieveUpdateAPIView):
    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["core.manage_config"])
    ]
    serializer_class = serializers.ConfigSerializer

    def get_object(self):
        return get_object_or_404(models.Config, pk=1)

    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        return Response(data)

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return response

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


class PortViewSet(ProtectedResourceViewSet):
    """
    Port model\n
    GET: Shows all ports created.\n
    POST: Adds a new port.\n
    GET{id}: Retrieves a specific port determined by id.\n
    PUT{id}: Modifies all fields of a specific port determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific port determined by id.\n
    DELETE{id}: Deletes a specific port determined by id.\n
    """

    queryset = models.Port.objects.all()
    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["core.manage_ports"])
    ]
    serializer_class = serializers.PortSerializer
    search_fields = ["name", "abbreviation"]


class IncotermsViewSet(ProtectedResourceViewSet):
    """
    Incoterms model\n
    GET: Shows all incoterms created.\n
    POST: Adds a new incoterms.\n
    GET{id}: Retrieves a specific incoterms determined by id.\n
    PUT{id}: Modifies all fields of a specific incoterms determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific incoterms determined by id.\n
    DELETE{id}: Deletes a specific incoterms determined by id.\n
    """

    queryset = models.Incoterms.objects.all()
    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["core.manage_incoterms"])
    ]
    serializer_class = serializers.IncotermsSerializer
    search_fields = ["name", "abbreviation"]


class ProcessingPlantViewSet(ProtectedResourceViewSet):
    """
    Processing Plant model\n
    GET: Shows all processing plants created.\n
    POST: Adds a new processing plant.\n
    GET{id}: Retrieves a specific processing plant determined by id.\n
    PUT{id}: Modifies all fields of a specific processing plant determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific processing plant determined by id.\n
    DELETE{id}: Deletes a specific processing plant determined by id.\n
    """

    queryset = models.ProcessingPlant.objects.all()
    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["core.manage_processing_plant"])
    ]
    serializer_class = serializers.ProcessingPlantSerializer
    search_fields = ["name"]


class PurchaseOrderViewSet(ProtectedResourceViewSet):
    """
    Purchase Order model\n
    GET: Shows all purchase orders created.\n
    POST: Adds a new purchase order.\n
    GET{id}: Retrieves a specific purchase order determined by id.\n
    PUT{id}: Modifies all fields of a specific purchase order determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific purchase order determined by id.\n
    DELETE{id}: Deletes a specific purchase order determined by id.\n
    """

    queryset = models.PurchaseOrder.objects.all()
    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["core.manage_purchase_orders"])
    ]
    serializer_class = serializers.PurchaseOrderSerializer


class SaleOrderViewSet(ProtectedResourceViewSet):
    """
    Sale Order model\n
    GET: Shows all sale orders created.\n
    POST: Adds a new sale order.\n
    GET{id}: Retrieves a specific sale order determined by id.\n
    PUT{id}: Modifies all fields of a specific sale order determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific sale order determined by id.\n
    DELETE{id}: Deletes a specific sale order determined by id.\n
    """

    queryset = models.SaleOrder.objects.all()
    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["core.manage_sale_orders"])
    ]
    serializer_class = serializers.SaleOrderSerializer


class ProviderInvoiceViewSet(ProtectedResourceViewSet):
    """
    Provider Invoice model\n
    GET: Shows all Provider Invoices created.\n
    POST: Adds a new Provider Invoice.\n
    GET{id}: Retrieves a specific Provider Invoice determined by id.\n
    PUT{id}: Modifies all fields of a specific Provider Invoice determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific Provider Invoice determined by id.\n
    DELETE{id}: Deletes a specific Provider Invoice determined by id.\n
    """

    queryset = models.ProviderInvoice.objects.all()
    serializer_class = serializers.ProviderInvoiceSerializer
    search_fields = ["pi_number"]


class ProviderInvoicePaymentsViewSet(ProtectedResourceViewSet):
    """
    Provider Invoice Payment model\n
    GET: Shows all Provider Invoice Payments created.\n
    POST: Adds a new Provider Invoice Payment.\n
    GET{id}: Retrieves a specific Provider Invoice Payment determined by id.\n
    PUT{id}: Modifies all fields of a specific Provider Invoice Payment determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific Provider Invoice Payment determined by id.\n
    DELETE{id}: Deletes a specific Provider Invoice Payment determined by id.\n
    """

    queryset = models.ProviderInvoicePayments.objects.all()
    serializer_class = serializers.ProviderInvoicePaymentsSerializer


class PaymentAgreementViewSet(ProtectedResourceViewSet):
    """
    Payment Agreement model\n
    GET: Shows all Payment Agreements created.\n
    POST: Adds a new Payment Agreement.\n
    GET{id}: Retrieves a specific Payment Agreement determined by id.\n
    PUT{id}: Modifies all fields of a specific Payment Agreement determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific Payment Agreement determined by id.\n
    DELETE{id}: Deletes a specific Payment Agreement determined by id.\n
    """

    queryset = models.PaymentAgreement.objects.all()
    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["core.manage_payment_agreements"])
    ]
    serializer_class = serializers.PaymentAgreementSerializer


class ShippingCompanyInvoiceViewSet(ProtectedResourceViewSet):
    """
    Shipping Company Invoice model\n
    GET: Shows all Shipping Company Invoices created.\n
    POST: Adds a new Shipping Company Invoice.\n
    GET{id}: Retrieves a specific Shipping Company Invoice determined by id.\n
    PUT{id}: Modifies all fields of a specific Shipping Company Invoice determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific Shipping Company Invoice determined by id.\n
    DELETE{id}: Deletes a specific Shipping Company Invoice determined by id.\n
    """

    queryset = models.ShippingCompanyInvoice.objects.all()
    serializer_class = serializers.ShippingCompanyInvoiceSerializer


class ProviderInvoiceV2ViewSet(ProtectedResourceViewSet):
    queryset = models.ProviderInvoiceV2.objects.all()
    serializer_class = serializers.ProviderInvoiceV2Serializer
