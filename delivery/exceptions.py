from rest_framework.exceptions import APIException
from rest_framework import status
from django.utils.translation import gettext_lazy as _


class OrderShippingDoesNotExistException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Order shipping does not exist")
    default_code = "order_shipping_does_not_exist"


class OrderHasNotDelivererAssignedException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Order has not deliverer assigned")
    default_code = "order_has_not_deliverer_assigned"


class OrderHasNotShipingRateException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Order has not shipping rate")
    default_code = "order_has_not_shipping_rate"
