from decimal import Decimal
from django.db import models
from core.models import Municipality, Order
from user.models import User
from core.generics import PermissionsMeta
from django.utils.translation import gettext_lazy as _


class ShippingZone(models.Model):
    """
    Shipping Zones

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    name = models.CharField(max_length=100)
    deliverers = models.ManyToManyField(User, related_name="shipping_zones")
    municipalities = models.ManyToManyField(Municipality, related_name="shipping_zones")
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def is_empty(self) -> bool:
        """Verifica que la zona tenga repartidores asignados."""
        return not self.deliverers.exists()

    def municipality_count(self) -> int:
        """Total municipios en esta zona."""
        return self.municipalities.count()

    class Meta(PermissionsMeta.Meta):
        permissions = [("manage_shipping_zones", _("Can manage shipping zones"))]
        verbose_name = "Shipping Zone"
        verbose_name_plural = "Shipping Zones"
        ordering = ["-id"]


class ShippingMethod(models.Model):
    """
    Shipping Methods

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    SHIPPING_METHOD_TYPES = (
        ("standard", "Estándar"),
        ("express", "Express"),
    )

    name = models.CharField(max_length=100)
    shipping_method_type = models.CharField(
        max_length=20, choices=SHIPPING_METHOD_TYPES
    )
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta(PermissionsMeta.Meta):
        permissions = [("manage_shipping_methods", _("Can manage shipping methods"))]
        verbose_name = "Shipping Method"
        verbose_name_plural = "Shipping Methods"
        ordering = ["-id"]


class ShippingRate(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    shipping_zone = models.ForeignKey(
        ShippingZone, on_delete=models.CASCADE, related_name="zone_shipping_rates"
    )
    shipping_method = models.ForeignKey(
        ShippingMethod, on_delete=models.CASCADE, related_name="method_shipping_rates"
    )
    price = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    estimated_delivery_time = models.PositiveIntegerField()
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["shipping_zone", "shipping_method"]

    def __str__(self):
        return f"{self.shipping_zone} - {self.shipping_method}: ${self.price}"

    class Meta(PermissionsMeta.Meta):
        permissions = [("manage_shipping_rates", _("Can manage shipping rates"))]
        verbose_name = "Shipping Rate"
        verbose_name_plural = "Shipping Rates"
        ordering = ["-id"]


class OrderShipping(models.Model):
    """_summary_

    Args:
        models (_type_): _description_
    """

    order = models.OneToOneField(
        Order, related_name="shipping", on_delete=models.CASCADE
    )
    delivery_address = models.CharField(max_length=1024)
    shipping_rate = models.ForeignKey(
        ShippingRate,
        related_name="shipping_orders",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    deliverer = models.ForeignKey(
        User,
        related_name="shipping_orders",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    shipping_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    shipped_at = models.DateTimeField(blank=True, null=True)
    estimated_delivery_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "Order Shipping"

    class Meta(PermissionsMeta.Meta):
        permissions = [("manage_delivery", _("Can manage delivery"))]
        verbose_name = "Order Shipping"
        verbose_name_plural = "Order Shippings"
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["deliverer", "shipped_at"]),
            models.Index(fields=["shipped_at", "delivered_at"]),
            models.Index(fields=["estimated_delivery_at"]),
            models.Index(fields=["delivered_at"]),
        ]
