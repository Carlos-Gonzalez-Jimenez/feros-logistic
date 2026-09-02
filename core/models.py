from decimal import Decimal

from django.db import models
from django.utils.translation import gettext_lazy as _

from cms.models import BlockMEDIA
from user.models import Fee, User
from .generics import PermissionsMeta


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

    odoo_product_id = models.PositiveBigIntegerField(null=True, unique=True)
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
    wholesale_price = models.DecimalField(
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
    daily_variation = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    minimal_stock = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("5.00")
    )
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    use_custom_template = models.BooleanField(default=False)
    on_offer = models.BooleanField(default=False)
    has_wholesale_price = models.BooleanField(default=False)
    wholesale_minimum = models.PositiveIntegerField(default=0)
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

    def sell_price(self, fee: Fee) -> Decimal:
        if fee is not None:
            return self.unit_price * (1 + fee.percentual_fee) + fee.fixed_fee
        return self.unit_price

    def sell_wholesale_price(self, fee: Fee) -> Decimal:
        if fee is not None:
            return self.wholesale_price * (1 + fee.percentual_fee) + fee.fixed_fee
        return self.wholesale_price


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


class CompositeProduct(models.Model):
    composite_product = models.ForeignKey(
        Product,
        related_name="composite_product",
        on_delete=models.PROTECT,
    )
    product = models.ForeignKey(
        Product,
        related_name="items",
        on_delete=models.PROTECT,
    )
    quantity = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )

    def __str__(self):
        return self.composite_product.name

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Composite Product"
        verbose_name_plural = "Composite Products"
        ordering = ["-id"]


class CreditType(models.Model):
    """_summary_

    Args:
        models (_type_): _description_
    """

    name = models.CharField(max_length=255)
    percentual_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    fixed_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    total_days = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta(PermissionsMeta.Meta):
        permissions = [("manage_credittypes", _("Can manage credit types"))]
        verbose_name = "Credit Type"
        verbose_name_plural = "Credit Types"
        ordering = ["-id"]


class Order(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    creation_date = models.DateTimeField(auto_now_add=True)
    expiration_date = models.DateField(null=True, blank=True)
    odoo_order_id = models.PositiveBigIntegerField(null=True, unique=True, blank=True)
    observations = models.TextField(blank=True, null=True)
    fixed_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    percentual_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    total_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    pending_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    credit_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    total_discount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    payment_deadline = models.DateField(null=True, blank=True)
    client = models.ForeignKey(
        User, related_name="orders_client", on_delete=models.PROTECT
    )
    seller = models.ForeignKey(
        User,
        related_name="orders_seller",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    credit_type = models.ForeignKey(
        CreditType,
        related_name="orders_credit",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    merge = models.ForeignKey(
        to="self",
        related_name="orders",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
    )

    def __str__(self):
        return str(self.id)

    class Meta(PermissionsMeta.Meta):
        permissions = [
            ("manage_order", _("Can manage order")),
            ("change_order_status", _("Can change order status")),
        ]
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["client", "-creation_date"]),
        ]

    @property
    def current_status(self):
        return self.order_trackings.order_by("-id").first()


class OrderProducts(models.Model):
    """_summary_

    Args:
        models (_type_): _description_
    """

    quantity = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    price = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    order = models.ForeignKey(
        Order, related_name="order_products", on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        Product, related_name="order_products", on_delete=models.CASCADE
    )

    @property
    def amount(self) -> Decimal:
        return self.quantity * self.price

    def __str__(self):
        return f"Product {self.product.name} from order {self.order.id}"

    class Meta(PermissionsMeta.Meta):
        permissions = [("manage_orderproducts", _("Can manage order product"))]
        verbose_name = "Order Product"
        verbose_name_plural = "Order Products"
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["order", "product"]),
        ]


