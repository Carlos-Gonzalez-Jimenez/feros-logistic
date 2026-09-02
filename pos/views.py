from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView, get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from core import filters
from core.builders import CreateOrderBuilder
from core.permissions import CustomPermissionFactory
from core.services import NotificationService
from core.views import cart_total_amount, cart_total_gross_weight, cart_total_net_weight, cart_total_boxes
from pos import models
from pos import serializers
from promotions.models import CouponAssignment
from promotions.serializers import CouponSerializer
from user.serializers import UserMinimalSerializer


class PosCartViewSet(viewsets.ModelViewSet):
    """_summary_

    Args:
        ModelViewSet (_type_): _description_
    """

    permission_classes = [CustomPermissionFactory(["user.manage_pos"])]
    queryset = models.PosCart.objects.all()
    serializer_class = serializers.PosCartSerializer

    def __serialize_products(self, products):
        return serializers.PosCartSerializer(products, many=True, context=self.get_serializer_context()).data

    def __serialize_response(self, products, client):
        return Response(
            {
                "total_amount": cart_total_amount(products, client.fee),
                "total_gross_weight": cart_total_gross_weight(products),
                "total_net_weight": cart_total_net_weight(products),
                "total_boxes": cart_total_boxes(products),
                "products": self.__serialize_products(products),
                "client_id": client.id,
                "client": UserMinimalSerializer(client, context=self.get_serializer_context()).data,
            },
            status=status.HTTP_200_OK,
        )

    def list(self, request):
        client_id = request.query_params.get("client_id")
        try:
            client = models.User.objects.get(id=client_id)
            products = (
                models.PosCart.objects.filter(client_id=client_id)
                .select_related("product")
                .prefetch_related("product__category")
            )

            return self.__serialize_response(products, client)
        except models.User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    def create(self, request):
        with transaction.atomic():
            serializer = self.serializer_class(
                data=request.data, context={"request": request}
            )
            serializer.is_valid(raise_exception=True)

            product = serializer.save()
            client = product.client

            products = models.PosCart.objects.filter(client_id=client.id)
            return self.__serialize_response(products, client)

    def update(self, request, *args, **kwargs):
        with transaction.atomic():
            partial = kwargs.pop("partial", False)
            instance = self.get_object()
            client = instance.client

            serializer = self.get_serializer(
                instance, data=request.data, partial=partial
            )
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)

            products = (
                models.PosCart.objects.filter(client_id=client.id)
                .select_related("product")
                .prefetch_related("product__category")
            )
            return self.__serialize_response(products, client)

    def destroy(self, request, pk):
        with transaction.atomic():
            instance = self.get_object()
            client = instance.client
            self.perform_destroy(instance)
            products = models.PosCart.objects.filter(client_id=client.id)
            return self.__serialize_response(products, client)

    @action(
        detail=False,
        methods=["get"],
        url_path=r"clear",
        permission_classes=[CustomPermissionFactory(["user.manage_pos"])],
    )
    def delete_pos_cart(self, request):
        client_id = request.query_params.get("client_id")
        client = get_object_or_404(models.User, id=client_id)

        with transaction.atomic():
            models.PosCart.objects.filter(client_id=client_id).delete()
            return self.__serialize_response([], client)

    @action(
        detail=False,
        methods=["post"],
        url_path=r"add-products",
        permission_classes=[CustomPermissionFactory(["user.manage_pos"])],
    )
    def pos_add_products(self, request, pk=None):
        serializer = serializers.PosAddProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            try:
                user = self.request.user
                client = serializer.validated_data["client_id"]
                code_sku = serializer.validated_data["code_sku"]

                product = get_object_or_404(
                    models.Product, code_sku=code_sku, active=True
                )
                pos_cart_product, created = models.PosCart.objects.get_or_create(
                    client=client,
                    product=product,
                    defaults={"seller": user, "quantity": 1},
                )
                if not created:
                    pos_cart_product.quantity += 1
                    pos_cart_product.save()

                products = models.PosCart.objects.filter(client=client)
                return self.__serialize_response(products, client)
            except Exception:
                return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=["post"],
        url_path=r"checkout",
        permission_classes=[CustomPermissionFactory(["user.manage_pos"])],
    )
    def pos_checkout(self, request):
        with transaction.atomic():
            serializer = serializers.CreatePosOrderSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            try:
                user = self.request.user
                client = serializer.validated_data.get("client_id")

                builder = CreateOrderBuilder(models.PosCart, serializer.validated_data, client=client, seller=user)
                builder.create_order()
                builder.append_order_products()
                builder.apply_discount()
                builder.add_shipping()
                builder.add_credit()
                builder.clear_cart()
                builder.add_expiration_days()

                builder.update_order_amounts()
                builder.add_initial_state("Estado inicial [Solicitud de compra creada en el punto de venta]")
                response, _ = builder.create_payment()

                builder.sync_with_odoo()
                order = builder.order

                NotificationService.send_notification(
                    "Nueva solicitud de compra",
                    f"Se ha creado una solicitud de compra <b>{order}</b> desde el punto de venta para el cliente <b>{client.first_name} {client.last_name}</b>",
                    [user, client],
                    "Informativo",
                    ["IN_APP", "WHATSAPP"],
                )

                return Response(response, status=status.HTTP_200_OK)

            except models.PosCart.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)


class PosShopViewSet(ListAPIView):
    permission_classes = [CustomPermissionFactory(["user.manage_pos"])]
    queryset = models.Product.objects.filter(active=True, quantity__gt=0)
    serializer_class = serializers.ProductPosSerializer
    filterset_class = filters.ProductFilter
    pagination_class = None


class UserValidPosCouponsAPIView(APIView):
    """
    API para obtener cupones asignados y válidos para el usuario actual según los productos en su carrito.
    """

    serializer_class = CouponSerializer
    permission_classes = [CustomPermissionFactory(["user.manage_pos"])]

    def get(self, request):
        user = request.user
        client_id = request.query_params.get("client_id")
        client = get_object_or_404(models.User, id=client_id)

        # Obtener productos del carrito del usuario
        cart_items = (
            models.PosCart.objects.select_related("product").filter(client=client).all()
        )
        cart_total = self.calculate_pos_cart_total(cart_items, client.fee)

        # Obtener asignaciones de cupones del usuario
        assignments = CouponAssignment.objects.select_related("coupon").filter(
            user=client, used=False
        )

        valid_coupons = []

        for assignment in assignments:
            coupon = assignment.coupon

            # Validar cupón para el usuario y la compra
            _valid, _message = coupon.is_valid(user, cart_total, cart_items)

            if _valid:
                # Calcular descuento potencial
                discount_amount = coupon.calculate_discount(cart_total)
                valid_coupons.append(
                    {
                        "coupon": CouponSerializer(coupon).data,
                        "discount_amount": discount_amount,
                    }
                )

        return Response(valid_coupons, status=status.HTTP_200_OK)

    def calculate_pos_cart_total(self, cart_items, fee):
        """Calcula el total del carrito"""
        total = 0
        for item in cart_items:
            if hasattr(item, "product") and item.product:
                total += item.quantity * item.product.sell_price(fee)
        return total
