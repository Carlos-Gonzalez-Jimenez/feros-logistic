from rest_framework.exceptions import APIException
from rest_framework import status
from django.utils.translation import gettext_lazy as _


class BothDatesAreRequiredException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Both dates (start_date and end_date) are required")
    default_code = "both_dates_are_required"


class StartDateIsRequiredException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Start date is required")
    default_code = "start_date_is_required"


class DateFormatInvalidException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Invalid date format")
    default_code = "invalid_date_format"


class StartDateCanNotBeAfterEnddateException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Start date can't be after end date")
    default_code = "start_date_can_not_be_after_end_data"


class DateRangeTooLongException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Date range too long")
    default_code = "date_range_too_long"
