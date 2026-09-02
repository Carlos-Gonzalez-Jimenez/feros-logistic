from decimal import Decimal
from dateutil.utils import today
from rest_framework import viewsets, status
from rest_framework.generics import (
    RetrieveUpdateAPIView,
    CreateAPIView,
)
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from user.exceptions import (
    NotMatchException,
    WrongPasswordException,
    UserNotVerifiedException,
    UserNotClientException,
    InvalidTokenException,
    TokenExpiredException,
    UserNotDelivererException,
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
from core.views import ProtectedResourceViewSet
from user import models, serializers
from core.models import Order, ContactAddress, Config, OrderTracking, OrderStatus
from core.serializers import (
    OrderSerializer,
    ContactAddressSerializer,
    OrderMinimalSerializer,
)
from user.filters import UserFilter, EventLogFilter
from django.contrib.auth.models import Group, Permission
from .tasks import send_mail
from core.permissions import (
    CustomPermissionFactory,
    ReadOnlyPermission,
    ClientPermission,
)
from core.services import WAHAService
from .tasks import send_mail, password_generator
from logistic_backend.settings import MEDIA_URL
from payments.models import Wallet, WalletOperationalLog
from payments.serializers import WalletOperationalLogSerializer, WalletSerializer
from payments.exceptions import WalletDoesNotExistException
from delivery.models import OrderShipping, ShippingZone
from promotions.models import CouponAssignment
from promotions.serializers import (
    ClientCouponAssignmentSerializer,
)
from django.db.models import Q, OuterRef, Subquery
from core.tasks import NomenclatorCacheManager
from core import filters


class OrganizationViewSet(ProtectedResourceViewSet):
    """
    Organization model\n
    GET: Shows all Organizations created.\n
    POST: Adds a new Organization.\n
    GET{id}: Retrieves a specific Organization determined by id.\n
    PUT{id}: Modifies all fields of a specific Organization determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific Organization determined by id.\n
    DELETE{id}: Deletes a specific Organization determined by id.\n
    """

    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["user.manage_organization"]),
    ]
    queryset = models.Organization.objects.all()
    serializer_class = serializers.OrganizationSerializer
    search_fields = ["name"]

    def list(self, request, *args, **kwargs):
        page = request.query_params.get("page")
        page_size = request.query_params.get("page_size")
        search_term = request.query_params.get("search", "")

        if search_term and search_term.strip():
            return super().list(request, *args, **kwargs)

        cache_kwargs = {"page": page, "page_size": page_size, "search": search_term}

        cached_data = NomenclatorCacheManager.get_cached_data(
            "organization", "list", request.user, **cache_kwargs
        )

        if cached_data is not None:
            return Response(cached_data)

        response = super().list(request, *args, **kwargs)

        if response.status_code == 200:
            NomenclatorCacheManager.set_cached_data(
                response.data,
                "organization",
                "list",
                request.user,
                timeout=60 * 60 * 24 * 7,
                **cache_kwargs,
            )

        return response

    def retrieve(self, request, *args, **kwargs):
        cached_data = NomenclatorCacheManager.get_cached_data(
            "organization", "retrieve", request.user, kwargs.get("pk")
        )

        if cached_data is not None:
            return Response(cached_data)

        response = super().retrieve(request, *args, **kwargs)

        if response.status_code == 200:
            NomenclatorCacheManager.set_cached_data(
                response.data,
                "organization",
                "retrieve",
                request.user,
                pk=kwargs.get("pk"),
                timeout=60 * 60 * 24 * 30,
            )

        return response

    def perform_create(self, serializer):
        NomenclatorCacheManager.invalidate_model_cache("organization")
        response = super().perform_create(serializer)
        return response

    def perform_update(self, serializer):
        NomenclatorCacheManager.invalidate_model_cache("organization")
        response = super().perform_update(serializer)
        return response

    def perform_destroy(self, instance):
        NomenclatorCacheManager.invalidate_model_cache("organization")
        response = super().perform_destroy(instance)
        return response


