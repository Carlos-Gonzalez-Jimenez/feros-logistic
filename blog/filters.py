from blog.models import (
    Post,
    BlogCategory,
    Comment,
)
from user.models import User
from django_filters import (
    ModelChoiceFilter,
    CharFilter,
    ModelMultipleChoiceFilter,
    BooleanFilter,
)
from django_filters import rest_framework as filters


class CommentFilter(filters.FilterSet):
    approved = BooleanFilter(field_name="is_approved")

    class Meta:
        model = Comment
        fields = [
            "is_approved",
        ]


class PostFilter(filters.FilterSet):
    category = ModelMultipleChoiceFilter(
        queryset=BlogCategory.objects.all(),
    )

    author = ModelChoiceFilter(queryset=User.objects.all(), field_name="author")

    tags = CharFilter(method="filter_by_all_tags")

    def filter_by_all_tags(self, queryset, name, value):

        tag_names = [tag.strip() for tag in value.split(",")]
        return queryset.filter(tags__in=tag_names).distinct()

    class Meta:
        model = Post
        fields = ["category", "author", "tags"]
