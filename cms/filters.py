from django_filters import ChoiceFilter
from cms.models import MEDIA_GROUP_CHOICES, BlockMEDIA
from django_filters import rest_framework as filters


class BlockMEDIAFilter(filters.FilterSet):
    status = ChoiceFilter(choices=MEDIA_GROUP_CHOICES)
    class Meta:
        model = BlockMEDIA
        fields = ["media_group"]
