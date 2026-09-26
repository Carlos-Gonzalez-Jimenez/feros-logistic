from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from cms.models import BlockMEDIA
from user.models import User
from .generics import PermissionsMeta


class Customer(models.Model):
    bussines_name = models.CharField(max_length=100)
    business_phone = models.CharField(max_length=50, null=True, blank=True)
    business_email = models.EmailField(null=True, blank=True)
    nit_code = models.CharField(max_length=100, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    contacts = models.JSONField(default=list, blank=True)

    class Meta(PermissionsMeta.Meta):
        permissions = [
            ("manage_customers", _("Can manage customers"))
        ]
        verbose_name = "Customer"
        verbose_name_plural = "Customers"
        ordering = ["bussines_name"]


class ShippingCompany(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    name = models.CharField(max_length=255)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta(PermissionsMeta.Meta):
        permissions = [
            ("manage_shipping_companies", _("Can manage shipping companies"))
        ]
        verbose_name = "Shipping Company"
        verbose_name_plural = "Shipping Companies"
        ordering = ["name"]


class Vessel(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    name = models.CharField(max_length=255)
    shipping_company = models.ForeignKey(
        ShippingCompany,
        related_name="vessels",
        on_delete=models.PROTECT,
    )
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta(PermissionsMeta.Meta):
        permissions = [("manage_vessels", _("Can manage vessels"))]
        verbose_name = "Vessel"
        verbose_name_plural = "Vessels"
        ordering = ["name"]


class ContainerType(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    name = models.CharField(max_length=255)
    abbreviation = models.CharField(max_length=10)
    free_days = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta(PermissionsMeta.Meta):
        permissions = [("manage_container_types", _("Can manage container types"))]
        verbose_name = "Container Type"
        verbose_name_plural = "Container Types"
        ordering = ["name"]


class Currency(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    name = models.CharField(max_length=255)
    initials = models.CharField(max_length=5)
    symbol = models.CharField(max_length=1)
    exchange_rate = models.DecimalField(
        max_digits=10, decimal_places=4, default=Decimal("0.00")
    )
    exchange_rate_date = models.DateTimeField(auto_now=True)
    default = models.BooleanField(default=False)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta(PermissionsMeta.Meta):
        permissions = [("manage_currencies", _("Can manage currencies"))]
        verbose_name = "Currency"
        verbose_name_plural = "Currencies"
        ordering = ["-id"]


class NotificationType(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    name = models.CharField(max_length=1024)
    icon = models.CharField(max_length=255, blank=True, null=True)
    color = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Notification Type"
        verbose_name_plural = "Notification Types"
        ordering = ["name"]


class Notification(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    title = models.CharField(max_length=255)
    message = models.CharField(max_length=1024)
    sent_date = models.DateTimeField(auto_now_add=True)
    notification_type = models.ForeignKey(
        NotificationType,
        related_name="notifications",
        on_delete=models.PROTECT,
    )

    def __str__(self):
        return self.title

    class Meta(PermissionsMeta.Meta):
        permissions = [("manage_notification", _("Can manage notification"))]
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ["-id"]


class NotificationUser(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    read = models.BooleanField(default=False)
    notification = models.ForeignKey(
        Notification, related_name="notifications_user", on_delete=models.PROTECT
    )
    user = models.ForeignKey(
        User, related_name="notifications_user", on_delete=models.PROTECT
    )

    def __str__(self):
        return self.notification.title

    class Meta(PermissionsMeta.Meta):
        verbose_name = "User Notification"
        verbose_name_plural = "User Notifications"
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["user"]),
        ]


class Measurement_Unit(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    name = models.CharField(max_length=255, unique=True)
    abbreviation = models.CharField(max_length=3)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta(PermissionsMeta.Meta):
        permissions = [("manage_measurement_unit", _("Can manage measurement unit"))]
        verbose_name = "Measurement Unit"
        verbose_name_plural = "Measurement Units"
        ordering = ["name"]


class Provider(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    name = models.CharField(max_length=255, unique=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta(PermissionsMeta.Meta):
        permissions = [("manage_provider", _("Can manage provider"))]
        verbose_name = "Provider"
        verbose_name_plural = "Providers"
        ordering = ["name"]


class Country(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    name = models.CharField(max_length=255, unique=True)
    code_alpha3 = models.CharField(max_length=3)
    country_flag = models.ImageField(
        upload_to="flags/pics",
        default="flags/flag_image_default.png",
        blank=True,
        null=True,
    )
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta(PermissionsMeta.Meta):
        permissions = [("manage_country", _("Can manage country"))]
        verbose_name = "Country"
        verbose_name_plural = "Countries"
        ordering = ["name"]


class Brand(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    parent = models.ForeignKey(
        to="self",
        related_name="brand",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
    )
    logo_brand = models.ImageField(
        upload_to="brands/pics",
        default="brands/brand_image_default.png",
        blank=True,
        null=True,
    )
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta(PermissionsMeta.Meta):
        permissions = [("manage_brand", _("Can manage brand"))]
        verbose_name = "Brand"
        verbose_name_plural = "Brands"
        ordering = ["name"]


class Category(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    name = models.CharField(max_length=255)
    parent = models.ForeignKey(
        to="self",
        related_name="category",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
    )
    category_image = models.ImageField(
        upload_to="categories/pics",
        default="categories/category_image_default.png",
        blank=True,
        null=True,
    )
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta(PermissionsMeta.Meta):
        permissions = [("manage_category", _("Can manage category"))]
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["id"]


class Specifications(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    name = models.CharField(max_length=255, unique=True)
    icon = models.CharField(max_length=255, blank=True, null=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta(PermissionsMeta.Meta):
        permissions = [("manage_specifications", _("Can manage specifications"))]
        verbose_name = "Specification"
        verbose_name_plural = "Specifications"
        ordering = ["id"]


class Product(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    code_sku = models.CharField(max_length=255, blank=True, unique=True)
    part_code = models.CharField(max_length=255, blank=True)
    name = models.CharField(max_length=1024)
    slug = models.SlugField(max_length=255, unique=True)
    product_images = models.ManyToManyField(
        BlockMEDIA, through="ProductImageOrder", related_name="products", blank=True
    )
    quantity = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    net_content = models.CharField(max_length=255, blank=True, null=True)
    cost_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    net_weight = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    gross_weight = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    quantity_per_box = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    use_custom_template = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    custom_template = models.BooleanField(default=False)
    category = models.ForeignKey(
        Category,
        related_name="products",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    provider = models.ForeignKey(
        Provider,
        related_name="products",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    brand = models.ForeignKey(
        Brand,
        related_name="products",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    country = models.ForeignKey(
        Country,
        related_name="products",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    measurement_unit = models.ForeignKey(
        Measurement_Unit,
        related_name="products",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.name

    def ordered_product_images(self):
        return self.product_images.order_by("productimageorder__id")

    class Meta(PermissionsMeta.Meta):
        permissions = [("manage_product", _("Can manage product"))]
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ["code_sku"]
        indexes = [
            models.Index(fields=["category", "active"]),
            models.Index(fields=["part_code", "active"]),
            models.Index(fields=["brand", "active"]),
            models.Index(fields=["provider", "active"]),
        ]


class Presentation(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    name = models.CharField(max_length=200)

    class Meta(PermissionsMeta.Meta):
        permissions = [("manage_presentation", _("Can manage presentation"))]
        verbose_name = "Presentation"
        verbose_name_plural = "Presentations"
        ordering = ["-id"]

    def __str__(self):
        return self.name


class ProductProvider(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    provider = models.ForeignKey(Provider, on_delete=models.PROTECT)

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Product - Presentation"
        verbose_name_plural = "Product - Presentations"
        ordering = ["-id"]
        unique_together = ["product", "provider"]

    def __str__(self):
        return f"{self.product.name} - {self.provider.name}"


class ProductProviderPresentation(models.Model):
    """_summary_

    Args:
        models (_type_): _description_
    """

    product_provider = models.ForeignKey(ProductProvider, on_delete=models.CASCADE)
    presentation = models.ForeignKey(
        Presentation, related_name="product_providers", on_delete=models.PROTECT
    )
    active = models.BooleanField(default=True)

    class Meta(PermissionsMeta.Meta):
        unique_together = ["product_provider", "presentation"]


class ProductImageOrder(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    blockmedia = models.ForeignKey(BlockMEDIA, on_delete=models.CASCADE)

    class Meta(PermissionsMeta.Meta):
        ordering = ["id"]
        unique_together = [["product", "blockmedia"]]
        indexes = [
            models.Index(fields=["product", "id"]),
        ]

    def __str__(self):
        return f"{self.product.name} - Imagen {str(self.id)}"


class SpecificationDetails(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    value = models.TextField(blank=True, null=True)
    product = models.ForeignKey(
        Product,
        related_name="specifications_details",
        on_delete=models.CASCADE,
    )
    specification = models.ForeignKey(
        Specifications,
        related_name="specifications_details",
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return f"{self.product.name} - {self.specification.name}"

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Specification Detail"
        verbose_name_plural = "Specification Details"
        ordering = ["id"]
        indexes = [
            models.Index(fields=["product"]),
            models.Index(fields=["product", "specification"]),
        ]


class Config(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    business_name = models.CharField(max_length=255, null=True, blank=True)
    business_phone = models.CharField(max_length=50, null=True, blank=True)
    business_email = models.CharField(max_length=100, null=True, blank=True)
    business_account = models.CharField(max_length=100, null=True, blank=True)
    business_nit = models.CharField(max_length=100, null=True, blank=True)
    business_licence = models.CharField(max_length=100, null=True, blank=True)
    business_schedule = models.TextField(null=True, blank=True)
    business_address = models.TextField(null=True, blank=True)
    social_networks = models.JSONField(default=list, blank=True)

    backend_url = models.CharField(max_length=255, default="")
    front_url = models.CharField(max_length=255, default="")
    recover_password_url = models.CharField(max_length=255, default="")
    login_url = models.CharField(max_length=255, default="")
    confirm_register_url = models.CharField(max_length=255, default="")

    recover_password_token_validation_time = models.IntegerField(default=30)
    ecommerce_commission_is_percentage = models.BooleanField(default=True)
    ecommerce_commission_value = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    client_minimum_wallet_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("100.00")
    )
    billing_email = models.TextField(blank=True, null=True)
    logo_light = models.ImageField(
        upload_to="config/pics", default="config/config_image_default.png"
    )
    logo_dark = models.ImageField(
        upload_to="config/pics", default="config/config_image_default.png"
    )
    logo_horizontal_light = models.ImageField(
        upload_to="config/pics", default="config/config_image_default.png"
    )
    logo_horizontal_dark = models.ImageField(
        upload_to="config/pics", default="config/config_image_default.png"
    )
    admin_logo_horizontal_light = models.ImageField(
        upload_to="config/pics", default="config/config_image_default.png"
    )
    admin_logo_horizontal_dark = models.ImageField(
        upload_to="config/pics", default="config/config_image_default.png"
    )

    waha_api_url = models.CharField(max_length=255, blank=True, null=True)
    waha_api_user = models.CharField(max_length=255, blank=True, null=True)
    waha_api_apikey = models.CharField(
        max_length=255, blank=True, null=True, default="admin"
    )
    waha_api_password = models.CharField(max_length=255, blank=True, null=True)
    waha_api_session = models.CharField(max_length=255, blank=True, null=True)

    enzona_api_url = models.CharField(max_length=255, blank=True, null=True)
    enzona_consumer_key = models.CharField(max_length=255, blank=True, null=True)
    enzona_consumer_secret = models.CharField(max_length=255, blank=True, null=True)

    transfermovil_api_url = models.CharField(max_length=255, blank=True, null=True)
    transfermovil_callback_url = models.CharField(max_length=255, blank=True, null=True)
    transfermovil_username = models.CharField(max_length=255, blank=True, null=True)
    transfermovil_source = models.CharField(max_length=255, blank=True, null=True)
    transfermovil_seed = models.CharField(max_length=255, blank=True, null=True)

    tropipay_api_url = models.CharField(max_length=255, blank=True, null=True)
    tropipay_client_id = models.CharField(max_length=255, blank=True, null=True)
    tropipay_client_secret = models.CharField(max_length=255, blank=True, null=True)
    tropipay_paymentcards_account_id = models.IntegerField(blank=True, null=True)

    mqtt_client_id = models.CharField(max_length=255, blank=True, null=True)
    mqtt_username = models.CharField(max_length=255, blank=True, null=True)
    mqtt_password = models.CharField(max_length=255, blank=True, null=True)
    mqtt_host = models.CharField(max_length=255, blank=True, null=True)
    mqtt_port = models.IntegerField(blank=True, null=True)
    mqtt_location_topic = models.CharField(max_length=255, blank=True, null=True)

    astrack_url = models.CharField(max_length=255, blank=True, null=True)
    astrack_websocket = models.CharField(max_length=255, blank=True, null=True)
    astrack_token = models.TextField(blank=True, null=True)

    def __str__(self):
        return "Configuration"

    class Meta(PermissionsMeta.Meta):
        permissions = [
            ("manage_config", _("Can manage configuration")),
        ]
        verbose_name = "Configuration"
        verbose_name_plural = "Configurations"
        ordering = ["-id"]


class Port(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    name = models.CharField(max_length=100)
    abbreviation = models.CharField(max_length=20)
    description = models.TextField(blank=True, null=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Port"
        verbose_name_plural = "Ports"
        permissions = [
            ("manage_ports", _("Can manage ports")),
        ]
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["abbreviation"]),
        ]


class Incoterms(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    name = models.CharField(max_length=100)
    abbreviation = models.CharField(max_length=20)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Incoterms"
        verbose_name_plural = "Incoterms"
        permissions = [
            ("manage_incoterms", _("Can manage incoterms")),
        ]
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["abbreviation"]),
        ]


class PaymentAgreement(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Payment Agreement"
        verbose_name_plural = "Payment Agreement"
        permissions = [
            ("manage_payment_agreements", _("Can manage payment agreements")),
        ]
        ordering = ["name"]


class ProcessingPlant(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    name = models.CharField(max_length=100)
    phytosanitary_permit = models.BooleanField(default=False)
    phytosanitary_permit_expires = models.DateField(blank=True, null=True)
    veterinary_permit = models.BooleanField(default=False)
    veterinary_permit_expires = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Processing Plant"
        verbose_name_plural = "Processing Plants"
        permissions = [
            ("manage_processing_plants", _("Can manage processing plant")),
        ]
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["name"]),
        ]


class PurchaseOrder(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    provider = models.ForeignKey(
        Provider, related_name="purchase_orders", on_delete=models.PROTECT
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="purchase_orders",
        on_delete=models.PROTECT,
    )
    observations = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.pk

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Purchase Order"
        verbose_name_plural = "Purchase Orders"
        permissions = [
            ("manage_purchase_orders", _("Can manage purchase orders")),
        ]
        ordering = ["-id"]


class PurchaseOrderItem(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    purchase_order = models.ForeignKey(
        PurchaseOrder, related_name="purchase_order_items", on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        ProductProviderPresentation,
        related_name="purchase_order_items",
        on_delete=models.PROTECT,
    )
    quantity = models.PositiveIntegerField(default=1)
    measurement_unit = models.ForeignKey(Measurement_Unit, on_delete=models.PROTECT)

    def __str__(self):
        return self.pk

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Purchase Order Item"
        verbose_name_plural = "Purchase Order Items"
        ordering = ["-id"]


class SaleOrder(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    so_number = models.CharField(max_length=100)
    so_date = models.DateField()
    observations = models.TextField(blank=True, null=True)
    total_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00"), editable=False
    )
    created_at = models.DateTimeField(auto_now_add=True)
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        related_name="sale_orders",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    provider = models.ForeignKey(
        Provider, related_name="sale_orders", on_delete=models.PROTECT
    )
    processing_plant = models.ForeignKey(
        ProcessingPlant,
        related_name="sale_orders",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    incoterms = models.ForeignKey(
        Incoterms, related_name="sale_orders", on_delete=models.PROTECT
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="sale_orders",
        on_delete=models.PROTECT,
        editable=False,
    )

    def __str__(self):
        return self.so_number

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Sale Order"
        verbose_name_plural = "Sale Orders"
        permissions = [
            ("manage_sale_orders", _("Can manage sale orders")),
        ]
        ordering = ["-so_date"]
        indexes = [
            models.Index(fields=["so_number"]),
        ]


class SaleOrderItems(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    sale_order = models.ForeignKey(
        SaleOrder, related_name="sale_order_items", on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        ProductProviderPresentation,
        related_name="sale_order_items",
        on_delete=models.PROTECT,
    )
    quantity = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    measurement_unit = models.ForeignKey(Measurement_Unit, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.sale_order.so_number} - {self.product.product_provider.product.name}"

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Sale Order Item"
        verbose_name_plural = "Sale Order Items"
        ordering = ["-id"]


class Invoice(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    bill_number = models.CharField(max_length=100)
    emission_date = models.DateField()
    expiration_date = models.DateField()
    payment_date = models.DateField(default=None, blank=True, null=True)
    total_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00"), editable=False
    )
    pending_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00"), editable=False
    )
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    other_charges_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    payment_agreement = models.ForeignKey(PaymentAgreement, on_delete=models.PROTECT)

    """
    total_amount = amount + other_charges_amount
    amount = Monto relacionado con los servicios
    other_charges_amount = Monto relacionado con otros cargos.
    """

    def __str__(self):
        return self.bill_number

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Invoice"
        verbose_name_plural = "Invoices"
        ordering = ["-id"]
        indexes = [models.Index(fields=["bill_number"])]

    def sync_pending_amount(self):
        self.pending_amount = (
            self.total_amount
            - self.payments.aggregate(pending_amount=Sum("amount_paid", default=0))[
                "pending_amount"
            ]
        )
        if self.pending_amount <= 0:
            self.payment_date = now().date()
        else:
            self.payment_date = None
        self.save()


class InvoicePayment(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    invoice = models.ForeignKey(
        Invoice, related_name="payments", on_delete=models.CASCADE
    )
    amount_paid = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    observations = models.TextField(blank=True, null=True)
    payment_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.invoice.bill_number} : {self.amount_paid}"

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Invoice Payment"
        verbose_name_plural = "Invoice Payments"
        ordering = ["-id"]


class Booking(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    booking_number = models.CharField(max_length=30)
    port_loading = models.ForeignKey(
        Port, on_delete=models.PROTECT, related_name="port_loading"
    )
    port_discharge = models.ForeignKey(
        Port, on_delete=models.PROTECT, related_name="port_discharge"
    )
    shipping_company = models.ForeignKey(
        ShippingCompany, related_name="bookings", on_delete=models.PROTECT
    )
    vessel = models.ForeignKey(
        Vessel, related_name="bookings", on_delete=models.PROTECT, null=True, blank=True
    )
    voyage_number = models.CharField(max_length=20, blank=True)
    quoted_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    cut_off = models.DateField(null=True, blank=True)
    ets = models.DateField(null=True, blank=True)
    eta = models.DateField(null=True, blank=True)
    observations = models.TextField(null=True, blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    sale_orders = models.ManyToManyField(SaleOrder, blank=True, related_name="bookings")

    def __str__(self):
        return self.booking_number

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Booking"
        verbose_name_plural = "Bookings"
        permissions = [
            ("manage_bookings", _("Can manage bookings")),
        ]
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["booking_number"]),
            models.Index(fields=["ets"]),
            models.Index(fields=["eta"]),
            models.Index(fields=["shipping_company", "ets"]),
            models.Index(fields=["shipping_company", "eta"]),
        ]


class Container(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    booking = models.ForeignKey(
        Booking, on_delete=models.SET_NULL, null=True, related_name="containers"
    )
    container_type = models.ForeignKey(
        ContainerType, on_delete=models.PROTECT, related_name="containers"
    )
    container_number = models.CharField(max_length=15, null=True, blank=True)
    seal_number = models.CharField(max_length=20, null=True, blank=True)
    net_weight = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    gross_weight = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    discharge_date = models.DateField(null=True, blank=True)
    extraction_date = models.DateField(null=True, blank=True)
    return_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.booking.booking_number} - {self.container_type.name}"

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Container"
        verbose_name_plural = "Containers"
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["discharge_date"]),
            models.Index(fields=["booking", "discharge_date"]),
        ]


class ContainerItem(models.Model):
    """_summary_

    Args:
        models (_type_): _description_
    """

    container = models.ForeignKey(
        Container, on_delete=models.CASCADE, related_name="items"
    )
    product = models.ForeignKey(
        ProductProviderPresentation,
        on_delete=models.PROTECT,
        related_name="container_items",
    )
    sale_order_item = models.ForeignKey(
        SaleOrderItems, related_name="container_items", on_delete=models.PROTECT
    )
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    unit_weight = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )


class ShippingCompanyInvoice(Invoice):
    """_summary_

    Args:
        Invoice (_type_): _description_

    Returns:
        _type_: _description_
    """

    booking = models.ForeignKey(
        Booking, related_name="shipping_company_invoice", on_delete=models.PROTECT
    )
    bl_number = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return self.bill_number

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Shipping Company Invoice"
        verbose_name_plural = "Shipping Company Invoices"
        ordering = ["-id"]


class ProviderInvoice(Invoice):
    """_summary_

    Args:
        Invoice (_type_): _description_

    Returns:
        _type_: _description_
    """

    sale_order = models.ForeignKey(SaleOrder, related_name="invoices", on_delete=models.PROTECT)

    def __str__(self):
        return self.bill_number

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Provider Invoice"
        verbose_name_plural = "Provider Invoices"
        ordering = ["-id"]
