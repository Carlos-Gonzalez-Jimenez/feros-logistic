import datetime

from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.permissions import (
    CustomPermissionFactory,
    ReadOnlyPermission,
)
from core.views import ProtectedResourceViewSet
from dashboard.exceptions import StartDateCanNotBeAfterEnddateException
from payments import filters, models, serializers
from payments.exceptions import (
    InsufficientWalletBalanceException,
    WalletDoesNotExistException,
)
from payments.services import PaymentFactory


class WalletViewSet(ProtectedResourceViewSet):
    """
    Wallet model\n
    GET: Shows all Wallets created.\n
    POST: Adds a new Wallet.\n
    GET{id}: Retrieves a specific Wallet determined by id.\n
    PUT{id}: Modifies all fields of a specific Wallet determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific Wallet determined by id.\n
    DELETE{id}: Deletes a specific Wallet determined by id.\n
    """

    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["payments.manage_payments"])
    ]
    queryset = models.Wallet.objects.all()
    serializer_class = serializers.WalletSerializer

    @action(detail=False, methods=["post"], url_path="deposit")
    def deposit(self, request):
        operator = self.request.user
        with transaction.atomic():
            serializer = serializers.DepositSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                user = serializer.validated_data["user_id"]
                currency = serializer.validated_data["currency_id"]
                amount = serializer.validated_data["amount"]
                description = serializer.validated_data.get("description", None)

                try:
                    wallet = models.Wallet.objects.get(user_id=user.id)
                except models.Wallet.DoesNotExist as exception:
                    raise WalletDoesNotExistException() from exception

                previous_amount = wallet.amount
                current_exchange_rate = currency.exchange_rate
                current_exchange_rate_date = currency.exchange_rate_date
                currency_amount = amount / current_exchange_rate

                models.WalletOperationalLog.objects.create(
                    transaction_id=f"DEPOSITO_{currency.initials}_{amount}",
                    description=description,
                    amount=currency_amount,
                    previous_amount=previous_amount,
                    exchange_rate=current_exchange_rate,
                    exchange_rate_date=current_exchange_rate_date,
                    wallet=wallet,
                    currency=currency,
                    charge_for=operator,
                )

                wallet.amount += currency_amount
                wallet.save()

                return Response(
                    serializers.WalletSerializer(
                        wallet,
                        context={"request": request},
                    ).data,
                    status=status.HTTP_200_OK,
                )

    @action(detail=False, methods=["post"], url_path="withdraw")
    def withdraw(self, request):
        operator = self.request.user
        with transaction.atomic():
            serializer = serializers.WithdrawalSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                user = serializer.validated_data["user_id"]
                currency = serializer.validated_data["currency_id"]
                amount = serializer.validated_data["amount"]
                description = serializer.validated_data.get("description", None)

                try:
                    wallet = models.Wallet.objects.get(user_id=user.id)
                except models.Wallet.DoesNotExist as exception:
                    raise WalletDoesNotExistException() from exception

                previous_amount = wallet.amount
                current_exchange_rate = currency.exchange_rate
                current_exchange_rate_date = currency.exchange_rate_date
                currency_amount = amount / current_exchange_rate
                if wallet.amount < currency_amount:
                    raise InsufficientWalletBalanceException()
                wallet.amount -= currency_amount
                wallet.save()
                models.WalletOperationalLog.objects.create(
                    transaction_id=f"RETIRO_{currency.initials}_{round(amount, 2)}",
                    description=description,
                    amount=currency_amount,
                    previous_amount=previous_amount,
                    exchange_rate=current_exchange_rate,
                    exchange_rate_date=current_exchange_rate_date,
                    wallet=wallet,
                    currency=currency,
                    charge_for=operator,
                )

                return Response(
                    serializers.WalletSerializer(
                        wallet,
                        context={"request": request},
                    ).data,
                    status=status.HTTP_200_OK,
                )


class TransactionLogViewSet(ProtectedResourceViewSet):
    """
    Transaction Log model\n
    GET: Shows all Transaction Log created.\n
    POST: Adds a new Transaction Log.\n
    GET{id}: Retrieves a specific Transaction Log determined by id.\n
    PUT{id}: Modifies all fields of a specific Transaction Log determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific Transaction Log determined by id.\n
    DELETE{id}: Deletes a specific Transaction Log determined by id.\n
    """

    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["payments.manage_payments"]),
    ]
    queryset = models.TransactionLog.objects.all()
    serializer_class = serializers.TransactionLogSerializer


