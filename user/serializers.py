from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.utils.timezone import now

from core.models import Config
from payments.models import Wallet
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from logistic_backend.settings import MEDIA_URL
from user.models import User, EventLog, Fee, Organization
from user.exceptions import (
    NotMatchException,
    UserNotActiveException,
    UserNotVerifiedException,
)
from core.services import WAHAService
from django.db import transaction
from django.template.loader import get_template
from .tasks import send_mail, password_generator
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class PermissionSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    name = serializers.SerializerMethodField()

    class Meta:
        model = Permission
        fields = ["id", "name", "codename"]

    def get_name(self, obj) -> str:
        return _(obj.name)


class RoleSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    permissions = PermissionSerializer(read_only=True, many=True)
    permissions_id = serializers.PrimaryKeyRelatedField(
        required=False,
        many=True,
        queryset=Permission.objects.all(),
        source="permissions",
    )

    class Meta:
        model = Group
        fields = ["id", "name", "permissions", "permissions_id"]

    def create(self, validated_data):
        with transaction.atomic():
            permissions = validated_data.pop("permissions", None)
            role = Group.objects.create(**validated_data)
            if permissions:
                role.permissions.set(permissions)
            return role

    def update(self, instance, validated_data):
        with transaction.atomic():
            permissions = validated_data.pop("permissions_id", None)
            instance = super(RoleSerializer, self).update(instance, validated_data)
            if permissions:
                instance.permissions.clear()
                instance.permissions.set(permissions)
            return instance


class OrganizationSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    class Meta:
        model = Organization
        fields = "__all__"


class FeeSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    class Meta:
        model = Fee
        fields = "__all__"

    def create(self, validated_data):
        with transaction.atomic():
            default = validated_data["default"]

            if default:
                fees = Fee.objects.filter(default=True)
                if fees.exists():
                    fees.update(default=False)
            fee = Fee.objects.create(**validated_data)
            return fee

    def update(self, instance, validated_data):
        with transaction.atomic():
            instance = super(FeeSerializer, self).update(instance, validated_data)

            if instance.default:
                Fee.objects.filter(default=True).exclude(id=instance.id).update(
                    default=False
                )

            return instance


class UserMinimalSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True, allow_blank=True, allow_null=True)
    profile_photo = serializers.ImageField(read_only=True)
    full_name = serializers.SerializerMethodField()
    is_active = serializers.BooleanField(default=True, required=False)
    phone_number = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=None
    )

    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "full_name",
            "email",
            "address",
            "dni",
            "phone_number",
            "profile_photo",
            "is_staff",
            "is_active",
            "verified",
            "whatsapp_chat_id",
            "next_login_change_password",
            "newsletter",
            "date_joined",
        ]

    def get_full_name(self, obj) -> str:
        return f"{obj.first_name} {obj.last_name}"