class FeeViewSet(ProtectedResourceViewSet):
    """
    Fee model\n
    GET: Shows all Fees created.\n
    POST: Adds a new Fee.\n
    GET{id}: Retrieves a specific Fee determined by id.\n
    PUT{id}: Modifies all fields of a specific Fee determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific Fee determined by id.\n
    DELETE{id}: Deletes a specific Fee determined by id.\n
    """

    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["user.manage_fee"]),
    ]
    queryset = models.Fee.objects.all()
    serializer_class = serializers.FeeSerializer
    search_fields = ["name"]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(active=True)

    def list(self, request, *args, **kwargs):
        page = request.query_params.get("page")
        page_size = request.query_params.get("page_size")
        search_term = request.query_params.get("search", "")

        if search_term and search_term.strip():
            return super().list(request, *args, **kwargs)

        cache_kwargs = {"page": page, "page_size": page_size, "search": search_term}

        cached_data = NomenclatorCacheManager.get_cached_data(
            "fee", "list", request.user, **cache_kwargs
        )

        if cached_data is not None:
            return Response(cached_data)

        response = super().list(request, *args, **kwargs)

        if response.status_code == 200:
            NomenclatorCacheManager.set_cached_data(
                response.data,
                "fee",
                "list",
                request.user,
                timeout=60 * 60 * 24 * 7,
                **cache_kwargs,
            )

        return response

    def retrieve(self, request, *args, **kwargs):
        cached_data = NomenclatorCacheManager.get_cached_data(
            "fee", "retrieve", request.user, kwargs.get("pk")
        )

        if cached_data is not None:
            return Response(cached_data)

        response = super().retrieve(request, *args, **kwargs)

        if response.status_code == 200:
            NomenclatorCacheManager.set_cached_data(
                response.data,
                "fee",
                "retrieve",
                request.user,
                pk=kwargs.get("pk"),
                timeout=60 * 60 * 24 * 30,
            )

        return response

    def perform_create(self, serializer):
        NomenclatorCacheManager.invalidate_model_cache("fee")
        response = super().perform_create(serializer)
        return response

    def perform_update(self, serializer):
        NomenclatorCacheManager.invalidate_model_cache("fee")
        response = super().perform_update(serializer)
        return response

    def perform_destroy(self, instance):
        NomenclatorCacheManager.invalidate_model_cache("fee")
        response = super().perform_destroy(instance)
        return response


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
            "delivery",
            "payments",
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

    def list(self, request, *args, **kwargs):
        page = request.query_params.get("page")
        page_size = request.query_params.get("page_size")
        search_term = request.query_params.get("search", "")

        if search_term and search_term.strip():
            return super().list(request, *args, **kwargs)

        cache_kwargs = {"page": page, "page_size": page_size, "search": search_term}

        cached_data = NomenclatorCacheManager.get_cached_data(
            "role", "list", request.user, **cache_kwargs
        )

        if cached_data is not None:
            return Response(cached_data)

        response = super().list(request, *args, **kwargs)

        if response.status_code == 200:
            NomenclatorCacheManager.set_cached_data(
                response.data,
                "role",
                "list",
                request.user,
                timeout=60 * 60 * 24 * 7,
                **cache_kwargs,
            )

        return response

    def retrieve(self, request, *args, **kwargs):
        cached_data = NomenclatorCacheManager.get_cached_data(
            "role", "retrieve", request.user, kwargs.get("pk")
        )

        if cached_data is not None:
            return Response(cached_data)

        response = super().retrieve(request, *args, **kwargs)

        if response.status_code == 200:
            NomenclatorCacheManager.set_cached_data(
                response.data,
                "role",
                "retrieve",
                request.user,
                pk=kwargs.get("pk"),
                timeout=60 * 60 * 24 * 30,
            )

        return response

    def perform_create(self, serializer):
        NomenclatorCacheManager.invalidate_model_cache("role")
        response = super().perform_create(serializer)
        return response

    def perform_update(self, serializer):
        NomenclatorCacheManager.invalidate_model_cache("role")
        response = super().perform_update(serializer)
        return response

    def perform_destroy(self, instance):
        NomenclatorCacheManager.invalidate_model_cache("role")
        response = super().perform_destroy(instance)
        return response