class PaymentMethodViewSet(ProtectedResourceViewSet):
    """
    Payment Method model\n
    GET: Shows all Payment Methods created.\n
    POST: Adds a new Payment Method.\n
    GET{id}: Retrieves a specific Payment Method determined by id.\n
    PUT{id}: Modifies all fields of a specific Payment Method determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific Payment Method determined by id.\n
    DELETE{id}: Deletes a specific Payment Method determined by id.\n
    """

    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["payments.manage_payments"]),
    ]
    queryset = models.PaymentMethod.objects.all()
    serializer_class = serializers.PaymentMethodSerializer
    filterset_class = filters.PaymentMethodFilter
    search_fields = ["name"]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(active=True)


class PaymentViewSet(ProtectedResourceViewSet):
    """
    Payment model\n
    GET: Shows all Payments created.\n
    POST: Adds a new Payment.\n
    GET{id}: Retrieves a specific Payment determined by id.\n
    PUT{id}: Modifies all fields of a specific Payment determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific Payment determined by id.\n
    DELETE{id}: Deletes a specific Payment determined by id.\n
    """

    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["payments.manage_payments"]),
    ]
    queryset = models.Payment.objects.all()
    serializer_class = serializers.PaymentSerializer
    http_method_names = ["get", "post", "delete", "head", "options"]

    @action(detail=True, methods=["get"], url_path="transfermovil-data")
    def transfermovil(self, request, pk=None):
        payment = models.Payment.objects.get(id=pk)
        return Response(
            serializers.TransfermovilPaymentSerializer(
                payment, context=self.get_serializer_context()
            ).data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["post"],
        url_path="callback",
        permission_classes=[AllowAny],
    )
    def callback(self, request, pk=None):
        """SE USA POR LA PASARELA DE PAGO PARA RECIBIR CONFIRMACION (WEBHOOK) Y RESPONDE CON LO NECESARIO PARA LA PASARELA"""
        payment = get_object_or_404(
            models.Payment, order_id=pk
        )  # TODO REVISAR ESTO PORQUE UNA ORDEN TIENE VARIOS PAGOS
        service = PaymentFactory.create_payment_service(
            payment.payment_method.code_name
        )
        response = service.callback_payment(payment, request.data)
        return Response(**response)

    @action(
        detail=True,
        methods=["post"],
        url_path="check-status",
        permission_classes=[CustomPermissionFactory(["payments.manage_payments"])],
    )
    def check_status(self, request, pk):
        payment = get_object_or_404(models.Payment, pk=pk)
        service = PaymentFactory.create_payment_service(
            payment.payment_method.code_name
        )
        service.check_payment_status(payment, request.user)
        payment.refresh_from_db(fields=["status"])
        return Response(self.get_serializer(instance=payment).data)


class PaymentReportViewSet(GenericAPIView):
    serializer_class = serializers.PaymentReportSerializer

    def get(self, request):

        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        start_date = serializer.validated_data.get("start_date")
        end_date = serializer.validated_data.get("end_date")
        payment_method = serializer.validated_data.get("payment_method_id")

        if start_date > end_date:
            raise StartDateCanNotBeAfterEnddateException

        filters = {
            "status": models.Payment.PaymentStatus.Completed,
            "updated_at__range": [start_date, end_date + datetime.timedelta(days=1)],
        }
        if payment_method is not None:
            filters["payment_method"] = payment_method

        payments = models.Payment.objects.filter(**filters).order_by(
            "created_at", "order__id"
        )

        return Response(
            {
                "payments": serializers.ConciliationPaymentSerializer(
                    payments, many=True
                ).data,
                "total_amount": payments.aggregate(total_amount=Sum("amount"))[
                    "total_amount"
                ],
            }
        )


class WalletOperationalLogsViewSet(ProtectedResourceViewSet):
    """
    Wallet Operational Log model\n
    GET: Shows all Wallet Operational Logs created.\n
    POST: Adds a new Wallet Operational Log.\n
    GET{id}: Retrieves a specific Wallet Operational Log determined by id.\n
    PUT{id}: Modifies all fields of a specific Wallet Operational Log determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific Wallet Operational Log determined by id.\n
    DELETE{id}: Deletes a specific Wallet Operational Log determined by id.\n
    """

    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["payments.manage_payments"]),
    ]
    queryset = models.WalletOperationalLog.objects.all()
    serializer_class = serializers.WalletOperationalLogSerializer
    http_method_names = ["get", "post", "delete", "head", "options"]
