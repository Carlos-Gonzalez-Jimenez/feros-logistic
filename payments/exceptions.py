from rest_framework.exceptions import APIException
from rest_framework import status
from django.utils.translation import gettext_lazy as _


class NotSoportedPaymentMethodException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Payment method not soported")
    default_code = "payment_method_not_soported"


class InsufficientWalletBalanceException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Insufficient wallet balance")
    default_code = "insufficient_wallet_balance"


class WalletDoesNotExistException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Wallet does not exist")
    default_code = "wallet_does_not_exist"


class OrderPaymentDoesNotExistException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Order payment does not exist")
    default_code = "order_payment_does_not_exist"


class PaymentNotCompletedException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Payment not completed")
    default_code = "payment_not_completed"
