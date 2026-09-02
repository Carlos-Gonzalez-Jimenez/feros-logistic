from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.exceptions import ValidationError

from rest_framework.views import exception_handler
from django.utils.translation import gettext_lazy as _


class ProtectedInstanceException(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = _("Resource protected")
    default_code = "protected_instance"


class InvalidParameterException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Invalid parameter, parameter should have value")
    default_code = "invalid_parameter"


class StatusNotAllowedException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Status not allowed")
    default_code = "invalid_parameter"


class ConfigurationDoesNotExistException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Configuration does not exist")
    default_code = "configuration_does_not_exist"


class ErrorContactingMessagingAPIException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Error contacting messaging API")
    default_code = "error_contacting_messaging_API"


class OrderUpdateException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Order can't be update")
    default_code = "invalid_operation"


class RollBackUnAvailableException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Order can't be rollback")
    default_code = "invalid_operation"


class StatusUnAvalaibleException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Current order status unavailable")
    default_code = "invalid_parameter"


class BatchItemIncompleteException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Batch items without product related")
    default_code = "batch_item_incomplete"


class ColumnRequiredException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Required column not found in the Excel file")
    default_code = "required_column"


def custom_exception_handler(exc, context):
    if isinstance(exc, ValidationError):
        exc.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        fields = exc.get_full_details()

    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)
    if response is not None and "detail" in response.data:
        response.data.pop("detail")

    # Now add the HTTP status code to the response.
    if response is not None and hasattr(exc, "default_code"):
        response.data["name"] = exc.default_code
        response.data["message"] = exc.default_detail

    if (
        response is not None
        and hasattr(exc, "status_code")
        and exc.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    ):
        response.data["fields"] = fields

    return response
