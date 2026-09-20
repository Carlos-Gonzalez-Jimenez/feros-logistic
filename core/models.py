from decimal import Decimal

from django.db import models
from django.utils.translation import gettext_lazy as _

from cms.models import BlockMEDIA
from user.models import User
from .generics import PermissionsMeta


class ShippingCompany(models.Model):
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
    name = models.CharField(max_length=255)
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
    name = models.CharField(max_length=200)

    class Meta(PermissionsMeta.Meta):
        permissions = [("manage_presentation", _("Can manage presentation"))]
        verbose_name = "Presentation"
        verbose_name_plural = "Presentations"
        ordering = ["-id"]

    def __str__(self):
        return self.name


class ProductPresentation(models.Model):
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    provider = models.ForeignKey(Provider, on_delete=models.PROTECT)
    presentation = models.ManyToManyField(
        Presentation, related_name="products", blank=True
    )

    class Meta(PermissionsMeta.Meta):
        ordering = ["-id"]

    def __str__(self):
        return f"{self.product.name} - {self.provider.name}"


class ProductImageOrder(models.Model):
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


class ProcessingPlant(models.Model):
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
    po_number = models.CharField(max_length=100)
    po_date = models.DateField()
    quantity = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    product = models.ForeignKey(
        Product, related_name="purchase_orders", on_delete=models.CASCADE
    )
    provider = models.ForeignKey(
        Provider, related_name="purchase_orders", on_delete=models.CASCADE
    )
    measurement_unit = models.ForeignKey(
        Measurement_Unit, related_name="purchase_orders", on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.po_number

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Purchase Order"
        verbose_name_plural = "Purchase Orders"
        ordering = ["-po_date"]
        indexes = [
            models.Index(fields=["po_number"]),
        ]


class SaleOrder(models.Model):
    so_number = models.CharField(max_length=100)
    so_date = models.DateField()
    quantity = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    purchase_order = models.ForeignKey(
        PurchaseOrder, related_name="sale_orders", on_delete=models.CASCADE
    )
    processing_plant = models.ForeignKey(
        ProcessingPlant, related_name="sale_orders", on_delete=models.CASCADE
    )
    incoterms = models.ForeignKey(
        Incoterms, related_name="sale_orders", on_delete=models.CASCADE
    )
    shipment_port = models.ForeignKey(
        Port, related_name="shipment_sale_orders", on_delete=models.CASCADE
    )
    arrival_port = models.ForeignKey(
        Port, related_name="arrival_sale_orders", on_delete=models.CASCADE
    )
    observations = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.so_number

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Sale Order"
        verbose_name_plural = "Sale Orders"
        ordering = ["-so_date"]
        indexes = [
            models.Index(fields=["so_number"]),
        ]
