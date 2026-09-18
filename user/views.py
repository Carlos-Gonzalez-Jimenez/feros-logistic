from decimal import Decimal
from dateutil.utils import today
from rest_framework import viewsets, status
from rest_framework.generics import (
    RetrieveUpdateAPIView,
    CreateAPIView,
)
from django.utils.translation import gettext_lazy as _
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from user.exceptions import (
    NotMatchException,
    WrongPasswordException,
    UserNotVerifiedException,
    InvalidTokenException,
    TokenExpiredException,
    UserNotActiveException,
)
from django.template.loader import get_template
from rest_framework.decorators import action
from django.utils import timezone
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
)
from django.db import transaction
from user import models, serializers
from core.models import Config
from user.filters import UserFilter, EventLogFilter
from django.contrib.auth.models import Group, Permission
from .tasks import send_mail
from core.permissions import (
    CustomPermissionFactory,
    ReadOnlyPermission,
)
from logistic_backend.settings import MEDIA_URL


class PermissionViewSet(viewsets.ModelViewSet):
    """
    GET: Shows all permissions created.\n
    POST: Adds a new permission.\n
    GET{id}: Retrieves a specific permission determined by id.\n
    PUT{id}: Modifies all fields of a specific permission determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific permission determined by id.\n
    DELETE{id}: Deletes a specific permission determined by id.\n
    """

    queryset = Permission.objects.filter(
        content_type__app_label__in=[
            "core",
            "user",
            "cms",
            "blog",
        ]
    )
    serializer_class = serializers.PermissionSerializer
    pagination_class = None


class RoleViewSet(viewsets.ModelViewSet):
    """
    GET: Shows all roles created.\n
    POST: Adds a new role.\n
    GET{id}: Retrieves a specific role determined by id.\n
    PUT{id}: Modifies all fields of a specific role determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific role determined by id.\n
    DELETE{id}: Deletes a specific role determined by id.\n
    """

    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["user.manage_role"]),
    ]
    queryset = Group.objects.all()
    serializer_class = serializers.RoleSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(active=True)


class RegisterUserAPIView(CreateAPIView):
    """
    Register a new client
    """

    serializer_class = serializers.UserRegisterSerializer
    permission_classes = [AllowAny]


class ChangePasswordView(APIView):
    """
    Sets a new password for the user given in the request.\n
    """

    permission_classes = [AllowAny]
    serializer_class = serializers.ChangePasswordSerializer

    def post(self, request):
        serializer = serializers.ChangePasswordSerializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            with transaction.atomic():
                user = request.user
                if user.check_password(serializer.validated_data["current_password"]):
                    user.set_password(serializer.validated_data["new_password"])
                    user.next_login_change_password = False
                    user.verified = True
                    user.is_active = True
                    user.save()
                    return Response(status=status.HTTP_204_NO_CONTENT)
                raise WrongPasswordException()


class ChangePasswordView(APIView):
    """
    Sets a new password for the user given in the request.\n
    """

    permission_classes = [IsAuthenticated]
    serializer_class = serializers.ChangePasswordSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        try:
            with transaction.atomic():
                if not serializer.is_valid():
                    return Response(
                        serializer.errors, status=status.HTTP_400_BAD_REQUEST
                    )

                user = request.user
                if user.check_password(serializer.validated_data["current_password"]):
                    user.set_password(serializer.validated_data["new_password"])
                    user.next_login_change_password = False
                    user.verified = True
                    user.is_active = True
                    user.save()
                    return Response(status=status.HTTP_204_NO_CONTENT)
                else:
                    raise WrongPasswordException()

        except WrongPasswordException:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class RecoverPasswordView(APIView):
    """
    Recover a forgotten password sending an email.\n
    Assuming the user has verified his verification code.\n
    """

    serializer_class = serializers.RecoverPasswordSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        try:
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                email = serializer.validated_data["email"]
                try:
                    user = models.User.objects.get(email=email)

                    if not user.verified:
                        raise UserNotVerifiedException()

                    config_settings = Config.objects.get()
                    recover_password_url = config_settings.recover_password_url

                    Token.objects.filter(user=user).delete()
                    token = Token.objects.create(user=user)

                    url = f"{recover_password_url}/{str(token)}"
                    context = {
                        "logo": request.build_absolute_uri(
                            f"{MEDIA_URL}{config_settings.logo_light}"
                        ),
                        "frontend_url": url,
                        "business_name": config_settings.business_name,
                    }
                    message = get_template("mailing/recover.html").render(context)
                    send_mail([email], "Recuperar contraseña", message)

                    return Response(
                        {"message": _("A recovery link has been sent to your email.")},
                        status=status.HTTP_200_OK,
                    )

                except models.User.DoesNotExist as exception:
                    raise NotMatchException() from exception

        except UserNotVerifiedException:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except NotMatchException:
            return Response(status=status.HTTP_200_OK)


