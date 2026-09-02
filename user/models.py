from decimal import Decimal

from django.contrib.auth.models import (
    BaseUserManager,
    Group,
    AbstractUser,
)
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_resized import ResizedImageField

from core.exceptions import ErrorContactingMessagingAPIException
from core.generics import PermissionsMeta


class UserManager(BaseUserManager):
    """_summary_

    Args:
        BaseUserManager (_type_): _description_
    """

    def create_user(self, email, password, first_name, last_name):
        if not email:
            raise ValueError("The user needs an email")

        user = self.model(email=self.normalize_email(email))

        user.set_password(password)
        user.first_name = first_name
        user.last_name = last_name
        user.save()
        return user

    def create_superuser(self, email, password, first_name, last_name):
        user = self.create_user(
            email=email, password=password, first_name=first_name, last_name=last_name
        )
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.save()
        return user


class Organization(models.Model):
    ORGANIZATION_TYPE_CHOICES = [
        ("empresa_estatal", "Empresa Estatal"),
        ("mipyme", "MiPyme"),
        ("tcp", "TCP"),
    ]

    name = models.CharField(max_length=255)
    nit_code = models.CharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(max_length=255, blank=True, null=True)
    address = models.CharField(max_length=1024, blank=True, null=True)
    organization_type = models.CharField(
        max_length=20, choices=ORGANIZATION_TYPE_CHOICES, default="empresa_estatal"
    )
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta(PermissionsMeta.Meta):
        permissions = [("manage_organization", _("Can manage organization"))]
        verbose_name = "Organization"
        verbose_name_plural = "Organizations"
        ordering = ["-id"]


class Fee(models.Model):
    name = models.CharField(max_length=255)
    fixed_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    percentual_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    default = models.BooleanField(default=False)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta(PermissionsMeta.Meta):
        permissions = [("manage_fee", _("Can manage fee"))]
        verbose_name = "Fee"
        verbose_name_plural = "Fees"
        ordering = ["-id"]


class User(AbstractUser):
    """_summary_

    Args:
        AbstractUser (_type_): _description_

    Returns:
        _type_: _description_
    """

    username = None
    email = models.EmailField(max_length=255, null=True, blank=True)
    dni = models.CharField(max_length=11, blank=True, null=True)
    address = models.CharField(max_length=1024, blank=True, null=True)
    phone_number = models.CharField(max_length=100, blank=True, null=True)
    profile_photo = ResizedImageField(
        size=[100, 100],
        crop=["middle", "center"],
        quality=75,
        upload_to="user/pics",
        default="user/user_photo_default.png",
        blank=True,
        null=True,
    )
    check_terms_conditions = models.BooleanField(default=False)
    check_privacy_policy = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_deliverer = models.BooleanField(default=False)
    verified = models.BooleanField(default=False)
    whatsapp_chat_id = models.CharField(max_length=100, blank=True, null=True)
    next_login_change_password = models.BooleanField(default=False)
    newsletter = models.BooleanField(default=False)
    fee = models.ForeignKey(
        Fee,
        related_name="clients",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    organization = models.ForeignKey(
        Organization,
        related_name="clients",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    groups = models.ManyToManyField(Group, related_name="users")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UserManager()

    @property
    def can_receive_newsletter(self):
        return self.newsletter and self.verified and self.is_active

    def __str__(self):
        if self.first_name is not None and self.last_name is not None:
            return f"{self.first_name} {self.last_name}"
        return str(self.id)

    def clean(self):
        if self.email:
            if User.objects.exclude(pk=self.pk).filter(email=self.email).exists():
                raise ValidationError({'email': 'Ya existe un usuario con este correo.'})

        super(User, self).clean()

    def save(self, *args, **kwargs):
        self.first_name = self.first_name.title()
        self.last_name = self.last_name.title()
        if self.phone_number:
            try:
                from core.services import WAHAService
                self.whatsapp_chat_id = WAHAService.check_exist(self.phone_number).get("chatId")
            except ErrorContactingMessagingAPIException as e:
                pass
        super().save(*args, **kwargs)

    class Meta(PermissionsMeta.Meta):
        permissions = [
            ("manage_user", _("Can manage user")),
            ("manage_customer", _("Can manage customer")),
            ("show_customer_orders", _("Can show customer orders")),
            ("show_customer_wallet", _("Can show customer wallet")),
            ("show_customer_coupons", _("Can show customer coupons")),
            ("show_customer_unpaid_orders", _("Can show customer unpaid orders")),
            ("manage_pos", _("Can manage point of sale")),
            ("manage_page", _("Can manage page")),
            ("manage_role", _("Can manage role")),
            ("show_all_boards", _("Can show all boards")),
            ("show_own_board", _("Can show own board")),
            ("show_all_orders", _("Can show all orders")),
            ("show_all_clients", _("Can show all clients")),
            ("show_availables_products", _("Can show availables products")),
            ("show_dashboards_conversion_rates", _("Can show conversion rates report")),
            ("show_dashboards_unpaid_report", _("Can show unpaid orders report")),
            ("can_deliver_orders", _("Can deliver orders")),
        ]
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["phone_number"]),
            models.Index(fields=["is_deliverer", "is_active"]),
            models.Index(fields=["newsletter", "is_active"]),
        ]


class EventLog(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    action = models.CharField(max_length=1024)
    description = models.TextField()
    raised_date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        User,
        related_name="event_logs",
        on_delete=models.PROTECT,
    )

    def __str__(self):
        return self.action

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Event Log"
        verbose_name_plural = "Event Logs"
        ordering = ["-raised_date"]
