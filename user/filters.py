from django_filters import BooleanFilter, ModelChoiceFilter, DateTimeFilter
from django_filters import rest_framework as filters

from user.models import User, EventLog
from django.contrib.auth.models import Group


class UserFilter(filters.FilterSet):

    role = ModelChoiceFilter(
        queryset=Group.objects.all(), field_name="groups", method="filter_role"
    )

    def filter_role(self, queryset, name, value):
        return queryset.filter(groups=value)

    staff = BooleanFilter(field_name="is_staff")
    delivery = BooleanFilter(field_name="is_deliverer")
    superuser = BooleanFilter(field_name="is_superuser")

    class Meta:
        model = User
        fields = ["staff", "superuser", "delivery", "groups"]


class EventLogFilter(filters.FilterSet):
    raised_date__gte = DateTimeFilter(field_name="raised_date", lookup_expr="gte")
    raised_date__lte = DateTimeFilter(field_name="raised_date", lookup_expr="lte")

    class Meta:
        model = EventLog
        fields = ["user", "action", "raised_date"]
