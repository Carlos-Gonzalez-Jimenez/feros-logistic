from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler
from django.utils.translation import gettext_lazy as _


class AssignCouponsException(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = _("Error during coupon assignment")
    default_code = "coupon_assignment_error"