class EmployeeSerializer(UserMinimalSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_

    Returns:
        _type_: _description_
    """

    email = serializers.EmailField(required=True, allow_blank=False, allow_null=False)
    groups = serializers.SerializerMethodField()
    groups_id = serializers.PrimaryKeyRelatedField(
        required=True, many=True, queryset=Group.objects.all(), source="groups"
    )

    class Meta:
        model = User
        fields = UserMinimalSerializer.Meta.fields + [
            "is_superuser",
            "is_deliverer",
            "groups",
            "groups_id",
        ]

    def get_groups(self, obj) -> list:
        groups = obj.groups.all()
        roles = []
        for group in groups:
            permissions = group.permissions.all()
            permissions_role = []
            for permission in permissions:
                permissions_role.append(permission.codename)
            roles.append({"role": group.name, "permissions": permissions_role})
        return roles

    def create(self, validated_data):
        with transaction.atomic():
            groups = validated_data.pop("groups", None)
            user = User.objects.create(**validated_data)
            if groups:
                user.groups.set(groups)
            password = password_generator.generate()
            user.set_password(password)
            user.next_login_change_password = True
            user.check_terms_conditions = True
            user.check_privacy_policy = True
            user.save()
            Wallet.objects.create(user=user)
            return user

    def update(self, instance, validated_data):
        with transaction.atomic():
            groups = validated_data.pop("groups_id", None)
            instance = super(EmployeeSerializer, self).update(instance, validated_data)
            if groups:
                instance.groups.clear()
                instance.groups.set(groups)
            return instance


class UserSerializer(UserMinimalSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_

    Returns:
        _type_: _description_
    """

    fee = FeeSerializer(read_only=True)
    fee_id = serializers.PrimaryKeyRelatedField(
        required=False, queryset=Fee.objects.all(), source="fee"
    )
    organization = OrganizationSerializer(read_only=True)
    organization_id = serializers.PrimaryKeyRelatedField(
        required=False, queryset=Organization.objects.all(), source="organization"
    )

    class Meta:
        model = User
        fields = UserMinimalSerializer.Meta.fields + [
            "fee",
            "fee_id",
            "organization",
            "organization_id",
        ]

    def create(self, validated_data):
        with transaction.atomic():
            password = validated_data.pop("password", None)
            user = User.objects.create(**validated_data)
            if password:
                user.set_password(password)
            user.next_login_change_password = False
            user.check_terms_conditions = True
            user.check_privacy_policy = True
            user.is_staff = False
            user.save()
            Wallet.objects.create(user=user)
            return user


class EmployeeRegisterSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_

    Returns:
        _type_: _description_
    """

    email = serializers.EmailField(required=True, allow_blank=False, allow_null=False)
    groups = serializers.ListField(required=False, write_only=True)
    phone_number = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=None
    )

    class Meta:
        model = User
        fields = [
            "email",
            "dni",
            "address",
            "first_name",
            "last_name",
            "phone_number",
            "groups",
            "date_joined",
        ]

    def create(self, validated_data):
        instance = super(EmployeeRegisterSerializer, self).create(validated_data)
        password = password_generator.generate()
        instance.set_password(password)
        instance.next_login_change_password = True
        instance.is_staff = True
        instance.is_active = False
        instance.check_terms_conditions = True
        instance.check_privacy_policy = True
        instance.save()
        Wallet.objects.create(user=instance)
        config_settings = Config.objects.get()
        context = {
            "logo": self.context.get("request").build_absolute_uri(
                f"{MEDIA_URL}{config_settings.logo_light}"
            ),
            "password": password,
            "user_name": f"{instance.first_name} {instance.last_name}",
            "business_name": config_settings.business_name,
            "frontend_url": config_settings.login_url,
        }
        message = get_template("mailing/staff_welcome.html").render(context)
        send_mail(
            [instance.email],
            "Bienvenido a la plataforma de ventas FEROS GRUPO S.U.R.L.A",
            message,
        )
        return instance

    def save(self, **kwargs):
        with transaction.atomic():
            user = super(EmployeeRegisterSerializer, self).save(**kwargs)
            return user


class UserRegisterSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_

    Returns:
        _type_: _description_
    """

    email = serializers.EmailField(required=True, allow_blank=False, allow_null=False)
    fee = FeeSerializer(read_only=True)
    fee_id = serializers.PrimaryKeyRelatedField(
        required=False, queryset=Fee.objects.all(), source="fee", allow_null=True
    )
    check_terms_conditions = serializers.BooleanField(required=True)
    check_privacy_policy = serializers.BooleanField(required=True)
    phone_number = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=None
    )

    def validate(self, attrs):
        if not attrs.get("check_terms_conditions"):
            raise serializers.ValidationError(
                _("You must accept the terms and conditions")
            )
        if not attrs.get("check_privacy_policy"):
            raise serializers.ValidationError(_("You must accept the privacy policy"))
        return attrs

    class Meta:
        model = User
        fields = [
            "email",
            "dni",
            "password",
            "first_name",
            "last_name",
            "phone_number",
            "fee",
            "fee_id",
            "date_joined",
            "newsletter",
            "check_terms_conditions",
            "check_privacy_policy",
        ]

    def create(self, validated_data):
        user = super(UserRegisterSerializer, self).create(validated_data)
        password = validated_data.get("password")
        user.set_password(password)
        user.is_active = False
        user.fee = Fee.objects.filter(default=True).first()
        user.save()
        Wallet.objects.create(user=user)

        Token.objects.filter(user=user).delete()
        token = Token.objects.create(user=user)

        config_settings = Config.objects.get()
        client_confirm_register_url = (
            f"{config_settings.confirm_register_url}/{str(token)}"
        )
        context = {
            "logo": self.context.get("request").build_absolute_uri(
                f"{MEDIA_URL}{config_settings.logo_light}"
            ),
            "user_name": f"{user.first_name} {user.last_name}",
            "business_name": config_settings.business_name,
            "confirm_url": client_confirm_register_url,
        }
        message = get_template("mailing/clients_welcome.html").render(context)
        send_mail(
            [user.email],
            "Bienvenido a la plataforma de ventas FEROS GRUPO S.U.R.L.",
            message,
        )
        return user

    def save(self, **kwargs):
        with transaction.atomic():
            user = super(UserRegisterSerializer, self).save(**kwargs)
            return user


