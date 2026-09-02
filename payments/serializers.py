import json
from decimal import Decimal

from rest_framework import serializers

from core import serializers as core_serializers
from core.models import Order, Currency, Config
from core.serializers import OrderMinimalSerializer
from payments.models import (
    Wallet,
    TransactionLog,
    Payment,
    PaymentMethod,
    WalletOperationalLog,
)
from user.models import User
from user.serializers import UserSerializer


class WalletSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    user_id = serializers.PrimaryKeyRelatedField(
        required=True,
        queryset=User.objects.all(),
        source="user",
    )

    class Meta:
        model = Wallet
        fields = ["id", "user_id", "amount", "created_at", "updated_at"]


class DepositSerializer(serializers.Serializer):
    user_id = serializers.PrimaryKeyRelatedField(
        allow_null=False,
        required=True,
        queryset=User.objects.filter(is_staff=False, is_active=True),
    )
    currency_id = serializers.PrimaryKeyRelatedField(
        allow_null=False,
        required=True,
        queryset=Currency.objects.all(),
    )
    amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0.01")
    )
    description = serializers.CharField(
        max_length=255, required=False, allow_blank=True, allow_null=True
    )


class WithdrawalSerializer(serializers.Serializer):
    user_id = serializers.PrimaryKeyRelatedField(
        allow_null=False,
        required=True,
        queryset=User.objects.filter(is_staff=False, is_active=True),
    )
    currency_id = serializers.PrimaryKeyRelatedField(
        allow_null=False,
        required=True,
        queryset=Currency.objects.all(),
    )
    amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0.01")
    )
    description = serializers.CharField(
        max_length=255, required=False, allow_blank=True, allow_null=True
    )


class PaymentReportSerializer(serializers.Serializer):
    start_date = serializers.DateField(required=True, allow_null=False)
    end_date = serializers.DateField(required=True, allow_null=False)
    payment_method_id = serializers.PrimaryKeyRelatedField(
        allow_null=True,
        required=False,
        queryset=PaymentMethod.objects.all(),
    )


class WalletOperationalLogSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    currency = core_serializers.CurrencySerializer()
    charge_for = UserSerializer()

    class Meta:
        model = WalletOperationalLog
        fields = "__all__"


class TransactionLogSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    charge_for = UserSerializer()

    class Meta:
        model = TransactionLog
        fields = [
            "id",
            "transaction_id",
            "payment_status",
            "created_at",
            "updated_at",
            "description",
            "charge_for",
            "charge_for_id",
        ]


class PaymentMethodSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    logo_payment_method = serializers.ImageField(read_only=True)
    logo_payment_method_file = serializers.ImageField(
        write_only=True, source="logo_payment_method", required=False
    )
    currency = core_serializers.CurrencySerializer(read_only=True)
    currency_id = serializers.PrimaryKeyRelatedField(
        required=True,
        queryset=Currency.objects.all(),
        source="currency",
    )

    class Meta:
        model = PaymentMethod
        fields = serializers.ALL_FIELDS


class PaymentSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    order_id = serializers.PrimaryKeyRelatedField(
        required=True,
        queryset=Order.objects.all(),
        source="order",
    )
    payment_method = PaymentMethodSerializer(read_only=True)
    payment_method_id = serializers.PrimaryKeyRelatedField(
        required=True,
        queryset=PaymentMethod.objects.all(),
        source="payment_method",
    )
    currency = core_serializers.CurrencySerializer(read_only=True)
    currency_id = serializers.PrimaryKeyRelatedField(
        required=True,
        queryset=Currency.objects.all(),
        source="currency",
    )

    class Meta:
        model = Payment
        fields = [
            "id",
            "order_id",
            "payment_method",
            "payment_method_id",
            "currency",
            "currency_id",
            "exchange_rate",
            "exchange_rate_date",
            "amount",
            "ecommerce_commission_amount",
            "ecommerce_commission_applied",
            "ecommerce_commission_percentage",
            "status",
            "transaction_id",
            "description",
            "created_at",
            "updated_at",
        ]


class TransfermovilPaymentSerializer(serializers.ModelSerializer):
    total_amount = serializers.SerializerMethodField(read_only=True)
    qr_code = serializers.SerializerMethodField(read_only=True)
    tm_link = serializers.SerializerMethodField(read_only=True)

    order_id = serializers.PrimaryKeyRelatedField(
        queryset=Order.objects.all(), source="order"
    )
    payment_method = PaymentMethodSerializer(read_only=True)
    currency = core_serializers.CurrencySerializer(read_only=True)

    def get_total_amount(self, obj) -> str:
        return str((obj.amount * obj.exchange_rate).quantize(Decimal("0.01")))

    def get_qr_code(self, obj) -> str:
        qr_code = dict(
            id_transaccion=obj.order_id,
            importe=self.get_total_amount(obj),
            moneda=obj.currency.initials,
            numero_proveedor=Config.objects.first().transfermovil_source,
            version="1.0",
        )
        return json.dumps(qr_code, sort_keys=True)

    def get_tm_link(self, obj) -> str:
        proveedor = Config.objects.first().transfermovil_source
        return f"transfermovil://tm_compra_en_linea/action?id_transaccion={obj.order_id}&importe={self.get_total_amount(obj)}&moneda={obj.currency.initials}&numero_proveedor={proveedor}"

    class Meta:
        model = Payment
        fields = [
            "id",
            "order_id",
            "payment_method",
            "currency",
            "total_amount",
            "status",
            "qr_code",
            "tm_link",
        ]


class ConciliationPaymentSerializer(PaymentSerializer):
    order = OrderMinimalSerializer(read_only=True)

    class Meta(PaymentSerializer.Meta):
        fields = PaymentSerializer.Meta.fields + ["order"]
