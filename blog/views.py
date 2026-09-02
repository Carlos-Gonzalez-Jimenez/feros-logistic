from blog import models, serializers, filters
from rest_framework.response import Response
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
)
from rest_framework.generics import (
    ListAPIView,
)

from core.generics import MultiplePermissionsView
from core.permissions import (
    ReadOnlyPermission,
    CustomPermissionFactory,
    ClientPermission,
)
from core.views import ProtectedResourceViewSet
from rest_framework.decorators import action
from rest_framework import status
from django.db import transaction
from core.tasks import NomenclatorCacheManager


class BlogCategoryViewSet(ProtectedResourceViewSet):
    """
    Blog Category model\n
    GET: Shows all Blog Categories created.\n
    POST: Adds a new Blog Category.\n
    GET{id}: Retrieves a specific Blog Category determined by id.\n
    PUT{id}: Modifies all fields of a specific Blog Category determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific Blog Category determined by id.\n
    DELETE{id}: Deletes a specific Blog Category determined by id.\n
    """

    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["blog.manage_blog_categories"]),
    ]
    queryset = models.BlogCategory.objects.all()
    serializer_class = serializers.BlogCategorySerializer
    search_fields = ["name", "description"]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(active=True)

    def list(self, request, *args, **kwargs):
        page = request.query_params.get("page")
        page_size = request.query_params.get("page_size")
        search_term = request.query_params.get("search", "")

        if search_term and search_term.strip():
            return super().list(request, *args, **kwargs)

        cache_kwargs = {"page": page, "page_size": page_size, "search": search_term}

        cached_data = NomenclatorCacheManager.get_cached_data(
            "blogcategory", "list", request.user, **cache_kwargs
        )

        if cached_data is not None:
            return Response(cached_data)

        response = super().list(request, *args, **kwargs)

        if response.status_code == 200:
            NomenclatorCacheManager.set_cached_data(
                response.data,
                "blogcategory",
                "list",
                request.user,
                timeout=60 * 60 * 24,
                **cache_kwargs,
            )

        return response

    def retrieve(self, request, *args, **kwargs):
        cached_data = NomenclatorCacheManager.get_cached_data(
            "blogcategory", "retrieve", request.user, kwargs.get("pk")
        )

        if cached_data is not None:
            return Response(cached_data)

        response = super().retrieve(request, *args, **kwargs)

        if response.status_code == 200:
            NomenclatorCacheManager.set_cached_data(
                response.data,
                "blogcategory",
                "retrieve",
                request.user,
                pk=kwargs.get("pk"),
                timeout=60 * 60 * 24 * 7,
            )

        return response

    def perform_create(self, serializer):
        NomenclatorCacheManager.invalidate_model_cache("blogcategory")
        response = super().perform_create(serializer)
        return response

    def perform_update(self, serializer):
        NomenclatorCacheManager.invalidate_model_cache("blogcategory")
        response = super().perform_update(serializer)
        return response

    def perform_destroy(self, instance):
        NomenclatorCacheManager.invalidate_model_cache("blogcategory")
        response = super().perform_destroy(instance)
        return response


class TagViewSet(ProtectedResourceViewSet):
    """
    Tag model\n
    GET: Shows all Tags created.\n
    POST: Adds a new Tag.\n
    GET{id}: Retrieves a specific Tag determined by id.\n
    PUT{id}: Modifies all fields of a specific Tag determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific Tag determined by id.\n
    DELETE{id}: Deletes a specific Tag determined by id.\n
    """

    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["blog.manage_blog_tags"]),
    ]
    queryset = models.Tag.objects.all()
    serializer_class = serializers.TagSerializer
    search_fields = ["name"]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(active=True)

    def list(self, request, *args, **kwargs):
        page = request.query_params.get("page")
        page_size = request.query_params.get("page_size")
        search_term = request.query_params.get("search", "")

        if search_term and search_term.strip():
            return super().list(request, *args, **kwargs)

        cache_kwargs = {"page": page, "page_size": page_size, "search": search_term}

        cached_data = NomenclatorCacheManager.get_cached_data(
            "tag", "list", request.user, **cache_kwargs
        )

        if cached_data is not None:
            return Response(cached_data)

        response = super().list(request, *args, **kwargs)

        if response.status_code == 200:
            NomenclatorCacheManager.set_cached_data(
                response.data,
                "tag",
                "list",
                request.user,
                timeout=60 * 60 * 24 * 7,
                **cache_kwargs,
            )

        return response

    def retrieve(self, request, *args, **kwargs):
        cached_data = NomenclatorCacheManager.get_cached_data(
            "tag", "retrieve", request.user, kwargs.get("pk")
        )

        if cached_data is not None:
            return Response(cached_data)

        response = super().retrieve(request, *args, **kwargs)

        if response.status_code == 200:
            NomenclatorCacheManager.set_cached_data(
                response.data,
                "tag",
                "retrieve",
                request.user,
                pk=kwargs.get("pk"),
                timeout=60 * 60 * 24 * 30,
            )

        return response

    def perform_create(self, serializer):
        NomenclatorCacheManager.invalidate_model_cache("tag")
        response = super().perform_create(serializer)
        return response

    def perform_update(self, serializer):
        NomenclatorCacheManager.invalidate_model_cache("tag")
        response = super().perform_update(serializer)
        return response

    def perform_destroy(self, instance):
        NomenclatorCacheManager.invalidate_model_cache("tag")
        response = super().perform_destroy(instance)
        return response


