from rest_framework import status
from rest_framework.exceptions import APIException
from django.utils.translation import gettext_lazy as _


class NotMatchException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("User does not exist")
    default_code = "user_not_match"


class UserNotVerifiedException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("User not verified")
    default_code = "user_not_verified"


class UserNotActiveException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("User not active")
    default_code = "user_not_active"


class UserNotStaffException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("User not staff")
    default_code = "user_not_staff"


class UserNotDelivererException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("User not deliverer")
    default_code = "user_not_deliverer"


class UserNotClientException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("User not client")
    default_code = "user_not_client"


class VerificationCodeNotSentException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Error sending verification code")
    default_code = "verification_code_not_sent"


class UserVerificationCodeNotExistException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("User - Verification code does not exist")
    default_code = "user_verification_code_not_exist"


class VerificationCodeExpiredException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Verification code expired")
    default_code = "verification_code_expired"


class WrongPasswordException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Wrong password")
    default_code = "wrong_password"


class InvalidTokenException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Invalid token")
    default_code = "invalid_token"


class TokenExpiredException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Token expired")
    default_code = "token_expired"


class UserAlreadyVerifiedException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("User already verified")
    default_code = "user_already_verified"