class ChangePasswordSerializer(serializers.Serializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)


class RecoverPasswordSerializer(serializers.Serializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    email = serializers.CharField(required=True)


class ChangeRecoverPasswordSerializer(serializers.Serializer):
    """
    Serializer for password recovery change process
    """

    token = serializers.CharField(required=True, min_length=1)
    new_password = serializers.CharField(
        required=True, min_length=6, write_only=True, style={"input_type": "password"}
    )

    def validate_new_password(self, value):
        """
        Password validation
        """
        if len(value) < 6:
            raise serializers.ValidationError(
                _("The password must be at least 6 characters long.")
            )
        return value


class ConfirmRegisterSerializer(serializers.Serializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    token = serializers.CharField(required=True)


class UserProfileSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_

    Returns:
        _type_: _description_
    """

    email = serializers.CharField(read_only=True)
    groups = serializers.SerializerMethodField()
    profile_photo = serializers.ImageField(read_only=True)
    profile_photo_file = serializers.ImageField(
        write_only=True, source="profile_photo", required=False
    )
    fee = FeeSerializer(read_only=True)
    fee_id = serializers.PrimaryKeyRelatedField(
        required=False, source="fee", read_only=True
    )
    organization = OrganizationSerializer(read_only=True)
    organization_id = serializers.PrimaryKeyRelatedField(
        required=False, read_only=True, source="organization"
    )
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "dni",
            "address",
            "profile_photo",
            "profile_photo_file",
            "first_name",
            "last_name",
            "full_name",
            "is_staff",
            "is_deliverer",
            "phone_number",
            "newsletter",
            "check_terms_conditions",
            "check_privacy_policy",
            "verified",
            "whatsapp_chat_id",
            "next_login_change_password",
            "groups",
            "fee",
            "fee_id",
            "organization",
            "organization_id",
            "date_joined",
        ]

    def get_groups(self, obj) -> list:
        groups = obj.groups.all()
        roles = []
        for group in groups:
            permissions = group.permissions.all()
            permissions_role = []
            for permission in permissions:
                permissions_role.append(permission.codename)
            roles.append({"role": group.name, "permissions": permissions_role})
        return roles

    def get_full_name(self, obj) -> str:
        return f"{obj.first_name} {obj.last_name}"


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login authentication
    """

    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    token = serializers.CharField(read_only=True)
    user = UserProfileSerializer(read_only=True)

    def validate(self, data):
        """
        Validate user credentials and return user data with token
        """
        email = data.get("email")
        password = data.get("password")

        try:
            user = User.objects.get(email=email)

            if not user.check_password(password):
                raise NotMatchException()

            if not user.verified:
                raise UserNotVerifiedException()

            if not user.is_active:
                raise UserNotActiveException()

            with transaction.atomic():
                Token.objects.filter(user=user).delete()
                token = Token.objects.create(user=user)

            user.last_login = now()
            user.save(update_fields=["last_login"])
            return {
                "token": token.key,
                "user": UserProfileSerializer(user, context=self.context).data,
            }

        except User.DoesNotExist as exception:
            raise NotMatchException() from exception


class EventLogSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        allow_null=True,
        required=False,
        queryset=User.objects.all(),
        source="user",
    )

    class Meta:
        model = EventLog
        fields = [
            "id",
            "action",
            "description",
            "raised_date",
            "user",
            "user_id",
        ]