class PostViewSet(ProtectedResourceViewSet):
    """
    Post model\n
    GET: Shows all Posts created.\n
    POST: Adds a new Post.\n
    GET{id}: Retrieves a specific Post determined by id.\n
    PUT{id}: Modifies all fields of a specific Post determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific Post determined by id.\n
    DELETE{id}: Deletes a specific Post determined by id.\n
    """

    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["blog.manage_blog"]),
    ]
    queryset = models.Post.objects.all()
    filterset_class = filters.PostFilter
    search_fields = ["title", "category", "author", "summary", "content", "status"]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(status="published")

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return serializers.PostWriteSerializer
        if self.action == "list":
            return serializers.PostReadMinimalSerializer
        return serializers.PostReadSerializer

    @action(
        detail=True,
        methods=["post"],
        url_path="increment-views",
        permission_classes=[IsAuthenticated],
    )
    def increment_views(self, request, pk=None):
        with transaction.atomic():
            post = self.get_object()
            user = self.request.user
            if not user.is_staff:
                post.increment_views()
            return Response(
                {"views_count": post.views_count}, status=status.HTTP_200_OK
            )

    @action(
        detail=True,
        methods=["get"],
        url_path="comments",
        permission_classes=[IsAuthenticated],
    )
    def post_comments(self, request, pk=None):
        post = self.get_object()
        comments = models.Comment.objects.filter(post_id=post.id, is_approved=True)
        return Response(
            serializers.CommentSerializer(comments, many=True).data,
            status=status.HTTP_200_OK,
        )


class PostSlugView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = serializers.PostReadSerializer

    def get_queryset(self):
        return (
            models.Post.objects.filter(status="published")
            .select_related("author", "category")
            .prefetch_related(
                "tags",
            )
        )

    def get(self, request, slug):
        try:
            post = self.get_queryset().get(slug=slug)
            serializer = self.get_serializer(post)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except models.Post.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


class CommentViewSet(ProtectedResourceViewSet, MultiplePermissionsView):
    """
    Comment model\n
    GET: Shows all Comments created.\n
    POST: Adds a new Comment.\n
    GET{id}: Retrieves a specific Comment determined by id.\n
    PUT{id}: Modifies all fields of a specific Comment determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific Comment determined by id.\n
    DELETE{id}: Deletes a specific Comment determined by id.\n
    """

    post_permission_classes = [IsAuthenticated]
    permission_classes = [CustomPermissionFactory(["blog.manage_blog_comments"])]
    queryset = models.Comment.objects.all()
    filterset_class = filters.CommentFilter
    serializer_class = serializers.CommentSerializer
    search_fields = ["content"]

    @action(
        detail=True,
        methods=["post"],
        url_path=r"approve",
        permission_classes=[CustomPermissionFactory(["blog.manage_blog_comments"])],
    )
    def approve(self, request, pk=None):
        with transaction.atomic():
            comment = self.get_object()
            comment.is_approved = True
            comment.may_be_obscene = False
            comment.save()
            return Response(
                serializers.CommentSerializer(comment).data, status=status.HTTP_200_OK
            )
