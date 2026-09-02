from decimal import Decimal
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from user.models import User
from core.models import Order, Category, Product
from core.generics import PermissionsMeta


class Coupon(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    COUPON_TYPES = [
        ("percentage", "Percentage"),
        ("fixed", "Fixed Amount"),
    ]

    code = models.CharField(max_length=50, unique=True)
    back_color = models.CharField(max_length=255, default="primary")
    description = models.TextField(blank=True, null=True)
    coupon_type = models.CharField(
        max_length=10, choices=COUPON_TYPES, default="percentage"
    )
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    max_discount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    min_purchase_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )

    max_uses = models.PositiveIntegerField(null=True, blank=True)
    uses_count = models.PositiveIntegerField(default=0)

    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField(null=True, blank=True)

    active = models.BooleanField(default=True)
    single_use = models.BooleanField(default=False)
    users_used = models.ManyToManyField(User, related_name="coupons", blank=True)

    applicable_categories = models.ManyToManyField(
        Category, related_name="coupons", blank=True
    )
    applicable_products = models.ManyToManyField(
        Product, related_name="coupons", blank=True
    )

    auto_assign_on_signup = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta(PermissionsMeta.Meta):
        permissions = [("manage_promotions", _("Can manage promotions"))]
        verbose_name = "Coupon"
        verbose_name_plural = "Coupons"

    def __str__(self):
        return self.code

    def is_valid(self, user=None, cart_total=0, cart_items=None):
        """Verifica si el cupón es válido"""
        if not self.active:
            return False, _("Inactive coupon")

        if self.valid_to and timezone.now() > self.valid_to:
            return False, _("Expired coupon")

        if self.valid_from and timezone.now() < self.valid_from:
            return False, _("Coupon not valid")

        if self.max_uses and self.uses_count >= self.max_uses:
            return False, _("Usage limit reached")

        if user and self.single_use:
            if CouponUsage.objects.filter(coupon=self, user=user).exists():
                return False, _("Single-use coupon")

        if 0 < cart_total < self.min_purchase_amount:
            return False, _("Insufficient minimum purchase")

        if cart_items is not None:
            # Verificar categorías aplicables
            if self.applicable_categories.exists():
                cart_categories = set(
                    item.product.category
                    for item in cart_items
                    if hasattr(item, "product") and item.product.category
                )
                applicable_categories = set(self.applicable_categories.all())

                if not cart_categories.intersection(applicable_categories):
                    return False, _("The coupon does not apply to products in the cart")

            # Verificar productos específicos
            if self.applicable_products.exists():
                cart_products = set(
                    item.product for item in cart_items if hasattr(item, "product")
                )
                applicable_products = set(self.applicable_products.all())

                if not cart_products.intersection(applicable_products):
                    return False, _("The coupon does not apply to products in the cart")

        return True, _("Valid")

    def calculate_discount(self, cart_total):
        """Calcula el descuento aplicable"""
        if self.coupon_type == "percentage":
            discount = cart_total * self.discount_value
            if self.max_discount and discount > self.max_discount:
                discount = self.max_discount
        else:
            discount = min(self.discount_value, cart_total)
        return discount

    def assign_to_user(self, user) -> bool:
        """Asigna el cupón a un usuario"""
        self.users_used.add(user)
        return True


class CouponUsage(models.Model):
    """_summary_

    Args:
        models (_type_): _description_
    """

    coupon = models.ForeignKey(
        Coupon, on_delete=models.PROTECT, related_name="coupon_usages"
    )
    user = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="coupon_usages"
    )
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="coupon_usages"
    )
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta(PermissionsMeta.Meta):
        unique_together = ["coupon", "user", "order"]


class CouponAssignment(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    ASSIGNMENT_TYPES = [
        ("signup", "User signup"),
        ("manual", "Manual assignment"),
        ("promotion", "Promotion"),
        # ('birthday', 'BirthDay'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="coupon_assignments"
    )
    coupon = models.ForeignKey(
        Coupon, on_delete=models.PROTECT, related_name="assignments"
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_type = models.CharField(
        max_length=20, choices=ASSIGNMENT_TYPES, default="signup"
    )
    used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    class Meta(PermissionsMeta.Meta):
        unique_together = ["user", "coupon"]
        verbose_name = "Asignación de Cupón"
        verbose_name_plural = "Asignaciones de Cupones"

    def __str__(self):
        return f"{self.user.username} - {self.coupon.code}"