class ChangeRecoverPasswordView(APIView):
    """
    Sets a new password for the recover password process.\n
    """

    serializer_class = serializers.ChangeRecoverPasswordSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid(raise_exception=True):
            with transaction.atomic():
                token = serializer.validated_data["token"]
                auth_tokens = Token.objects.filter(key=token)
                if auth_tokens.exists():
                    user_token = auth_tokens.first()
                    elapsed_time = int(
                        (
                                timezone.localtime(timezone.now()) - user_token.created
                        ).total_seconds()
                        / 60
                    )
                    config_settings = Config.objects.get()
                    if (
                            elapsed_time
                            <= config_settings.recover_password_token_validation_time
                    ):
                        user = models.User.objects.filter(id=user_token.user_id).first()
                        user.set_password(serializer.validated_data["new_password"])
                        user.save()
                        return Response(status=status.HTTP_200_OK)
                    else:
                        raise TokenExpiredException()
                raise InvalidTokenException()


class ChangeRecoverPasswordView(APIView):
    """
    Sets a new password for the recover password process.\n
    """

    serializer_class = serializers.ChangeRecoverPasswordSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        try:
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                token = serializer.validated_data["token"]

                try:
                    user_token = Token.objects.get(key=token)

                    elapsed_time = int(
                        (
                                timezone.localtime(timezone.now()) - user_token.created
                        ).total_seconds()
                        / 60
                    )

                    config_settings = Config.objects.get()

                    if (
                            elapsed_time
                            > config_settings.recover_password_token_validation_time
                    ):
                        user_token.delete()
                        raise TokenExpiredException()

                    user = user_token.user
                    user.set_password(serializer.validated_data["new_password"])
                    user.save()
                    user_token.delete()

                    return Response(
                        status=status.HTTP_200_OK,
                    )

                except Token.DoesNotExist as exception:
                    raise InvalidTokenException() from exception

        except TokenExpiredException:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except InvalidTokenException:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class ConfirmRegisterView(APIView):
    """
    Confirm register process. Set active and verified to True\n
    """

    serializer_class = serializers.ConfirmRegisterSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        try:
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                token = serializer.validated_data["token"]

                try:
                    user_token = Token.objects.get(key=token)
                    user = user_token.user

                    user.verified = True
                    user.is_active = True
                    user.save()
                    user_token.delete()

                    return Response(status=status.HTTP_200_OK)

                except Token.DoesNotExist as exception:
                    raise InvalidTokenException() from exception

        except InvalidTokenException:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class ProfileView(RetrieveUpdateAPIView):
    """
    User model.\n
    GET: Shows the profile of the authenticated user.\n
    PUT{id}: Modifies all fields of the authenticated user.\n
    PATCH{id}: Partially modifies the fields of the authenticated user.\n
    """

    permission_classes = [IsAuthenticated]
    serializer_class = serializers.UserProfileSerializer
    queryset = models.User.objects.all()

    def get_object(self):
        return self.request.user


class UserViewSet(viewsets.ModelViewSet):
    """
    User model\n
    GET: Shows all clients created.\n
    POST: Adds a new clients.\n
    GET{id}: Retrieves a specific client determined by id.\n
    PUT{id}: Modifies all fields of a specific client determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific client determined by id.\n
    DELETE{id}: Deletes a specific client determined by id.\n
    """

    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["user.manage_user"]),
    ]
    queryset = models.User.objects.all()
    serializer_class = serializers.UserSerializer
    search_fields = ["first_name", "last_name", "email", "phone_number"]


class EventLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    EventLog model\n
    GET: Shows all event logs created.\n
    POST: Adds a new event log.\n
    GET{id}: Retrieves a specific event log determined by id.\n
    PUT{id}: Modifies all fields of a specific event log determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific event log determined by id.\n
    DELETE{id}: Deletes a specific event log determined by id.\n
    """

    permission_classes = [ReadOnlyPermission]
    queryset = models.EventLog.objects.all()
    filterset_class = EventLogFilter
    serializer_class = serializers.EventLogSerializer
    search_fields = ["action", "description"]
    ordering = ["-raised_date"]


class LoginView(APIView):
    """
    Tries to log in a user into the app.\n
    In case the user - password combination doesn't match, it returns a 'NotMatchException' response.\n
    *If the user password combination matches:\n
        *If the user is not verified, returns a 'UserNotVerifiedException' response.\n
        *If the user is verified but not active, returns a 'UserNotActiveException' response.\n
        *If all the previous steps are ok returns an 'OK' response.\n
    """

    serializer_class = serializers.UserLoginSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={"request": request})

        try:
            if serializer.is_valid():
                return Response(serializer.validated_data, status.HTTP_200_OK)
            return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)

        except (NotMatchException, UserNotVerifiedException, UserNotActiveException):
            return Response(status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """
    Logs out a User and deletes the authentication token previously generated.
    This prevents multiple sessions.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = serializers.UserProfileSerializer

    def post(self, request):
        try:
            with transaction.atomic():
                Token.objects.filter(user=request.user).delete()

                return Response(status=status.HTTP_200_OK)

        except Exception:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
