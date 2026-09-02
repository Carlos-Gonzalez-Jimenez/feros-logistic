from rest_framework import serializers
from blog import models
from cms.serializers import (
    BlockMEDIASerializer,
    blocks_process,
    get_any_blocks,
)
from cms.models import Composer, ContentType
from cms.exceptions import InvalidContentTypeException
from user.serializers import UserMinimalSerializer
from django.db import transaction
from django.utils.text import slugify
import datetime
from .tasks import kmp_search
from django.utils.translation import gettext_lazy as _
from .obscene_words import SPANISH_OBSCENE_WORDS


class BlogCategorySerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    class Meta:
        model = models.BlogCategory
        fields = "__all__"


class TagSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    class Meta:
        model = models.Tag
        fields = "__all__"


class PostWriteSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    author = UserMinimalSerializer(read_only=True)
    category = BlogCategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        required=False, queryset=models.BlogCategory.objects.all(), source="category"
    )
    tags = TagSerializer(read_only=True, many=True, required=False)
    tags_ids = serializers.PrimaryKeyRelatedField(
        required=True, many=True, queryset=models.Tag.objects.all(), source="tags"
    )
    featured_image = BlockMEDIASerializer(read_only=True)
    featured_image_id = serializers.PrimaryKeyRelatedField(
        required=False,
        allow_null=True,
        queryset=models.BlockMEDIA.objects.all(),
        source="featured_image",
    )
    slug = serializers.SlugField(required=False, allow_blank=True)
    blocks = serializers.ListField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = models.Post
        fields = [
            "id",
            "title",
            "slug",
            "summary",
            "content",
            "author",
            "category",
            "category_id",
            "tags",
            "tags_ids",
            "featured_image",
            "featured_image_id",
            "status",
            "published_date",
            "created_at",
            "updated_at",
            "views_count",
            "is_featured",
            "no_comments",
            "blocks",
        ]

    def create(self, validated_data):
        with transaction.atomic():
            tags = validated_data.pop("tags", None)
            blocks = validated_data.pop("blocks", None)
            validated_data["slug"] = slugify(validated_data["title"])
            post = models.Post.objects.create(
                **validated_data, author=self.context.get("request").user
            )
            if tags:
                post.tags.set(tags)
            if blocks is not None:
                blocks_process(blocks, post)
            if post.status == "published" and not post.published_date:
                post.published_date = datetime.datetime.now().date()
                post.save()
            return post

    def update(self, instance, validated_data):
        with transaction.atomic():
            tags = validated_data.pop("tags_ids", None)
            blocks = validated_data.pop("blocks", None)
            validated_data["slug"] = slugify(validated_data["title"])
            instance = super(PostWriteSerializer, self).update(instance, validated_data)
            if tags:
                instance.tags.clear()
                instance.tags.set(tags)
            Composer.objects.filter(
                local_id=instance.id,
                local_content_type=ContentType.objects.get(model="post"),
            ).delete()
            if blocks:
                blocks_process(blocks, instance)
            if instance.status == "published" and not instance.published_date:
                instance.published_date = datetime.datetime.now().date()
                instance.save()
            return instance


class PostReadSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_

    Raises:
        InvalidContentTypeException: _description_
        UnexpectedRelatedObjectException: _description_

    Returns:
        _type_: _description_
    """

    author = UserMinimalSerializer(read_only=True)
    category = BlogCategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        required=False, queryset=models.BlogCategory.objects.all(), source="category"
    )
    tags = TagSerializer(read_only=True, many=True, required=False)
    tags_ids = serializers.PrimaryKeyRelatedField(
        required=True, many=True, queryset=models.Tag.objects.all(), source="tags"
    )
    featured_image = BlockMEDIASerializer(read_only=True)
    featured_image_id = serializers.PrimaryKeyRelatedField(
        required=False,
        allow_null=True,
        queryset=models.BlockMEDIA.objects.all(),
        source="featured_image",
    )
    blocks = serializers.SerializerMethodField()

    class Meta:
        model = models.Post
        fields = [
            "id",
            "title",
            "slug",
            "summary",
            "content",
            "author",
            "category",
            "category_id",
            "tags",
            "tags_ids",
            "featured_image",
            "featured_image_id",
            "status",
            "published_date",
            "created_at",
            "updated_at",
            "views_count",
            "is_featured",
            "no_comments",
            "blocks",
        ]

    def get_blocks(self, obj) -> list:
        return get_any_blocks(
            obj, "post", context={"request": self.context.get("request")}
        )


class PostReadMinimalSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_

    Raises:
        InvalidContentTypeException: _description_
        UnexpectedRelatedObjectException: _description_

    Returns:
        _type_: _description_
    """

    author = UserMinimalSerializer(read_only=True)
    category = BlogCategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        required=False, queryset=models.BlogCategory.objects.all(), source="category"
    )
    tags = TagSerializer(read_only=True, many=True, required=False)
    tags_ids = serializers.PrimaryKeyRelatedField(
        required=True, many=True, queryset=models.Tag.objects.all(), source="tags"
    )
    featured_image = BlockMEDIASerializer(read_only=True)
    featured_image_id = serializers.PrimaryKeyRelatedField(
        required=False,
        allow_null=True,
        queryset=models.BlockMEDIA.objects.all(),
        source="featured_image",
    )

    class Meta:
        model = models.Post
        fields = [
            "id",
            "title",
            "slug",
            "summary",
            "content",
            "author",
            "category",
            "category_id",
            "tags",
            "tags_ids",
            "featured_image",
            "featured_image_id",
            "status",
            "published_date",
            "created_at",
            "updated_at",
            "views_count",
            "is_featured",
            "no_comments",
        ]


class CommentSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    post = PostReadSerializer(read_only=True)
    post_id = serializers.PrimaryKeyRelatedField(
        required=True, queryset=models.Post.objects.all(), source="post"
    )
    author = UserMinimalSerializer(read_only=True)
    author_id = serializers.PrimaryKeyRelatedField(
        required=False,
        allow_null=True,
        queryset=models.User.objects.all(),
        source="author",
    )

    class Meta:
        model = models.Comment
        fields = [
            "id",
            "post",
            "post_id",
            "author",
            "author_id",
            "content",
            "is_approved",
            "may_be_obscene",
            "created_at",
            "updated_at",
            "parent_comment",
        ]

    def save(self, **kwargs):
        with transaction.atomic():
            kwargs["author"] = self.context["request"].user
            comment = super(CommentSerializer, self).save(**kwargs)
            for word in SPANISH_OBSCENE_WORDS:
                if kmp_search(comment.content.lower(), word.lower()):
                    comment.may_be_obscene = True
                    comment.save()
                    break
            return comment