class Batch(models.Model):
    batch_identificator = models.CharField(max_length=255, unique=True)
    invoice_number = models.CharField(max_length=255, blank=True, null=True)

    notes = models.TextField(blank=True, null=True)
    # total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    completed = models.BooleanField(default=False)
    processed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta(PermissionsMeta.Meta):
        permissions = [("manage_batch_entry", _("Can manage batch entry"))]
        ordering = ["-processed_at", "-created_at"]
        verbose_name = "Batch entry"
        verbose_name_plural = "Batch entries"

    def __str__(self):
        return f"{self.batch_identificator[:50]}"


class BatchItem(models.Model):
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    quantity_sold = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    amount_sold = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    sold = models.BooleanField(default=False)
    batch = models.ForeignKey(
        Batch,
        related_name="items",
        on_delete=models.PROTECT,
    )
    product = models.ForeignKey(
        Product,
        related_name="batch_items",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.product.name

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Batch Item"
        verbose_name_plural = "Batch Items"
        ordering = ["-id"]


class ProductBatch(models.Model):
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    order_product = models.ForeignKey(
        OrderProducts,
        related_name="batch_item",
        on_delete=models.PROTECT,
    )
    batch_item = models.ForeignKey(
        BatchItem,
        related_name="order_product",
        on_delete=models.PROTECT,
    )
    reserved = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.order_product.product.name} {self.batch_item.batch.batch_identificator}"

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Product Batch"
        verbose_name_plural = "Product Batch"
        ordering = ["-id"]


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


class OrderStatus(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    name = models.CharField(max_length=255)
    code_name = models.CharField(max_length=20, blank=True, null=True)
    order = models.IntegerField(default=0)
    icon = models.CharField(max_length=255, null=True, blank=True)
    color = models.CharField(max_length=50, null=True, blank=True)
    initial_status = models.BooleanField(default=False)
    final_status = models.BooleanField(default=False)
    store_status = models.BooleanField(default=False)
    delivery_status = models.BooleanField(default=False)
    merge_status = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Order Status"
        verbose_name_plural = "Order Statuses"
        ordering = ["order"]
        indexes = [
            models.Index(fields=["code_name"]),
        ]


class Review(models.Model):
    """

    Args:
        models (_type_): _description_
    """

    comment = models.TextField(blank=True, null=True)
    rating = models.PositiveIntegerField(default=0)
    review_date = models.DateTimeField(auto_now_add=True)
    product = models.ForeignKey(
        Product, related_name="reviews", on_delete=models.PROTECT
    )
    user = models.ForeignKey(User, related_name="reviews", on_delete=models.PROTECT)

    def __str__(self):
        return self.comment

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Review"
        verbose_name_plural = "Reviews"
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["product"]),
            models.Index(fields=["product", "rating"]),
            models.Index(fields=["product", "rating", "-review_date"]),
        ]


class Province(models.Model):
    """_summary_

    Args:
        models (_type_): _description_
    """

    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta(PermissionsMeta.Meta):
        permissions = [("show_province", _("Can show province"))]
        verbose_name = "Province"
        verbose_name_plural = "Provinces"
        ordering = ["id"]


class Municipality(models.Model):
    """_summary_

    Args:
        models (_type_): _description_
    """

    name = models.CharField(max_length=255)
    province = models.ForeignKey(
        Province, related_name="municipalities", on_delete=models.PROTECT
    )

    def __str__(self):
        return self.name

    class Meta(PermissionsMeta.Meta):
        permissions = [("show_municipality", _("Can show municipality"))]
        verbose_name = "Municipality"
        verbose_name_plural = "Municipalities"
        ordering = ["id"]


