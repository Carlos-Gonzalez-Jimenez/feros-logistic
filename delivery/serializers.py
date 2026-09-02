from django.db import transaction
from rest_framework import serializers

from core import serializers as core_serializers
from core.models import Municipality
from delivery import models
from user.models import User
from user.serializers import UserSerializer


class ShippingZoneSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    municipalities = core_serializers.MunicipalitySerializer(
        read_only=True, many=True, required=False
    )
    municipalities_ids = serializers.PrimaryKeyRelatedField(
        required=True,
        many=True,
        queryset=Municipality.objects.all(),
        source="municipalities",
    )
    total_assigned_municipalities = serializers.SerializerMethodField()
    deliverers = UserSerializer(read_only=True, many=True, required=False)
    deliverers_ids = serializers.PrimaryKeyRelatedField(
        required=True,
        many=True,
        queryset=User.objects.all(),
        source="deliverers",
    )
    deliverers_assigned = serializers.SerializerMethodField()
    province_id = serializers.SerializerMethodField()
    province = serializers.SerializerMethodField()

    class Meta:
        model = models.ShippingZone
        fields = [
            "id",
            "name",
            "municipalities",
            "municipalities_ids",
            "total_assigned_municipalities",
            "deliverers",
            "deliverers_ids",
            "deliverers_assigned",
            "province",
            "province_id",
            "created_at",
            "updated_at",
            "active",
        ]

    def get_province_id(self, obj) -> int | None:
        first_municipality = obj.municipalities.first()
        if first_municipality and first_municipality.province:
            return first_municipality.province.id
        return None

    def get_province(self, obj) -> dict | None:
        first_municipality = obj.municipalities.first()
        if first_municipality and first_municipality.province:
            return core_serializers.ProvinceSerializer(first_municipality.province).data
        return None

    def get_total_assigned_municipalities(self, obj) -> int:
        return obj.municipality_count()

    def get_deliverers_assigned(self, obj) -> bool:
        return obj.is_empty()

    def create(self, validated_data):
        with transaction.atomic():
            municipalities = validated_data.pop("municipalities", None)
            deliverers = validated_data.pop("deliverers", None)
            shipping_zone = models.ShippingZone.objects.create(**validated_data)
            if municipalities:
                shipping_zone.municipalities.set(municipalities)
            if deliverers:
                shipping_zone.deliverers.set(deliverers)
            return shipping_zone

    def update(self, instance, validated_data):
        with transaction.atomic():
            municipalities = validated_data.pop("municipalities_ids", None)
            deliverers = validated_data.pop("deliverers_ids", None)
            instance = super(ShippingZoneSerializer, self).update(
                instance, validated_data
            )
            if municipalities:
                instance.municipalities.clear()
                instance.municipalities.set(municipalities)
            if deliverers:
                instance.deliverers.clear()
                instance.deliverers.set(deliverers)
            return instance


class ShippingMethodSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    class Meta:
        model = models.ShippingMethod
        fields = [
            "id",
            "name",
            "shipping_method_type",
            "created_at",
            "updated_at",
            "active",
        ]


class ShippingRateSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    shipping_zone = ShippingZoneSerializer(read_only=True)
    shipping_zone_id = serializers.PrimaryKeyRelatedField(
        allow_null=False,
        required=True,
        queryset=models.ShippingZone.objects.all(),
        source="shipping_zone",
    )
    shipping_method = ShippingMethodSerializer(read_only=True)
    shipping_method_id = serializers.PrimaryKeyRelatedField(
        allow_null=False,
        required=True,
        queryset=models.ShippingMethod.objects.all(),
        source="shipping_method",
    )

    class Meta:
        model = models.ShippingRate
        fields = [
            "id",
            "shipping_zone",
            "shipping_zone_id",
            "shipping_method",
            "shipping_method_id",
            "price",
            "estimated_delivery_time",
            "active",
            "created_at",
            "updated_at",
        ]


class OrderShippingSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    order_id = serializers.PrimaryKeyRelatedField(
        allow_null=False,
        required=True,
        queryset=models.Order.objects.all(),
        source="order",
    )
    shipping_rate = ShippingRateSerializer(read_only=True)
    shipping_rate_id = serializers.PrimaryKeyRelatedField(
        allow_null=False,
        required=True,
        queryset=models.ShippingRate.objects.all(),
        source="shipping_rate",
    )
    deliverer = UserSerializer(read_only=True)
    deliverer_id = serializers.PrimaryKeyRelatedField(
        allow_null=False,
        required=True,
        queryset=models.User.objects.filter(is_deliverer=True),
        source="deliverer",
    )

    class Meta:
        model = models.OrderShipping
        fields = [
            "id",
            "order_id",
            "delivery_address",
            "shipping_rate",
            "shipping_rate_id",
            "deliverer",
            "deliverer_id",
            "shipping_price",
            "shipped_at",
            "estimated_delivery_at",
            "delivered_at",
            "created_at",
            "updated_at",
        ]


class AssignOrdersToDelivererSerializer(serializers.Serializer):
    deliverer = serializers.PrimaryKeyRelatedField(
        allow_null=False,
        required=True,
        queryset=models.User.objects.filter(is_deliverer=True, is_active=True),
    )
    orders = serializers.PrimaryKeyRelatedField(
        many=True,
        allow_null=False,
        required=True,
        queryset=models.Order.objects.filter(shipping__isnull=False, shipping__deliverer__isnull=True),
    )

    def create(self, validated_data):
        orders = validated_data.get("orders")
        deliverer = validated_data.get("deliverer")
        models.OrderShipping.objects.filter(deliverer__isnull=True, order__in=orders).update(deliverer=deliverer)
        return dict(orders=orders, deliverer=deliverer)
