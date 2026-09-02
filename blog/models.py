from django.db import models
from core.generics import PermissionsMeta
from django.utils.translation import gettext_lazy as _
from user.models import User
from cms.models import BlockMEDIA


class BlogCategory(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta(PermissionsMeta.Meta):
        permissions = [("manage_blog_categories", _("Can manage blog categories"))]
        verbose_name = "Blog Category"
        verbose_name_plural = "Blog Categories"
        ordering = ["name"]


class Tag(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

    class Meta(PermissionsMeta.Meta):
        permissions = [("manage_blog_tags", _("Can manage blog tags"))]
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        ordering = ["-id"]


class Post(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("published", "Published"),
        ("archived", "Archived"),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=255, unique=True)
    summary = models.TextField(blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    category = models.ForeignKey(
        BlogCategory, on_delete=models.SET_NULL, null=True, related_name="posts"
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="posts")
    featured_image = models.ForeignKey(
        BlockMEDIA,
        related_name="image_posts",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="draft")
    published_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    views_count = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    no_comments = models.BooleanField(default=False)

    class Meta(PermissionsMeta.Meta):
        permissions = [("manage_blog", _("Can manage blog"))]
        verbose_name = "Post"
        verbose_name_plural = "Post"
        ordering = ["-published_date", "-created_at"]
        indexes = [
            models.Index(fields=["author", "-created_at"]),
            models.Index(fields=["status", "-published_date", "-created_at"]),
            models.Index(fields=["category", "status", "-published_date"]),
            models.Index(fields=["status", "-views_count"]),
        ]

    def __str__(self):
        return self.title

    def increment_views(self):
        self.views_count += 1
        self.save(update_fields=["views_count"])


class Comment(models.Model):
    post = models.ForeignKey(Post, related_name="comments", on_delete=models.CASCADE)
    author = models.ForeignKey(
        User, related_name="comments", on_delete=models.PROTECT, blank=True, null=True
    )
    content = models.TextField()
    is_approved = models.BooleanField(default=False)
    may_be_obscene = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    parent_comment = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies"
    )

    def __str__(self):
        return f"Comment by {self.author.first_name} {self.author.last_name} on {self.post.title}"

    class Meta(PermissionsMeta.Meta):
        permissions = [("manage_blog_comments", _("Can manage blog comments"))]
        verbose_name = "Comment"
        verbose_name_plural = "Comments"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["post", "is_approved", "-created_at"]),
        ]
