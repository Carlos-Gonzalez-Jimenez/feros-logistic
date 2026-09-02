from decimal import Decimal

from django.db import models
from django.utils.translation import gettext_lazy as _

from core.generics import PermissionsMeta
from core.models import Order, Currency
from user.models import User


class Wallet(models.Model):
    """_summary_

    Args:
        models (_type_): _description_
    """

    user = models.OneToOneField(User, related_name="wallet", on_delete=models.PROTECT)
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} - {self.amount}"

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Wallet"
        verbose_name_plural = "Wallets"
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
        ]


class WalletOperationalLog(models.Model):
    transaction_id = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    previous_amount = models.DecimalField(max_digits=10, decimal_places=2)
    exchange_rate = models.DecimalField(
        max_digits=10, decimal_places=4, default=Decimal("0.00")
    )
    exchange_rate_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    wallet = models.ForeignKey(
        Wallet, related_name="operational_logs", on_delete=models.PROTECT
    )
    currency = models.ForeignKey(
        Currency,
        related_name="operational_logs",
        on_delete=models.PROTECT,
    )
    charge_for = models.ForeignKey(
        User,
        related_name="operational_logs",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.transaction_id

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Wallet Operational Log"
        verbose_name_plural = "Wallet Operational Logs"
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["wallet", "-created_at"]),
        ]


class TransactionLog(models.Model):
    """_summary_

    Args:
        models (_type_): _description_
    """

    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    payment_status = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    description = models.TextField(blank=True, null=True)
    charge_for = models.ForeignKey(
        User,
        related_name="transaction_logs",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.transaction_id

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Transaction Log"
        verbose_name_plural = "Transaction Logs"
        ordering = ["-id"]


class PaymentMethod(models.Model):
    name = models.CharField(max_length=100)
    code_name = models.CharField(max_length=20, blank=True, null=True)
    use_in_pos = models.BooleanField(default=False)
    use_in_store = models.BooleanField(default=False)
    logo_payment_method = models.ImageField(
        upload_to="payment_methods/pics",
        default="payment_methods/payment_method_default.png",
        blank=True,
        null=True,
    )
    currency = models.ForeignKey(
        Currency,
        related_name="payment_methods",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta(PermissionsMeta.Meta):
        permissions = [("manage_payment_methods", _("Can manage payment methods"))]
        ordering = ["name"]

    def __str__(self):
        return self.name


class Payment(models.Model):
    class PaymentStatus(models.TextChoices):
        Pending = 'pending', 'Pending'
        Completed = 'completed', 'Completed'
        Failed = 'failed', 'Failed'
        Refunded = 'refunded', 'Refunded'

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payment")
    payment_method = models.ForeignKey(
        PaymentMethod, related_name="payments", on_delete=models.PROTECT
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    ecommerce_commission_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    ecommerce_commission_applied = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    ecommerce_commission_percentage = models.BooleanField(default=True)
    currency = models.ForeignKey(
        Currency, on_delete=models.PROTECT, related_name="payments"
    )
    exchange_rate = models.DecimalField(
        max_digits=10, decimal_places=4, default=Decimal("0.00")
    )
    exchange_rate_date = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=25, choices=PaymentStatus.choices, default="pending")
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    data = models.JSONField(blank=True, null=True, default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta(PermissionsMeta.Meta):
        permissions = [("manage_payments", _("Can manage payments"))]
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["order", "-created_at"]),
        ]

    def __str__(self):
        return f"Payment {self.order} - {self.payment_method} - {self.amount}"
