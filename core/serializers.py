from decimal import Decimal
from math import ceil

import pandas as pd
from django.db import transaction
from django.db.models import Avg, Count
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from cms.models import Composer, ContentType, BlockMEDIA
from cms.serializers import (
    BlockMEDIASerializer,
    blocks_process,
    get_any_blocks,
)
from core import models
from core.services import NotificationService
from delivery.models import ShippingRate
from payments.models import Payment, PaymentMethod
from promotions.models import Coupon
from user.models import User
from user.serializers import UserSerializer, UserMinimalSerializer


class BatchSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    class Meta:
        model = models.Batch
        fields = "__all__"


class BatchItemSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """
    batch_id = serializers.PrimaryKeyRelatedField(
        queryset=models.Batch.objects.all(),
        required=True,
        source="batch",
    )
    product_name = serializers.SerializerMethodField()
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=models.Product.objects.all(),
        source="product",
    )
    total_amount = serializers.SerializerMethodField()
    commercial_margin = serializers.SerializerMethodField()
    unit_profit = serializers.SerializerMethodField()
    total_profit = serializers.SerializerMethodField()
    real_profit = serializers.SerializerMethodField()
    break_event_point = serializers.SerializerMethodField()

    class Meta:
        model = models.BatchItem
        fields = [
            "id",
            "product_name",
            "quantity",
            "quantity_sold",
            "amount_sold",
            "cost_price",
            "sale_price",
            "sold",
            "batch_id",
            "product_id",
            "total_amount",
            "commercial_margin",
            "unit_profit",
            "total_profit",
            "real_profit",
            "break_event_point",
        ]

    def get_product_name(self, obj):
        return obj.product.name

    def get_total_amount(self, obj) -> Decimal:
        return obj.quantity * obj.sale_price

    def get_commercial_margin(self, obj) -> Decimal:
        if obj.sale_price == 0:
            return Decimal("0.00")
        return (obj.sale_price - obj.cost_price) / obj.sale_price

    def get_unit_profit(self, obj) -> Decimal:
        return obj.sale_price - obj.cost_price

    def get_total_profit(self, obj) -> Decimal:
        return obj.quantity * self.get_unit_profit(obj)

    def get_real_profit(self, obj) -> Decimal:
        profit = obj.amount_sold - (obj.cost_price * obj.quantity)
        if profit < 0:
            return Decimal("0.00")
        return profit

    def get_break_event_point(self, obj):
        if obj.sale_price == 0:
            return None
        return ceil(abs(obj.cost_price / obj.sale_price) * obj.quantity)


class BatchImportSerializer(serializers.Serializer):
    batch_items_file = serializers.FileField()

    def validate_batch_items_file(self, value):
        if not value.name.endswith(".xlsx"):
            raise serializers.ValidationError(
                _("The file must be an Excel file (.xlsx)")
            )
        df = pd.read_excel(value)
        required_columns = [
            "Código / No. de Parte",
            "Nombre del Producto",
            "Cantidad",
            "Precio Costo USD",
        ]
        columns_df = df.columns.tolist()
        for column in required_columns:
            if column not in columns_df:
                raise serializers.ValidationError(
                    _("Required column not found in the Excel file")
                )

        rows = []
        for index, row in df.iterrows():
            rows.append(
                {
                    "part_code": str(row["Código / No. de Parte"]),
                    "name": str(row["Nombre del Producto"]),
                    "quantity": int(row["Cantidad"]),
                    "cost_price": Decimal(row["Precio Costo USD"]),
                }
            )

        return rows


class BatchSalesReportSerializer(serializers.Serializer):
    batch_id = serializers.IntegerField()
    batch_identificator = serializers.CharField()
    received_date = serializers.DateField()
    exchange_rate = serializers.DecimalField(max_digits=10, decimal_places=2)
    invoice_number = serializers.CharField()
    part_code = serializers.CharField()
    product_name = serializers.CharField()
    product_id = serializers.IntegerField(allow_null=True)
    cost_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    sale_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_quantity = serializers.DecimalField(max_digits=10, decimal_places=2)
    sold_quantity = serializers.DecimalField(max_digits=10, decimal_places=2)
    remaining_quantity = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_cost = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_profit = serializers.DecimalField(max_digits=10, decimal_places=2)
    profit_margin_percentage = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_orders = serializers.IntegerField()
    average_selling_price = serializers.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        fields = "__all__"


class CurrencySerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    class Meta:
        model = models.Currency
        fields = "__all__"

    def create(self, validated_data):
        currency = models.Currency(**validated_data)
        if currency.default:
            models.Currency.objects.all().update(default=False)
        currency.save()
        return currency

    def update(self, instance, validated_data):
        instance = super(CurrencySerializer, self).update(instance, validated_data)
        if instance.default:
            models.Currency.objects.all().exclude(id=instance.id).update(default=False)
        return instance


class NotificationTypeSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    class Meta:
        model = models.NotificationType
        fields = "__all__"


class VehicleTypeSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    class Meta:
        model = models.VehicleType
        fields = "__all__"


class VehicleSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    vehicle_type = VehicleTypeSerializer(read_only=True)
    vehicle_type_id = serializers.PrimaryKeyRelatedField(
        queryset=models.VehicleType.objects.all(),
        required=True,
        source="vehicle_type",
    )
    driver = UserSerializer(read_only=True)
    driver_id = serializers.PrimaryKeyRelatedField(
        queryset=models.User.objects.all(),
        source="driver",
        required=True,
    )

    class Meta:
        model = models.Vehicle
        fields = [
            "id",
            "plate",
            "avg_fuel_consumption",
            "vehicle_type",
            "vehicle_type_id",
            "driver",
            "driver_id",
            "active",
        ]


class VehicleLocationSerializer(serializers.ModelSerializer):
    vehicle = VehicleSerializer()
    driver = UserMinimalSerializer()

    class Meta:
        model = models.VehicleLocation
        fields = serializers.ALL_FIELDS


class NotificationUserSerializer(serializers.ModelSerializer):

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["title"] = instance.notification.title
        representation["message"] = instance.notification.message
        representation["notification_type"] = (
            instance.notification.notification_type.name
        )
        representation["icon"] = instance.notification.notification_type.icon
        representation["color"] = instance.notification.notification_type.color
        representation["created_date"] = instance.notification.sent_date

        return representation

    class Meta:
        model = models.NotificationUser
        fields = "__all__"


class NotificationSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    notification_type = NotificationTypeSerializer(read_only=True)
    notification_type_id = serializers.PrimaryKeyRelatedField(
        allow_null=True,
        required=False,
        queryset=models.NotificationType.objects.all(),
        source="notification_type",
    )
    users_type = serializers.CharField(write_only=True, required=False, allow_null=True)
    users_id = serializers.ListField(write_only=True, required=False)
    users = serializers.SerializerMethodField()

    def get_users(self, obj) -> list:
        notification_users = models.NotificationUser.objects.filter(notification=obj)
        user_list = []
        for notification_user in notification_users:
            user = notification_user.user
            full_name = f"{user.first_name} {user.last_name}"
            user_list.append({"id": user.id, "name": full_name})
        return user_list

    class Meta:
        model = models.Notification
        fields = [
            "title",
            "message",
            "sent_date",
            "notification_type",
            "notification_type_id",
            "users",
            "users_id",
            "users_type",
        ]

    def create(self, validated_data):
        with transaction.atomic():
            users_id = validated_data.pop("users_id", [])
            users_type = validated_data.pop("users_type", None)
            user_filters = {"is_active": True}
            if users_type == "only_clients":
                user_filters["is_staff"] = False
            elif users_type == "only_staffs":
                user_filters["is_staff"] = True
            elif users_type is None:
                user_filters["id__in"] = users_id
            users = User.objects.filter(**user_filters)
            notification = models.Notification.objects.create(**validated_data)
            models.NotificationUser.objects.bulk_create(
                [
                    models.NotificationUser(user=user, notification=notification)
                    for user in users
                ]
            )
            title = validated_data.pop("title", None)
            message = validated_data.pop("message", None)
            notification_type = validated_data.pop("notification_type", None)
            if users.exists():
                NotificationService.send_notification(
                    title,
                    message,
                    users,
                    notification_type.name,
                    ["WHATSAPP"],
                )
            return notification

    def update(self, instance, validated_data):
        with transaction.atomic():
            users_id = validated_data.pop("users_id", [])
            users_type = validated_data.pop("users_type", None)
            user_filters = {"is_active": True}
            if users_type == "only_clients":
                user_filters["is_staff"] = False
            elif users_type == "only_staffs":
                user_filters["is_staff"] = True
            if users_id:
                user_filters["id__in"] = users_id
            users = User.objects.filter(**user_filters)
            instance = super(NotificationSerializer, self).update(
                instance, validated_data
            )
            models.NotificationUser.objects.filter(notification=instance).delete()
            models.NotificationUser.objects.bulk_create(
                [
                    models.NotificationUser(user=user, notification=instance)
                    for user in users
                ]
            )
            title = validated_data.pop("title", None)
            message = validated_data.pop("message", None)
            notification_type = validated_data.pop("notification_type", None)
            if users.exists():
                NotificationService.send_notification(
                    title,
                    message,
                    users,
                    notification_type.name,
                    ["WHATSAPP"],
                )
            return instance


class CountrySerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    country_flag = serializers.ImageField(read_only=True)
    country_flag_file = serializers.ImageField(
        write_only=True, source="country_flag", required=False
    )

    class Meta:
        model = models.Country
        fields = [
            "id",
            "name",
            "code_alpha3",
            "country_flag",
            "country_flag_file",
            "active",
        ]


class ProviderSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    class Meta:
        model = models.Provider
        fields = "__all__"


class BrandSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    logo_brand = serializers.ImageField(read_only=True)
    logo_brand_file = serializers.ImageField(
        write_only=True, source="logo_brand", required=False
    )

    class Meta:
        model = models.Brand
        fields = [
            "id",
            "name",
            "description",
            "parent",
            "logo_brand",
            "logo_brand_file",
            "active",
        ]


class CategorySerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    category_image = serializers.ImageField(read_only=True)
    category_image_file = serializers.ImageField(
        write_only=True, source="category_image", required=False
    )

    class Meta:
        model = models.Category
        fields = [
            "id",
            "name",
            "category_image",
            "category_image_file",
            "active",
            "parent",
        ]


class MeasurementUnitSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    class Meta:
        model = models.Measurement_Unit
        fields = "__all__"


class OrderStatusSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    class Meta:
        model = models.OrderStatus
        fields = "__all__"


class OrderTrackingSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    status = OrderStatusSerializer(read_only=True)
    status_id = serializers.PrimaryKeyRelatedField(
        allow_null=False,
        required=True,
        queryset=models.OrderStatus.objects.all(),
        source="status",
    )

    class Meta:
        model = models.OrderTracking
        fields = [
            "id",
            "order_tracking_date",
            "observations",
            "order_id",
            "status",
            "status_id",
        ]


class CreditTypeSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    class Meta:
        model = models.CreditType
        fields = "__all__"


class ProvinceSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    class Meta:
        model = models.Province
        fields = "__all__"


class MunicipalitySerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    province = ProvinceSerializer(read_only=True)
    province_id = serializers.PrimaryKeyRelatedField(
        allow_null=False,
        required=True,
        queryset=models.Province.objects.all(),
        source="province",
    )

    class Meta:
        model = models.Municipality
        fields = ["id", "name", "province", "province_id"]


class ContactAddressSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    user_id = serializers.PrimaryKeyRelatedField(
        allow_null=False,
        required=False,
        write_only=True,
        source="user",
        queryset=models.User.objects.filter(is_staff=False).all(),
    )
    municipality = MunicipalitySerializer(read_only=True)
    municipality_id = serializers.PrimaryKeyRelatedField(
        allow_null=False,
        required=True,
        queryset=models.Municipality.objects.all(),
        source="municipality",
    )
    province_id = serializers.SerializerMethodField()
    province = serializers.SerializerMethodField()

    class Meta:
        model = models.ContactAddress
        fields = [
            "id",
            "address",
            "reference",
            "default",
            "municipality",
            "municipality_id",
            "province",
            "province_id",
            "user_id",
        ]

    def get_province_id(self, obj) -> int:
        return obj.municipality.province.id

    def get_province(self, obj) -> str:
        return ProvinceSerializer(obj.municipality.province).data

    def create(self, validated_data):
        with transaction.atomic():
            user = validated_data.get("user", self.context.get("request").user)
            address = validated_data["address"]
            default = validated_data["default"]
            municipality = validated_data["municipality"]

            if default:
                contact_addresses = models.ContactAddress.objects.filter(user=user)
                if contact_addresses.exists():
                    contact_addresses.update(default=False)

            contact_address = models.ContactAddress.objects.create(
                address=address, default=default, municipality=municipality, user=user
            )
            return contact_address

    def update(self, instance, validated_data):
        with transaction.atomic():
            instance = super(ContactAddressSerializer, self).update(
                instance, validated_data
            )

            if instance.default:
                models.ContactAddress.objects.filter(user=instance.user).exclude(
                    id=instance.id
                ).update(default=False)

            return instance


def order_gross_weight(order_products: list[models.OrderProducts]) -> Decimal:
    total_order_gross_weight = sum(
        [
            order_product.quantity * order_product.product.gross_weight
            for order_product in order_products
        ]
    )
    return Decimal(total_order_gross_weight)


def order_net_weight(order_products: list[models.OrderProducts]) -> Decimal:
    total_order_net_weight = sum(
        [
            order_product.quantity * order_product.product.net_weight
            for order_product in order_products
        ]
    )
    return Decimal(total_order_net_weight)


class OrderMinimalSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    client = UserSerializer(read_only=True)
    credit_type = CreditTypeSerializer(read_only=True)
    total_gross_weight = serializers.SerializerMethodField()
    total_net_weight = serializers.SerializerMethodField()
    current_status = serializers.SerializerMethodField()
    total_products = serializers.SerializerMethodField()
    shipping = serializers.SerializerMethodField()

    class Meta:
        model = models.Order
        fields = [
            "id",
            "creation_date",
            "expiration_date",
            "amount",
            "credit_amount",
            "total_discount",
            "pending_amount",
            "payment_deadline",
            "total_amount",
            "total_gross_weight",
            "total_net_weight",
            "client",
            "credit_type",
            "current_status",
            "total_products",
            "shipping",
        ]

    def get_shipping(self, obj) -> dict | None:
        from delivery.serializers import OrderShippingSerializer

        if hasattr(obj, "shipping"):
            return OrderShippingSerializer(obj.shipping).data
        return None

    def get_total_products(self, obj) -> int:
        return models.OrderProducts.objects.filter(order=obj).count()

    def get_current_status(self, obj) -> dict | None:
        return OrderTrackingSerializer(obj.current_status).data

    def get_total_gross_weight(self, obj) -> Decimal:
        order_products = models.OrderProducts.objects.filter(order=obj)
        if order_products.exists():
            return order_gross_weight(order_products)
        return Decimal("0.00")

    def get_total_net_weight(self, obj) -> Decimal:
        order_products = models.OrderProducts.objects.filter(order=obj)
        if order_products.exists():
            return order_net_weight(order_products)
        return Decimal("0.00")


class OrderSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    client = UserSerializer(read_only=True)
    client_id = serializers.PrimaryKeyRelatedField(
        required=False,
        queryset=models.User.objects.all(),
        source="client",
    )
    credit_type = CreditTypeSerializer(read_only=True)
    credit_type_id = serializers.PrimaryKeyRelatedField(
        required=False,
        allow_null=True,
        queryset=models.CreditType.objects.all(),
        source="credit_type",
    )
    seller = UserSerializer(read_only=True)
    payments = serializers.SerializerMethodField()
    shipping = serializers.SerializerMethodField()
    order_products = serializers.SerializerMethodField()
    order_statuses = serializers.SerializerMethodField()
    total_gross_weight = serializers.SerializerMethodField()
    total_net_weight = serializers.SerializerMethodField()
    current_status = serializers.SerializerMethodField()
    merged = serializers.SerializerMethodField()

    class Meta:
        model = models.Order
        fields = [
            "id",
            "creation_date",
            "expiration_date",
            "amount",
            "credit_amount",
            "total_discount",
            "pending_amount",
            "payment_deadline",
            "total_amount",
            "total_gross_weight",
            "total_net_weight",
            "observations",
            "percentual_fee",
            "fixed_fee",
            "client",
            "client_id",
            "credit_type",
            "credit_type_id",
            "seller",
            "merged",
            "current_status",
            "order_products",
            "order_statuses",
            "payments",
            "shipping",
        ]

    def get_payments(self, obj) -> dict:
        from payments.serializers import PaymentSerializer

        payments = Payment.objects.filter(order=obj)
        return PaymentSerializer(
            payments, many=True, context={"request": self.context.get("request")}
        ).data

    def get_shipping(self, obj) -> dict | None:
        from delivery.serializers import OrderShippingSerializer

        if hasattr(obj, "shipping"):
            return OrderShippingSerializer(obj.shipping).data
        return None

    def get_order_products(self, obj) -> dict | None:
        order_products = models.OrderProducts.objects.filter(order=obj)
        if order_products.exists():
            return OrderProductsSerializer(
                order_products,
                many=True,
                context={"request": self.context.get("request")},
            ).data
        return None

    def get_order_statuses(self, obj) -> dict | None:
        order_statuses = models.OrderTracking.objects.filter(order=obj).order_by("id")
        if order_statuses.exists():
            return OrderTrackingSerializer(order_statuses, many=True).data
        return None

    def get_current_status(self, obj) -> dict | None:
        return OrderTrackingSerializer(obj.current_status).data

    def get_total_gross_weight(self, obj) -> Decimal:
        order_products = models.OrderProducts.objects.filter(order=obj)
        if order_products.exists():
            return order_gross_weight(order_products)
        return Decimal("0.00")

    def get_total_net_weight(self, obj) -> Decimal:
        order_products = models.OrderProducts.objects.filter(order=obj)
        if order_products.exists():
            return order_net_weight(order_products)
        return Decimal("0.00")

    def get_merged(self, obj) -> bool:
        return models.Order.objects.filter(merge=obj.id).exists()


class OrderAddPaymentSerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, min_value=Decimal("0.01")
    )
    payment_method_id = serializers.PrimaryKeyRelatedField(
        allow_null=False,
        required=True,
        queryset=PaymentMethod.objects.filter(active=True, use_in_pos=True),
    )
    paid = serializers.BooleanField(required=True, allow_null=False)


class ReviewSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        required=True,
        queryset=models.User.objects.all(),
        source="user",
    )
    product_id = serializers.PrimaryKeyRelatedField(
        required=True,
        queryset=models.Product.objects.all(),
        source="product",
    )

    class Meta:
        model = models.Review
        fields = ["comment", "rating", "review_date", "product_id", "user", "user_id"]


class SpecificationsSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    class Meta:
        model = models.Specifications
        fields = "__all__"


class SpecificationDetailsSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    specification = SpecificationsSerializer(read_only=True)
    specification_id = serializers.PrimaryKeyRelatedField(
        allow_null=True,
        required=False,
        queryset=models.Specifications.objects.all(),
        source="specification",
    )

    class Meta:
        model = models.SpecificationDetails
        fields = [
            "id",
            "value",
            "specification",
            "specification_id",
        ]


class ProductWriteSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    product_images = BlockMEDIASerializer(many=True, read_only=True)
    product_images_ids = serializers.PrimaryKeyRelatedField(
        required=False,
        many=True,
        queryset=BlockMEDIA.objects.all(),
        write_only=True,
        source="product_images",
    )
    country = CountrySerializer(read_only=True)
    brand = BrandSerializer(read_only=True)
    provider = ProviderSerializer(read_only=True)
    measurement_unit = MeasurementUnitSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    specifications_details = SpecificationDetailsSerializer(write_only=True, many=True)
    country_id = serializers.PrimaryKeyRelatedField(
        allow_null=True,
        required=False,
        queryset=models.Country.objects.filter(active=True),
        source="country",
    )
    brand_id = serializers.PrimaryKeyRelatedField(
        allow_null=True,
        required=False,
        queryset=models.Brand.objects.filter(active=True),
        source="brand",
    )
    provider_id = serializers.PrimaryKeyRelatedField(
        allow_null=True,
        required=False,
        queryset=models.Provider.objects.filter(active=True),
        source="provider",
    )
    measurement_unit_id = serializers.PrimaryKeyRelatedField(
        allow_null=True,
        required=False,
        queryset=models.Measurement_Unit.objects.filter(active=True),
        source="measurement_unit",
    )
    category_id = serializers.PrimaryKeyRelatedField(
        allow_null=True,
        required=False,
        queryset=models.Category.objects.filter(active=True),
        source="category",
    )
    slug = serializers.SlugField(required=False, allow_blank=True)
    net_weight = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, default=Decimal("0.00")
    )
    gross_weight = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, default=Decimal("0.00")
    )
    daily_variation = serializers.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00"), read_only=True
    )
    wholesale_minimum = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    wholesale_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    price_per_box = serializers.SerializerMethodField()
    reviews = serializers.SerializerMethodField()
    blocks = serializers.ListField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = models.Product
        fields = [
            "id",
            "code_sku",
            "part_code",
            "name",
            "slug",
            "product_images",
            "country",
            "brand",
            "provider",
            "measurement_unit",
            "category",
            "specifications_details",
            "product_images_ids",
            "country_id",
            "brand_id",
            "provider_id",
            "measurement_unit_id",
            "category_id",
            "quantity",
            "net_content",
            "price_per_box",
            "cost_price",
            "unit_price",
            "wholesale_price",
            "has_wholesale_price",
            "wholesale_minimum",
            "net_weight",
            "gross_weight",
            "quantity_per_box",
            "daily_variation",
            "minimal_stock",
            "description",
            "on_offer",
            "use_custom_template",
            "active",
            "reviews",
            "blocks",
        ]

    def get_reviews(self, obj) -> dict:
        reviews = models.Review.objects.filter(product=obj).aggregate(
            total=Count("id"), rating_avg=Avg("rating")
        )
        return reviews

    def get_price_per_box(self, obj) -> Decimal:
        request = self.context.get("request")
        if not request:
            return obj.quantity_per_box * obj.unit_price
        user = request.user
        if user.is_authenticated:
            return obj.quantity_per_box * obj.sell_price(user.fee)
        return obj.quantity_per_box * obj.unit_price

    def validate(self, attrs):
        attrs = super().validate(attrs)

        has_wholesale_price = attrs.get("has_wholesale_price")
        wholesale_price = attrs.get("wholesale_price")
        wholesale_minimum = attrs.get("wholesale_minimum")

        errors = {}

        if has_wholesale_price and not wholesale_price:
            errors["wholesale_price"] = [_("There must be a wholesale price.")]
        if has_wholesale_price and not wholesale_minimum:
            errors["wholesale_minimum"] = [
                _("There must be a minimum wholesale quantity.")
            ]

        if errors:
            raise serializers.ValidationError(errors)

        return attrs

    def create(self, validated_data):
        with transaction.atomic():
            product_images = validated_data.pop("product_images", None)
            details = validated_data.pop("specifications_details", None)
            validated_data["slug"] = slugify(validated_data["name"])
            blocks = validated_data.pop("blocks", None)
            product = models.Product.objects.create(**validated_data)
            if details:
                for detail in details:
                    models.SpecificationDetails.objects.create(
                        product=product,
                        specification=detail["specification"],
                        value=detail["value"],
                    )
            # product.product_images.set(product_images)
            if product_images:
                all_medias = []
                for media in product_images:
                    all_medias.append(
                        models.ProductImageOrder(product=product, blockmedia=media)
                    )
                models.ProductImageOrder.objects.bulk_create(all_medias)
            if blocks:
                blocks_process(blocks, product)
            return product

    def update(self, instance, validated_data):
        with transaction.atomic():
            details = validated_data.pop("specifications_details", None)
            product_images = validated_data.pop("product_images", None)
            validated_data["slug"] = slugify(validated_data["name"])
            blocks = validated_data.pop("blocks", None)
            instance.daily_variation = (
                    validated_data.get("unit_price") - instance.unit_price
            )
            instance = super().update(instance, validated_data)
            if details:
                models.SpecificationDetails.objects.filter(product=instance).delete()
                for detail in details:
                    models.SpecificationDetails.objects.create(
                        product=instance,
                        specification=detail["specification"],
                        value=detail["value"],
                    )
            # instance.product_images.set(product_images)
            models.ProductImageOrder.objects.filter(product=instance).delete()
            if product_images:
                all_medias = []
                for media in product_images:
                    all_medias.append(
                        models.ProductImageOrder(product=instance, blockmedia=media)
                    )
                models.ProductImageOrder.objects.bulk_create(all_medias)
            Composer.objects.filter(
                local_id=instance.id,
                local_content_type=ContentType.objects.get(model="product"),
            ).delete()
            if blocks:
                blocks_process(blocks, instance)
            return instance


class ProductReadSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    product_images = BlockMEDIASerializer(
        read_only=True, many=True, source="ordered_product_images"
    )
    country = CountrySerializer(read_only=True)
    brand = BrandSerializer(read_only=True)
    provider = ProviderSerializer(read_only=True)
    measurement_unit = MeasurementUnitSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    specifications_details = SpecificationDetailsSerializer(read_only=True, many=True)
    product_images_ids = serializers.PrimaryKeyRelatedField(
        required=False,
        allow_null=True,
        many=True,
        queryset=BlockMEDIA.objects.all(),
        source="product_images",
    )
    country_id = serializers.PrimaryKeyRelatedField(
        allow_null=True,
        required=False,
        queryset=models.Country.objects.filter(active=True),
        source="country",
    )
    brand_id = serializers.PrimaryKeyRelatedField(
        allow_null=True,
        required=False,
        queryset=models.Brand.objects.filter(active=True),
        source="brand",
    )
    provider_id = serializers.PrimaryKeyRelatedField(
        allow_null=True,
        required=False,
        queryset=models.Provider.objects.filter(active=True),
        source="provider",
    )
    measurement_unit_id = serializers.PrimaryKeyRelatedField(
        allow_null=True,
        required=False,
        queryset=models.Measurement_Unit.objects.filter(active=True),
        source="measurement_unit",
    )
    category_id = serializers.PrimaryKeyRelatedField(
        allow_null=True,
        required=False,
        queryset=models.Category.objects.filter(active=True),
        source="category",
    )
    specifications_details_ids = serializers.PrimaryKeyRelatedField(
        required=False,
        many=True,
        queryset=models.SpecificationDetails.objects.all(),
        source="specifications",
    )
    price_per_box = serializers.SerializerMethodField()
    reviews = serializers.SerializerMethodField()
    blocks = serializers.SerializerMethodField()
    unit_price = serializers.SerializerMethodField()
    wholesale_price = serializers.SerializerMethodField()
    daily_variation = serializers.SerializerMethodField()

    class Meta:
        model = models.Product
        fields = [
            "id",
            "code_sku",
            "part_code",
            "name",
            "slug",
            "product_images",
            "country",
            "brand",
            "provider",
            "measurement_unit",
            "category",
            "specifications_details",
            "product_images_ids",
            "country_id",
            "brand_id",
            "provider_id",
            "measurement_unit_id",
            "specifications_details_ids",
            "category_id",
            "quantity",
            "net_content",
            "price_per_box",
            "cost_price",
            "unit_price",
            "wholesale_price",
            "has_wholesale_price",
            "wholesale_minimum",
            "net_weight",
            "gross_weight",
            "quantity_per_box",
            "daily_variation",
            "minimal_stock",
            "description",
            "on_offer",
            "use_custom_template",
            "active",
            "reviews",
            "blocks",
        ]

    def get_reviews(self, obj) -> dict:
        reviews = models.Review.objects.filter(product=obj).aggregate(
            total=Count("id"), rating_avg=Avg("rating")
        )
        return reviews

    def get_unit_price(self, obj) -> Decimal:
        request = self.context.get("request")
        if not request:
            return Decimal("0.00")
        user = request.user
        if user.is_authenticated:
            return obj.sell_price(user.fee)
        return Decimal("0.00")

    def get_wholesale_price(self, obj) -> Decimal:
        request = self.context.get("request")
        if not request:
            return Decimal("0.00")
        user = request.user
        if user.is_authenticated:
            return obj.sell_wholesale_price(user.fee)
        return Decimal("0.00")

    def get_daily_variation(self, obj) -> Decimal:
        request = self.context.get("request")
        if not request:
            return Decimal("0.00")
        user = request.user
        if user.is_authenticated:
            fee = user.fee
            return obj.daily_variation * (1 + fee.percentual_fee if fee else 0)
        return Decimal("0.00")

    def get_price_per_box(self, obj) -> Decimal:
        request = self.context.get("request")
        if not request:
            return obj.quantity_per_box * obj.unit_price
        user = request.user
        if user.is_authenticated:
            return obj.quantity_per_box * obj.sell_price(user.fee)
        return obj.quantity_per_box * obj.unit_price

    def get_blocks(self, obj) -> list:
        return get_any_blocks(
            obj, "product", context={"request": self.context.get("request")}
        )


class ProductReadMinimalSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    product_images = BlockMEDIASerializer(
        read_only=True, many=True, source="ordered_product_images"
    )
    country = CountrySerializer(read_only=True)
    brand = BrandSerializer(read_only=True)
    provider = ProviderSerializer(read_only=True)
    measurement_unit = MeasurementUnitSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    specifications_details = SpecificationDetailsSerializer(read_only=True, many=True)
    product_images_ids = serializers.PrimaryKeyRelatedField(
        required=False,
        allow_null=True,
        many=True,
        queryset=BlockMEDIA.objects.all(),
        source="product_images",
    )
    country_id = serializers.PrimaryKeyRelatedField(
        allow_null=True,
        required=False,
        queryset=models.Country.objects.filter(active=True),
        source="country",
    )
    brand_id = serializers.PrimaryKeyRelatedField(
        allow_null=True,
        required=False,
        queryset=models.Brand.objects.filter(active=True),
        source="brand",
    )
    provider_id = serializers.PrimaryKeyRelatedField(
        allow_null=True,
        required=False,
        queryset=models.Provider.objects.filter(active=True),
        source="provider",
    )
    measurement_unit_id = serializers.PrimaryKeyRelatedField(
        allow_null=True,
        required=False,
        queryset=models.Measurement_Unit.objects.filter(active=True),
        source="measurement_unit",
    )
    category_id = serializers.PrimaryKeyRelatedField(
        allow_null=True,
        required=False,
        queryset=models.Category.objects.filter(active=True),
        source="category",
    )
    specifications_details_ids = serializers.PrimaryKeyRelatedField(
        required=False,
        many=True,
        queryset=models.SpecificationDetails.objects.all(),
        source="specifications",
    )
    price_per_box = serializers.SerializerMethodField()
    unit_price = serializers.SerializerMethodField()
    wholesale_price = serializers.SerializerMethodField()
    daily_variation = serializers.SerializerMethodField()
    reviews = serializers.SerializerMethodField()

    class Meta:
        model = models.Product
        fields = [
            "id",
            "code_sku",
            "part_code",
            "name",
            "slug",
            "product_images",
            "country",
            "brand",
            "provider",
            "measurement_unit",
            "category",
            "specifications_details",
            "product_images_ids",
            "country_id",
            "brand_id",
            "provider_id",
            "measurement_unit_id",
            "specifications_details_ids",
            "category_id",
            "quantity",
            "net_content",
            "price_per_box",
            "cost_price",
            "unit_price",
            "wholesale_price",
            "has_wholesale_price",
            "wholesale_minimum",
            "net_weight",
            "gross_weight",
            "quantity_per_box",
            "daily_variation",
            "minimal_stock",
            "description",
            "on_offer",
            "use_custom_template",
            "active",
            "reviews",
        ]

    def get_reviews(self, obj) -> dict:
        reviews = models.Review.objects.filter(product=obj).aggregate(
            total=Count("id"), rating_avg=Avg("rating")
        )
        return reviews

    def get_unit_price(self, obj) -> Decimal:
        request = self.context.get("request")
        if not request:
            return obj.unit_price
        user = request.user
        if user.is_authenticated:
            return obj.sell_price(user.fee)
        return obj.unit_price

    def get_wholesale_price(self, obj) -> Decimal:
        request = self.context.get("request")
        if not request:
            return Decimal("0.00")
        user = request.user
        if user.is_authenticated:
            return obj.sell_wholesale_price(user.fee)
        return Decimal("0.00")

    def get_daily_variation(self, obj) -> Decimal:
        request = self.context.get("request")
        if not request:
            return Decimal("0.00")
        user = request.user
        if user.is_authenticated:
            fee = user.fee
            return obj.daily_variation * (1 + fee.percentual_fee if fee else 0)
        return Decimal("0.00")

    def get_price_per_box(self, obj) -> Decimal:
        request = self.context.get("request")
        if not request:
            return obj.quantity_per_box * obj.unit_price
        user = request.user
        if user.is_authenticated:
            return obj.quantity_per_box * obj.sell_price(user.fee)
        return obj.quantity_per_box * obj.unit_price


class OrderProfitReportSerializer(serializers.Serializer):
    start_date = serializers.DateField(required=True, allow_null=False)
    end_date = serializers.DateField(required=True, allow_null=False)


class OrderProductsSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    product = ProductReadSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        allow_null=False,
        required=True,
        queryset=models.Product.objects.filter(active=True),
        source="product",
    )
    price = serializers.SerializerMethodField()
    amount = serializers.SerializerMethodField()
    net_weight = serializers.SerializerMethodField()
    gross_weight = serializers.SerializerMethodField()

    class Meta:
        model = models.OrderProducts
        fields = [
            "id",
            "quantity",
            "cost",
            "price",
            "amount",
            "net_weight",
            "gross_weight",
            "product",
            "product_id",
        ]

    def get_price(self, obj) -> Decimal:
        return obj.price * (1 + obj.order.percentual_fee) + obj.order.fixed_fee

    def get_amount(self, obj) -> Decimal:
        return obj.amount

    def get_net_weight(self, obj) -> Decimal:
        return obj.quantity * obj.product.net_weight

    def get_gross_weight(self, obj) -> Decimal:
        return obj.quantity * obj.product.gross_weight


class CartSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    product = ProductReadSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        allow_null=False,
        required=True,
        queryset=models.Product.objects.filter(active=True),
    )
    price = serializers.SerializerMethodField()
    amount = serializers.SerializerMethodField()
    save_amount = serializers.SerializerMethodField()
    weight_net = serializers.SerializerMethodField()
    weight_gross = serializers.SerializerMethodField()

    class Meta:
        model = models.Cart
        fields = [
            "id",
            "quantity",
            "price",
            "amount",
            "save_amount",
            "product",
            "product_id",
            "weight_net",
            "weight_gross",
        ]

    def get_price(self, obj) -> Decimal:
        if (
                obj.product.has_wholesale_price
                and obj.quantity >= obj.product.wholesale_minimum
        ):
            return obj.product.sell_wholesale_price(obj.client.fee)
        return obj.product.sell_price(obj.client.fee)

    def get_amount(self, obj) -> Decimal:
        return obj.quantity * (
            obj.product.sell_wholesale_price(obj.client.fee)
            if obj.product.has_wholesale_price
               and obj.quantity >= obj.product.wholesale_minimum
            else obj.product.sell_price(obj.client.fee)
        )

    def get_save_amount(self, obj) -> Decimal:
        save_amount = Decimal("0.00")
        if (
                obj.product.has_wholesale_price
                and obj.quantity >= obj.product.wholesale_minimum
        ):
            save_amount = obj.quantity * obj.product.sell_price(
                obj.client.fee
            ) - obj.quantity * obj.product.sell_wholesale_price(obj.client.fee)
        return save_amount

    def get_weight_net(self, obj) -> Decimal:
        return obj.quantity * obj.product.net_weight

    def get_weight_gross(self, obj) -> Decimal:
        return obj.quantity * obj.product.gross_weight

    def create(self, validated_data):
        with transaction.atomic():
            client = self.context.get("request").user
            product = validated_data["product_id"]
            quantity = validated_data["quantity"]
            cart_products = models.Cart.objects.filter(
                product_id=product.id, client_id=client.id
            )
            if cart_products.exists():
                cart_products.delete()
            cart_product = models.Cart.objects.create(
                product_id=product.id, client_id=client.id, quantity=quantity
            )
            return cart_product

    def update(self, instance, validated_data):
        with transaction.atomic():
            instance = super(CartSerializer, self).update(instance, validated_data)
            return instance


class CreateOrderSerializer(serializers.Serializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    delivery_address_id = serializers.PrimaryKeyRelatedField(
        allow_null=True,
        required=False,
        queryset=models.ContactAddress.objects.all(),
    )
    shipping_rate_id = serializers.PrimaryKeyRelatedField(
        allow_null=True,
        required=False,
        queryset=ShippingRate.objects.filter(
            active=True, shipping_method__active=True, shipping_zone__active=True
        ),
    )
    payment_method_id = serializers.PrimaryKeyRelatedField(
        allow_null=False,
        required=True,
        queryset=PaymentMethod.objects.filter(active=True, use_in_store=True),
    )
    observations = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, trim_whitespace=True
    )
    coupons_ids = serializers.PrimaryKeyRelatedField(
        allow_null=False,
        many=True,
        required=True,
        queryset=Coupon.objects.filter(active=True),
    )

    def validate(self, attrs):
        attrs = super().validate(attrs)

        errors = {}

        delivery_address = attrs.get("delivery_address_id")
        shipping_rate = attrs.get("shipping_rate_id")

        if shipping_rate and not delivery_address:
            errors["delivery_address_id"] = [
                _("There can be no shipping fee without a delivery address.")
            ]

        if delivery_address and shipping_rate:
            if (
                    delivery_address.municipality
                    not in shipping_rate.shipping_zone.municipalities.all()
            ):
                errors["shipping_rate_id"] = [
                    _(
                        "The shipping address does not belong to the shipping zone of the rate used."
                    )
                ]
        elif delivery_address and not shipping_rate:
            errors["shipping_rate_id"] = [
                _("A shipping rate must be provided for the selected delivery address.")
            ]

        coupons = attrs.get("coupons_ids", [])
        now = timezone.now()
        invalid_coupons = []
        for coupon in coupons:
            if not (coupon.valid_from <= now <= coupon.valid_to):
                invalid_coupons.append(str(coupon.id))
        if invalid_coupons:
            errors["coupons_ids"] = [_("The list contains no valid coupons")]

        if errors:
            raise serializers.ValidationError(errors)

        return attrs


class ConfigSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    business_name = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    business_phone = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    business_address = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    business_email = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    business_schedule = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    business_nit = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    business_licence = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    business_account = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    logo_light = serializers.ImageField(read_only=True)
    logo_light_file = serializers.ImageField(
        write_only=True, source="logo_light", required=False
    )
    logo_dark = serializers.ImageField(read_only=True)
    logo_dark_file = serializers.ImageField(
        write_only=True, source="logo_dark", required=False
    )
    logo_horizontal_light = serializers.ImageField(read_only=True)
    logo_horizontal_light_file = serializers.ImageField(
        write_only=True, source="logo_horizontal_light", required=False
    )
    logo_horizontal_dark = serializers.ImageField(read_only=True)
    logo_horizontal_dark_file = serializers.ImageField(
        write_only=True, source="logo_horizontal_dark", required=False
    )

    admin_logo_horizontal_light = serializers.ImageField(read_only=True)
    admin_logo_horizontal_light_file = serializers.ImageField(
        write_only=True, source="admin_logo_horizontal_light", required=False
    )
    admin_logo_horizontal_dark = serializers.ImageField(read_only=True)
    admin_logo_horizontal_dark_file = serializers.ImageField(
        write_only=True, source="admin_logo_horizontal_dark", required=False
    )

    class Meta:
        model = models.Config
        fields = [
            "business_name",
            "business_phone",
            "business_address",
            "business_email",
            "business_nit",
            "business_account",
            "business_licence",
            "business_schedule",
            "social_networks",
            "logo_light",
            "logo_light_file",
            "logo_dark",
            "logo_dark_file",
            "logo_horizontal_light",
            "logo_horizontal_light_file",
            "logo_horizontal_dark",
            "logo_horizontal_dark_file",
            "admin_logo_horizontal_light",
            "admin_logo_horizontal_light_file",
            "admin_logo_horizontal_dark",
            "admin_logo_horizontal_dark_file",
            "billing_email",
        ]


class OrderProductSaleProfit(serializers.Serializer):
    order_id = serializers.IntegerField()
    client_name = serializers.CharField()
    creation_date = serializers.DateTimeField()
    quantity = serializers.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    sell_price = serializers.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    sale_amount = serializers.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    total_cost = serializers.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    absolute_margin = serializers.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    margin_percentual = serializers.DecimalField(max_digits=10, decimal_places=4, default=Decimal("0.00"))
    profit_per_unit = serializers.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))


class OrderProductProfit(serializers.Serializer):
    product = ProductReadMinimalSerializer()
    quantity = serializers.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    sale_amount = serializers.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    total_cost = serializers.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    absolute_margin = serializers.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    avg_sell_price = serializers.SerializerMethodField()
    avg_profit_per_unit = serializers.SerializerMethodField()

    margin_percentual = serializers.SerializerMethodField()

    sales = OrderProductSaleProfit(many=True)

    def get_avg_profit_per_unit(self, obj) -> Decimal:
        return Decimal(sum([sale["profit_per_unit"] for sale in obj["sales"]]) / len(obj["sales"]))

    def get_avg_sell_price(self, obj) -> Decimal:
        return obj["sell_price"] / len(obj["sales"])

    def get_margin_percentual(self, obj) -> Decimal:
        return obj["absolute_margin"] / obj['sale_amount']


class MergeOrderSerializer(serializers.Serializer):
    order_list = serializers.PrimaryKeyRelatedField(
        queryset=models.Order.objects.filter(merge__isnull=True).all(),
        many=True,
        allow_empty=True,
    )
    delivery_address_id = serializers.PrimaryKeyRelatedField(
        queryset=models.ContactAddress.objects.all(), allow_null=True
    )
    shipping_rate_id = serializers.PrimaryKeyRelatedField(
        queryset=ShippingRate.objects.filter(
            active=True, shipping_method__active=True, shipping_zone__active=True
        ).all(),
        allow_null=True,
    )
    observations = serializers.CharField()


class OdooWebhookSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    state = serializers.CharField()
    pickup_date = serializers.DateField()
    # PROXIMAMENTE MÁS CAMPOS