class RegisterEmployeeAPIView(CreateAPIView):
    """
    Register a new employee
    """

    serializer_class = serializers.EmployeeRegisterSerializer
    permission_classes = [CustomPermissionFactory(["user.manage_user"])]


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
                        {
                            "message": "Se ha enviado un enlace de recuperación a su correo"
                        },
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


class EmployeeViewSet(viewsets.ModelViewSet):
    """
    User model\n
    GET: Shows all employees created.\n
    POST: Adds a new employee.\n
    GET{id}: Retrieves a specific employee determined by id.\n
    PUT{id}: Modifies all fields of a specific employee determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific employee determined by id.\n
    DELETE{id}: Deletes a specific employee determined by id.\n
    """

    permission_classes = [
        ReadOnlyPermission
        | CustomPermissionFactory(
            [
                "user.manage_user",
            ]
        )
    ]
    queryset = models.User.objects.filter(is_staff=True)
    serializer_class = serializers.EmployeeSerializer
    filterset_class = UserFilter
    search_fields = ["first_name", "last_name", "email", "phone_number"]

    @action(
        detail=True,
        methods=["get"],
        url_path=r"deliverable-orders",
        queryset=models.User.objects.filter(is_deliverer=True).all(),
        permission_classes=[CustomPermissionFactory(["delivery.manage_delivery"])],
    )
    def deliverable_orders(self, request, pk=None):
        user = self.get_object()
        latest_tracking = (
            OrderTracking.objects.filter(order=OuterRef("pk"))
            .order_by("-id")
            .values("status__code_name")[:1]
        )
        deliverer_zones = ShippingZone.objects.filter(deliverers=user, active=True)
        orders = (
            Order.objects.annotate(latest_status=Subquery(latest_tracking))
            .filter(
                shipping__isnull=False, shipping__deliverer__isnull=True,
                shipping__shipping_rate__shipping_zone__in=deliverer_zones,
                latest_status="ready_shipping",
            )
        )

        return Response(OrderSerializer(orders, many=True).data, status.HTTP_200_OK)

    @action(
        detail=True,
        methods=["get"],
        url_path=r"non-completed-orders",
        queryset=models.User.objects.filter(is_deliverer=True, is_active=True).all(),
        permission_classes=[
            CustomPermissionFactory(
                ["delivery.manage_delivery", "user.can_deliver_orders"]
            )
        ],
    )
    def user_non_completed_orders(self, request, pk=None):
        user = self.get_object()
        shipping_order_ids = OrderShipping.objects.filter(
            deliverer_id=user.id
        ).values_list("order_id", flat=True)
        latest_tracking = (
            OrderTracking.objects.filter(order=OuterRef("pk"))
            .order_by("-id")
            .values("status__code_name")[:1]
        )
        non_completed_orders = (
            Order.objects.filter(id__in=shipping_order_ids)
            .annotate(latest_status=Subquery(latest_tracking))
            .exclude(latest_status__in=["completed", "cancelled", "returned"])
        )
        return Response(
            OrderSerializer(non_completed_orders, many=True).data,
            status.HTTP_200_OK,
        )


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
        ReadOnlyPermission | CustomPermissionFactory(["user.manage_customer"]),
    ]
    queryset = models.User.objects.filter(is_staff=False)
    serializer_class = serializers.UserSerializer
    search_fields = ["first_name", "last_name", "email", "phone_number"]

    @action(
        detail=True,
        methods=["get"],
        url_path=r"orders",
        permission_classes=[
            ClientPermission | CustomPermissionFactory(["user.show_customer_orders"])
        ],
    )
    def user_orders(self, request, pk=None):
        user = self.get_object()
        if user.is_staff:
            raise UserNotClientException()
        orders = filters.OrderFilter(
            data=request.GET,
            queryset=Order.objects.filter(client_id=user.id, merge__isnull=True),
        ).qs
        paginated = self.paginate_queryset(orders)
        orders = OrderMinimalSerializer(
            paginated, many=True, context=self.get_serializer_context()
        ).data
        return self.get_paginated_response(orders)

    @action(
        detail=True,
        methods=["get"],
        url_path=r"addresses",
        permission_classes=[
            ClientPermission | CustomPermissionFactory(["user.manage_customer"])
        ],
    )
    def user_addresses(self, request, pk=None):
        user = self.get_object()
        if user.is_staff:
            raise UserNotClientException()
        addresses = ContactAddress.objects.filter(user_id=user.id)
        return Response(
            ContactAddressSerializer(addresses, many=True).data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["get"],
        url_path=r"operational-logs",
        permission_classes=[
            ClientPermission | CustomPermissionFactory(["user.manage_customer"])
        ],
    )
    def operational_logs(self, request, pk=None):
        user = self.get_object()
        if user.is_staff:
            raise UserNotClientException()
        try:
            wallet = Wallet.objects.get(user_id=user.id)
        except Wallet.DoesNotExist as exception:
            raise WalletDoesNotExistException() from exception

        operational_logs = WalletOperationalLog.objects.filter(wallet=wallet).order_by(
            "-created_at"
        )
        paginated = self.paginate_queryset(operational_logs)
        logs = WalletOperationalLogSerializer(
            paginated, many=True, context=self.get_serializer_context()
        ).data
        return self.get_paginated_response(logs)

    @action(
        detail=True,
        methods=["get"],
        url_path=r"wallet",
        permission_classes=[
            ClientPermission | CustomPermissionFactory(["user.show_customer_wallet"])
        ],
    )
    def client_wallet(self, request, pk=None):
        user = self.get_object()
        if user.is_staff:
            raise UserNotClientException()
        try:
            wallet = Wallet.objects.get(user_id=user.id)
        except Wallet.DoesNotExist as exception:
            raise WalletDoesNotExistException() from exception

        return Response(WalletSerializer(wallet).data, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=["get"],
        url_path=r"coupons",
        permission_classes=[
            ClientPermission | CustomPermissionFactory(["user.show_customer_coupons"])
        ],
    )
    def client_coupons(self, request, pk=None):
        user = self.get_object()
        if user.is_staff:
            raise UserNotClientException()

        coupons = CouponAssignment.objects.filter(user_id=user.id)

        return Response(
            ClientCouponAssignmentSerializer(
                coupons, many=True, context={"request": request}
            ).data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["get"],
        url_path=r"unpaid-orders",
        permission_classes=[
            ClientPermission
            | CustomPermissionFactory(["user.show_customer_unpaid_orders"])
        ],
    )
    def user_unpaid_orders(self, request, pk=None):
        user = self.get_object()
        if user.is_staff:
            raise UserNotClientException()
        last_status_code = Subquery(
            OrderTracking.objects.filter(order=OuterRef('pk')).order_by('-id').values('status__code_name')[:1]
        )
        orders = (
            Order.objects.filter(
                client_id=user.id,
                merge__isnull=True,
                pending_amount__gt=0,
            )
            .annotate(last_status_code=Subquery(last_status_code))
            .exclude(last_status_code__in=['cancelled', 'returned'])
        )
        paginated = self.paginate_queryset(orders)
        orders = OrderMinimalSerializer(
            paginated, many=True, context=self.get_serializer_context()
        ).data
        return self.get_paginated_response(orders)


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
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )

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
