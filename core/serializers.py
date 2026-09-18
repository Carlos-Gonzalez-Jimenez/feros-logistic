from decimal import Decimal
from django.db import transaction
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
from user.models import User


class ShippingCompanySerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    class Meta:
        model = models.ShippingCompany
        fields = "__all__"


class VesselSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    shipping_company = ShippingCompanySerializer(read_only=True)
    shipping_company_id = serializers.PrimaryKeyRelatedField(
        allow_null=True,
        required=False,
        queryset=models.ShippingCompany.objects.all(),
        source="shipping_company",
    )

    class Meta:
        model = models.Vessel
        fields = [
            "name",
            "shipping_company",
            "shipping_company_id",
            "active",
        ]


class ContainerTypeSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    class Meta:
        model = models.ContainerType
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
            "cost_price",
            "unit_price",
            "net_weight",
            "gross_weight",
            "quantity_per_box",
            "description",
            "use_custom_template",
            "active",
            "blocks",
        ]

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
    blocks = serializers.SerializerMethodField()

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
            "cost_price",
            "unit_price",
            "net_weight",
            "gross_weight",
            "quantity_per_box",
            "description",
            "use_custom_template",
            "active",
            "blocks",
        ]

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
            "cost_price",
            "unit_price",
            "net_weight",
            "gross_weight",
            "quantity_per_box",
            "description",
            "use_custom_template",
            "active",
        ]


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


class PortSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    class Meta:
        model = models.Port
        fields = "__all__"


class IncotermsSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    class Meta:
        model = models.Incoterms
        fields = "__all__"


class ProcessingPlantSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    class Meta:
        model = models.ProcessingPlant
        fields = "__all__"


class PurchaseOrderSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    product = ProductReadSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        required=True,
        queryset=models.Product.objects.all(),
        source="product",
    )
    provider = ProviderSerializer(read_only=True)
    provider_id = serializers.PrimaryKeyRelatedField(
        required=True,
        queryset=models.Provider.objects.all(),
        source="provider",
    )
    measurement_unit = MeasurementUnitSerializer(read_only=True)
    measurement_unit_id = serializers.PrimaryKeyRelatedField(
        required=True,
        queryset=models.Measurement_Unit.objects.all(),
        source="measurement_unit",
    )

    class Meta:
        model = models.PurchaseOrder
        fields = [
            "po_number",
            "po_date",
            "quantity",
            "product",
            "product_id",
            "provider",
            "provider_id",
            "measurement_unit",
            "measurement_unit_id",
            "created_at",
        ]