class ContactAddress(models.Model):
    """_summary_

    Args:
        models (_type_): _description_
    """

    address = models.CharField(max_length=255)
    reference = models.TextField(blank=True, null=True)
    default = models.BooleanField(default=False)
    user = models.ForeignKey(User, related_name="addresses", on_delete=models.PROTECT)
    municipality = models.ForeignKey(
        Municipality, related_name="addresses", on_delete=models.PROTECT
    )

    def __str__(self):
        return self.address

    class Meta(PermissionsMeta.Meta):
        permissions = [("manage_contactaddress", _("Can manage contact address"))]
        verbose_name = "Contact Address"
        verbose_name_plural = "Contact Addresses"
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["user"]),
        ]


class OrderTracking(models.Model):
    """_summary_

    Args:
        models (_type_): _description_
    """

    order_tracking_date = models.DateTimeField(auto_now_add=True)
    observations = models.TextField(blank=True, null=True)
    order = models.ForeignKey(
        Order, related_name="order_trackings", on_delete=models.CASCADE
    )
    status = models.ForeignKey(
        OrderStatus, related_name="order_trackings", on_delete=models.CASCADE
    )

    def __str__(self):
        return f"{self.order} - {self.status.name}"

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Order Tracking"
        verbose_name_plural = "Order Trackings"
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["order", "status"]),
        ]


class Cart(models.Model):
    """_summary_

    Args:
        models (_type_): _description_
    """

    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    client = models.ForeignKey(User, related_name="cart", on_delete=models.PROTECT)
    product = models.ForeignKey(Product, related_name="cart", on_delete=models.PROTECT)

    def __str__(self):
        return self.client

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Cart"
        verbose_name_plural = "Carts"
        ordering = ["id"]
        indexes = [
            models.Index(fields=["client", "product"]),
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
    social_networks = models.JSONField(default=list)

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

    odoo_url = models.CharField(max_length=255, blank=True, null=True)
    odoo_token = models.TextField(blank=True, null=True)

    order_expiration_days = models.SmallIntegerField(default=1)

    def __str__(self):
        return "Configuration"

    class Meta(PermissionsMeta.Meta):
        permissions = [("manage_config", _("Can manage configuration")), ]
        verbose_name = "Configuration"
        verbose_name_plural = "Configurations"
        ordering = ["-id"]


class VehicleType(models.Model):
    """_summary_

    Args:
        models (_type_): _description_
    """

    name = models.CharField(max_length=100)
    color = models.CharField(max_length=100)
    icon = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Vehicle Type"
        verbose_name_plural = "Vehicle Types"
        ordering = ["id"]


class Vehicle(models.Model):
    """_summary_

    Args:
        models (_type_): _description_
    """

    plate = models.CharField(max_length=10)
    avg_fuel_consumption = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    driver = models.ForeignKey(User, related_name="vehicles", on_delete=models.PROTECT, null=True)
    vehicle_type = models.ForeignKey(VehicleType, related_name="vehicles", on_delete=models.PROTECT)
    device_id = models.CharField(max_length=255, blank=True, null=True)
    use_mobile_gps = models.BooleanField(default=False)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.plate

    class Meta(PermissionsMeta.Meta):
        permissions = [("manage_vehicles", _("Can manage vehicles"))]
        verbose_name = "Vehicle"
        verbose_name_plural = "Vehicles"
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["plate"]),
        ]


class VehicleLocation(models.Model):
    vehicle = models.ForeignKey(Vehicle, related_name="locations", on_delete=models.CASCADE)
    driver = models.ForeignKey(User, related_name="locations", on_delete=models.CASCADE, null=True, blank=True)
    lat = models.DecimalField(max_digits=10, decimal_places=7)
    lon = models.DecimalField(max_digits=10, decimal_places=7)
    alt = models.DecimalField(max_digits=10, decimal_places=2)
    cog = models.DecimalField(max_digits=10, decimal_places=2)
    vel = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    acc = models.DecimalField(max_digits=10, decimal_places=2)
    vac = models.DecimalField(max_digits=10, decimal_places=2)
    batt = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    broker_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Vehicle Location"
        verbose_name_plural = "Vehicle Locations"
        ordering = ["-created_at"]
