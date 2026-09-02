from decimal import Decimal
from django.db import models
from core.generics import PermissionsMeta
from core.models import Product
from user.models import User


class PosCart(models.Model):
    """_summary_

    Args:
        models (_type_): _description_
    """

    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    seller = models.ForeignKey(
        User, related_name="seller_cart", on_delete=models.PROTECT
    )
    client = models.ForeignKey(
        User, related_name="client_cart", on_delete=models.PROTECT
    )
    product = models.ForeignKey(
        Product, related_name="product_cart", on_delete=models.PROTECT
    )

    def __str__(self):
        return f"{self.seller}/{self.client}-{self.product}"

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Pos Cart"
        verbose_name_plural = "Pos Carts"
        ordering = ["id"]
        indexes = [
            models.Index(fields=["seller", "client", "product"]),
        ]
