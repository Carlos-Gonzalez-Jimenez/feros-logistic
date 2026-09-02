from rest_framework import status
from rest_framework.exceptions import APIException

from django.utils.translation import gettext_lazy as _


class UnexpectedRelatedObjectException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Unexpected related object")
    default_code = "unexpected_related_object"


class InvalidContentTypeException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Invalid content type")
    default_code = "invalid_content_type"


class ErrorProcessingBlockException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Error processing block")
    default_code = "error_procesing_block"


class UnsupportedModelException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Unsupported model")
    default_code = "unsupported_model"

class ItemRequiredForModelException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Item required for model")
    default_code = "item_required_for_model"