from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticatedOrReadOnly,
)
from rest_framework import viewsets, status
from rest_framework.views import APIView
from promotions import models, serializers
from core.models import Cart
from core.permissions import (
    CustomPermissionFactory,
    ReadOnlyPermission,
    ClientPermission,
)


class CouponViewSet(viewsets.ModelViewSet):
    """_summary_

    Args:
        viewsets (_type_): _description_

    Returns:
        _type_: _description_
    """

    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["promotions.manage_promotions"]),
    ]
    queryset = models.Coupon.objects.all()
    serializer_class = serializers.CouponSerializer

    @action(
        detail=True,
        methods=["get"],
        url_path="assignments",
        permission_classes=[
            ReadOnlyPermission
            | CustomPermissionFactory(["promotions.manage_promotions"]),
        ],
    )
    def coupon_assignments(self, request, pk=None):
        """Devuelve todas las asignaciones de un cupón"""

        coupon = self.get_object()
        assignments = models.CouponAssignment.objects.filter(
            coupon_id=coupon.id
        ).order_by("assigned_at")
        paginated = self.paginate_queryset(assignments)
        assignments = serializers.CouponAssignmentSerializer(
            paginated, many=True, context={"request": request}
        ).data
        return self.get_paginated_response(assignments)

    @action(
        detail=True,
        methods=["get"],
        url_path="usages",
        permission_classes=[
            ReadOnlyPermission
            | CustomPermissionFactory(["promotions.manage_promotions"]),
        ],
    )
    def coupon_usages(self, request, pk=None):
        """Devuelve todos los usos de un cupón"""

        coupon = self.get_object()
        usages = models.CouponUsage.objects.filter(coupon_id=coupon.id).order_by(
            "used_at"
        )
        paginated = self.paginate_queryset(usages)
        usages = serializers.CouponUsageSerializer(
            paginated, many=True, context={"request": request}
        ).data
        return self.get_paginated_response(usages)

    @action(
        detail=True,
        methods=["post"],
        url_path="assign-users",
        permission_classes=[
            ReadOnlyPermission
            | CustomPermissionFactory(["promotions.manage_promotions"]),
        ],
    )
    def coupon_assign_users(self, request, pk=None):
        """Realiza las asignaciones de usuarios a un cupón"""

        coupon = self.get_object()
        user_ids = request.data.get("user_ids", [])

        if not user_ids:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        user_assignments_to_create = []
        for user_id in user_ids:
            try:
                assignment = models.CouponAssignment(
                    coupon_id=coupon.id,
                    user_id=user_id,
                    assigned_type="manual",
                )
                user_assignments_to_create.append(assignment)
            except (ValueError, TypeError):
                continue

        models.CouponAssignment.objects.bulk_create(
            user_assignments_to_create, ignore_conflicts=True
        )

        return Response(
            status=status.HTTP_200_OK,
        )

class UserValidCouponsAPIView(APIView):
    """
    API para obtener cupones asignados y válidos para el usuario actual según los productos en su carrito.
    """

    serializer_class = serializers.CouponSerializer
    permission_classes = [ClientPermission]

    def get(self, request):
        user = request.user

        # Obtener productos del carrito del usuario
        cart_items = Cart.objects.select_related("product").filter(client=user).all()
        cart_total = self.calculate_cart_total(cart_items, user.fee)

        # Obtener asignaciones de cupones del usuario
        assignments = models.CouponAssignment.objects.select_related("coupon").filter(user=user, used=False)

        valid_coupons = []

        for assignment in assignments:
            coupon = assignment.coupon

            # Validar cupón para el usuario y la compra
            _valid, _message = coupon.is_valid(user, cart_total, cart_items)

            if _valid:
                # Calcular descuento potencial
                discount_amount = coupon.calculate_discount(cart_total)
                valid_coupons.append({
                    'coupon': serializers.CouponSerializer(coupon).data,
                    'discount_amount': discount_amount
                })

        return Response(valid_coupons, status=status.HTTP_200_OK)

    def calculate_cart_total(self, cart_items, fee):
        """Calcula el total del carrito"""
        total = 0
        for item in cart_items:
            if hasattr(item, "product") and item.product:
                total += item.quantity * item.product.sell_price(fee)
        return total


class CouponAssignmentViewSet(viewsets.ModelViewSet):
    """_summary_

    Returns:
        _type_: _description_
    """

    serializer_class = serializers.CouponAssignmentSerializer
    queryset = models.CouponAssignment.objects.all()
    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["promotions.manage_promotions"]),
    ]


class CouponUsageViewSet(viewsets.ReadOnlyModelViewSet):
    """_summary_

    Args:
        viewsets (_type_): _description_

    Returns:
        _type_: _description_
    """

    serializer_class = serializers.CouponUsageSerializer
    permission_classes = [ReadOnlyPermission | CustomPermissionFactory(["promotions.manage_promotions"])]

    def get_queryset(self):
        queryset = models.CouponUsage.objects.all()

        coupon_code = self.request.query_params.get("coupon_code")
        if coupon_code:
            queryset = queryset.filter(coupon__code__icontains=coupon_code)

        user_email = self.request.query_params.get("user_email")
        if user_email:
            queryset = queryset.filter(user__email__icontains=user_email)

        return queryset.select_related("coupon", "user")
