from decimal import Decimal

from django.db import transaction
from django.db.models import Count, Avg
from rest_framework import serializers

from cms.models import BlockMEDIA
from cms.serializers import BlockMEDIASerializer, get_any_blocks
from core.models import (
    Brand,
    Category,
    Country,
    CreditType,
    Measurement_Unit,
    Provider,
    Review,
    SpecificationDetails,
)
from core.serializers import (
    BrandSerializer,
    CategorySerializer,
    CountrySerializer,
    CreateOrderSerializer,
    MeasurementUnitSerializer,
    ProviderSerializer,
    SpecificationDetailsSerializer,
)
from payments.models import PaymentMethod
from pos import models


class ProductPosSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    product_images = BlockMEDIASerializer(many=True, source="ordered_product_images")
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
        queryset=Country.objects.filter(active=True),
        source="country",
    )
    brand_id = serializers.PrimaryKeyRelatedField(
        allow_null=True,
        required=False,
        queryset=Brand.objects.filter(active=True),
        source="brand",
    )
    provider_id = serializers.PrimaryKeyRelatedField(
        allow_null=True,
        required=False,
        queryset=Provider.objects.filter(active=True),
        source="provider",
    )
    measurement_unit_id = serializers.PrimaryKeyRelatedField(
        allow_null=True,
        required=False,
        queryset=Measurement_Unit.objects.filter(active=True),
        source="measurement_unit",
    )
    category_id = serializers.PrimaryKeyRelatedField(
        allow_null=True,
        required=False,
        queryset=Category.objects.filter(active=True),
        source="category",
    )
    specifications_details_ids = serializers.PrimaryKeyRelatedField(
        required=False,
        many=True,
        queryset=SpecificationDetails.objects.all(),
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
            "active",
            "reviews",
            "blocks",
        ]

    def get_reviews(self, obj) -> dict:
        reviews = Review.objects.filter(product=obj).aggregate(
            total=Count("id"), rating_avg=Avg("rating")
        )
        return reviews

    def get_unit_price(self, obj) -> Decimal:
        request = self.context.get("request")

        if not request:
            return Decimal("0.00")

        client_id = request.data.get("client_id") or request.query_params.get(
            "client_id"
        )

        if not client_id:
            return Decimal("0.00")

        try:
            client = models.User.objects.filter(id=client_id, is_active=True).first()

            if not client:
                return Decimal("0.00")

            return obj.sell_price(client.fee)

        except (ValueError, TypeError):
            return Decimal("0.00")

    def get_wholesale_price(self, obj) -> Decimal:
        request = self.context.get("request")

        if not request:
            return Decimal("0.00")

        client_id = request.data.get("client_id") or request.query_params.get(
            "client_id"
        )

        if not client_id:
            return Decimal("0.00")

        try:
            client = models.User.objects.filter(id=client_id, is_active=True).first()

            if not client:
                return Decimal("0.00")

            return obj.sell_wholesale_price(client.fee)

        except (ValueError, TypeError):
            return Decimal("0.00")

    def get_daily_variation(self, obj) -> Decimal:
        request = self.context.get("request")
        if not request:
            return Decimal("0.00")

        client_id = request.data.get("client_id") or request.query_params.get(
            "client_id"
        )
        if not client_id:
            return Decimal("0.00")

        try:
            client = models.User.objects.filter(id=client_id, is_active=True).first()

            if not client:
                return Decimal("0.00")

            fee = client.fee
            return obj.daily_variation * (1 + fee.percentual_fee if fee else 0)
        except (ValueError, TypeError):
            return Decimal("0.00")

    def get_price_per_box(self, obj) -> Decimal:
        request = self.context.get("request")

        if not request:
            return obj.quantity_per_box * obj.unit_price

        client_id = request.data.get("client_id") or request.query_params.get(
            "client_id"
        )

        if not client_id:
            return obj.quantity_per_box * obj.unit_price

        try:
            client = models.User.objects.filter(id=client_id, is_active=True).first()

            if not client:
                return obj.quantity_per_box * obj.unit_price

            return obj.quantity_per_box * obj.sell_price(client.fee)

        except (ValueError, TypeError):
            return obj.quantity_per_box * obj.unit_price

    def get_blocks(self, obj) -> list:
        return get_any_blocks(
            obj, "product", context={"request": self.context.get("request")}
        )


class PosCartSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    product = ProductPosSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        allow_null=False,
        required=True,
        queryset=models.Product.objects.filter(active=True),
    )
    client_id = serializers.PrimaryKeyRelatedField(
        allow_null=False,
        required=True,
        queryset=models.User.objects.filter(is_active=True),
    )
    price = serializers.SerializerMethodField()
    amount = serializers.SerializerMethodField()
    save_amount = serializers.SerializerMethodField()
    weight_net = serializers.SerializerMethodField()
    weight_gross = serializers.SerializerMethodField()

    class Meta:
        model = models.PosCart
        fields = [
            "id",
            "quantity",
            "price",
            "amount",
            "save_amount",
            "product",
            "product_id",
            "client_id",
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

    def get_weight_net(self, obj) -> float:
        return obj.quantity * obj.product.net_weight

    def get_weight_gross(self, obj) -> float:
        return obj.quantity * obj.product.gross_weight

    def create(self, validated_data):
        with transaction.atomic():
            seller = self.context.get("request").user
            client = validated_data["client_id"]
            product = validated_data["product_id"]
            quantity = validated_data["quantity"]
            pos_cart_products = models.PosCart.objects.filter(
                product_id=product.id, client_id=client.id, seller_id=seller.id
            )
            if pos_cart_products.exists():
                pos_cart_products.delete()
            pos_cart_product = models.PosCart.objects.create(
                product_id=product.id,
                client_id=client.id,
                seller_id=seller.id,
                quantity=quantity,
            )
            return pos_cart_product

    def update(self, instance, validated_data):
        with transaction.atomic():
            instance = super(PosCartSerializer, self).update(instance, validated_data)
            return instance


class CreatePosOrderSerializer(CreateOrderSerializer):
    payment_method_id = serializers.PrimaryKeyRelatedField(
        allow_null=False,
        required=True,
        queryset=PaymentMethod.objects.filter(active=True, use_in_pos=True),
    )
    client_id = serializers.PrimaryKeyRelatedField(
        allow_null=False,
        required=True,
        queryset=models.User.objects.filter(is_staff=False),
    )
    credit_type_id = serializers.PrimaryKeyRelatedField(
        allow_null=True,
        required=False,
        queryset=CreditType.objects.filter(active=True),
    )
    paid = serializers.BooleanField(default=False, allow_null=False)


class PosAddProductSerializer(serializers.Serializer):
    client_id = serializers.PrimaryKeyRelatedField(
        queryset=models.User.objects.all(), required=True
    )
    code_sku = serializers.CharField(required=True, max_length=100, min_length=1)
