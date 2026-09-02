from django.core.cache import cache
from django.db import transaction
from django.db.models import ProtectedError
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import (
    AllowAny,
)
from rest_framework.response import Response

from cms import models, serializers, filters
from core.exceptions import InvalidParameterException, ProtectedInstanceException
from core.permissions import CustomPermissionFactory, ReadOnlyPermission
from core.views import ProtectedResourceViewSet


class PageViewSet(ProtectedResourceViewSet):
    """
    Page model\n
    GET: Shows all Pages created.\n
    POST: Adds a new Page.\n
    GET{id}: Retrieves a specific Page determined by id.\n
    PUT{id}: Modifies all fields of a specific Page determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific Page determined by id.\n
    DELETE{id}: Deletes a specific Page determined by id.\n
    """

    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["user.manage_page"]),
    ]
    queryset = models.Page.objects.all()

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return serializers.PageWriteSerializer
        return serializers.PageReadSerializer


class PageSlugView(ListAPIView):
    permission_classes = [AllowAny]
    queryset = models.Page.objects.all()
    serializer_class = serializers.PageReadSerializer

    def get(self, request, slug):
        try:
            page = models.Page.objects.get(slug=slug)
            serializer = serializers.PageReadSerializer(
                page,
                context={"request": request},
            )
            return Response(serializer.data, status=status.HTTP_200_OK)

        except models.Page.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


class BlockHTMLViewSet(ProtectedResourceViewSet):
    """
    Block HTML model\n
    GET: Shows all Block HTML created.\n
    POST: Adds a new Block HTML.\n
    GET{id}: Retrieves a specific Block HTML determined by id.\n
    PUT{id}: Modifies all fields of a specific Block HTML determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific Block HTML determined by id.\n
    DELETE{id}: Deletes a specific Block HTML determined by id.\n
    """

    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["user.manage_page"]),
    ]
    queryset = models.BlockHTML.objects.all()
    serializer_class = serializers.BlockHTMLSerializer


class BlockMarkdownViewSet(ProtectedResourceViewSet):
    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["user.manage_page"]),
    ]
    queryset = models.BlockMarkdown.objects.all()
    serializer_class = serializers.BlockMarkdownSerializer


class BlockMEDIAViewSet(ProtectedResourceViewSet):
    """
    Block MEDIA model\n
    GET: Shows all Block MEDIA created.\n
    POST: Adds a new Block MEDIA.\n
    GET{id}: Retrieves a specific Block MEDIA determined by id.\n
    PUT{id}: Modifies all fields of a specific Block MEDIA determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific Block MEDIA determined by id.\n
    DELETE{id}: Deletes a specific Block MEDIA determined by id.\n
    """

    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["user.manage_page"]),
    ]
    queryset = models.BlockMEDIA.objects.all()
    serializer_class = serializers.BlockMEDIASerializer
    filterset_class = filters.BlockMEDIAFilter
    search_fields = ["media"]

    @action(
        methods=["delete"],
        detail=False,
        url_path="delete-blocks",
        permission_classes=[
            ReadOnlyPermission | CustomPermissionFactory(["user.manage_page"]),
        ],
    )
    def delete_blocks(self, request):
        with transaction.atomic():
            media_list = request.data.get("media_ids")
            try:
                for media_id in media_list:
                    media = models.BlockMEDIA.objects.get(id=media_id)
                    try:
                        media.delete()
                    except ProtectedError as exception:
                        raise ProtectedInstanceException() from exception
                return Response(status=status.HTTP_204_NO_CONTENT)
            except models.BlockMEDIA.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)


class BlockMEDIACARDViewSet(ProtectedResourceViewSet):
    """
    Block MEDIA CARD model\n
    GET: Shows all Block MEDIA CARD created.\n
    POST: Adds a new Block MEDIA CARD.\n
    GET{id}: Retrieves a specific Block MEDIA CARD determined by id.\n
    PUT{id}: Modifies all fields of a specific Block MEDIA CARD determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific Block MEDIA CARD determined by id.\n
    DELETE{id}: Deletes a specific Block MEDIA CARD determined by id.\n
    """

    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["user.manage_page"]),
    ]
    queryset = models.BlockMEDIACARD.objects.all()
    serializer_class = serializers.BlockMEDIACARDSerializer


class BlockCONTAINERViewSet(ProtectedResourceViewSet):
    """
    Block CONTAINER model\n
    GET: Shows all Block CONTAINER created.\n
    POST: Adds a new Block CONTAINER.\n
    GET{id}: Retrieves a specific Block CONTAINER determined by id.\n
    PUT{id}: Modifies all fields of a specific Block CONTAINER determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific Block CONTAINER determined by id.\n
    DELETE{id}: Deletes a specific Block CONTAINER determined by id.\n
    """

    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["user.manage_page"]),
    ]
    queryset = models.BlockCONTAINER.objects.all()

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return serializers.BlockCONTAINERWriteSerializer
        return serializers.BlockCONTAINERReadSerializer


class BlockBUTTONViewSet(ProtectedResourceViewSet):
    """
    Block BUTTON model\n
    GET: Shows all Block BUTTON created.\n
    POST: Adds a new Block BUTTON.\n
    GET{id}: Retrieves a specific Block BUTTON determined by id.\n
    PUT{id}: Modifies all fields of a specific Block BUTTON determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific Block BUTTON determined by id.\n
    DELETE{id}: Deletes a specific Block BUTTON determined by id.\n
    """

    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["user.manage_page"]),
    ]
    queryset = models.BlockBUTTON.objects.all()
    serializer_class = serializers.BlockBUTTONSerializer


class BlockCAROUSELViewSet(ProtectedResourceViewSet):
    """
    Block CAROUSEL model\n
    GET: Shows all Block CAROUSEL created.\n
    POST: Adds a new Block CAROUSEL.\n
    GET{id}: Retrieves a specific Block CAROUSEL determined by id.\n
    PUT{id}: Modifies all fields of a specific Block CAROUSEL determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific Block CAROUSEL determined by id.\n
    DELETE{id}: Deletes a specific Block CAROUSEL determined by id.\n
    """

    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["user.manage_page"]),
    ]
    queryset = models.BlockCAROUSEL.objects.all()

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return serializers.BlockCAROUSELWriteSerializer
        return serializers.BlockCAROUSELReadSerializer


class BlockCARDGROUPViewSet(ProtectedResourceViewSet):
    """
    Block CARD GROUP model\n
    GET: Shows all Block CARD GROUP created.\n
    POST: Adds a new Block CARD GROUP.\n
    GET{id}: Retrieves a specific Block CARD GROUP determined by id.\n
    PUT{id}: Modifies all fields of a specific Block CARD GROUP determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific Block CARD GROUP determined by id.\n
    DELETE{id}: Deletes a specific Block CARD GROUP determined by id.\n
    """

    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["user.manage_page"]),
    ]
    queryset = models.BlockCARDGROUP.objects.all()

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return serializers.BlockCARDGROUPWriteSerializer
        return serializers.BlockCARDGROUPReadSerializer


class BlockCARDViewSet(ProtectedResourceViewSet):
    """
    Block CARD model\n
    GET: Shows all Block CARD created.\n
    POST: Adds a new Block CARD.\n
    GET{id}: Retrieves a specific Block CARD determined by id.\n
    PUT{id}: Modifies all fields of a specific Block CArD determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific Block CARD determined by id.\n
    DELETE{id}: Deletes a specific Block CARD determined by id.\n
    """

    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["user.manage_page"]),
    ]
    queryset = models.BlockCARD.objects.all()
    serializer_class = serializers.BlockCARDSerializer


class BlockViewSet(ProtectedResourceViewSet):
    """
    Block model\n
    GET: Shows all Block created.\n
    POST: Adds a new Block.\n
    GET{id}: Retrieves a specific Block determined by id.\n
    PUT{id}: Modifies all fields of a specific Block determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific Block determined by id.\n
    DELETE{id}: Deletes a specific Block determined by id.\n
    """

    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["user.manage_page"]),
    ]
    queryset = models.Blocks.objects.all()
    serializer_class = serializers.BlockSerializer


class ComposerViewSet(ProtectedResourceViewSet):
    """
    Composer model\n
    GET: Shows all Composer created.\n
    POST: Adds a new Composer.\n
    GET{id}: Retrieves a specific Composer determined by id.\n
    PUT{id}: Modifies all fields of a specific Composer determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific Composer determined by id.\n
    DELETE{id}: Deletes a specific Composer determined by id.\n
    """

    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["user.manage_page"]),
    ]
    queryset = models.Composer.objects.all()
    serializer_class = serializers.ComposerSerializer


class RelationShipsViewSet(ProtectedResourceViewSet):
    """
    RelationShip model\n
    GET: Shows all RelationShips created.\n
    POST: Adds a new RelationShip.\n
    GET{id}: Retrieves a specific RelationShip determined by id.\n
    PUT{id}: Modifies all fields of a specific RelationShip determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific RelationShip determined by id.\n
    DELETE{id}: Deletes a specific RelationShip determined by id.\n
    """

    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["user.manage_page"]),
    ]
    queryset = models.RelationShips.objects.all()
    serializer_class = serializers.RelationShipsSerializer

    @action(
        detail=False,
        methods=["get"],
        url_path=r"content",
        permission_classes=[
            ReadOnlyPermission | CustomPermissionFactory(["user.manage_page"]),
        ],
    )
    def content_relationships(self, request):
        with transaction.atomic():
            content_type = request.query_params.get("content_type", None)
            field_name = request.query_params.get("field_name", None)
            if content_type is not None:
                relationships = models.RelationShips.objects.filter(
                    Q(local_content_type__model=content_type)
                    & (Q(field_name__isnull=True) | Q(field_name__iexact=field_name))
                )
                local_content_type = models.ContentType.objects.get(model=content_type)
                blocks = []
                if relationships.exists():
                    for relationship in relationships:
                        block = models.Blocks.objects.get(id=relationship.block_id)
                        blocks.append(
                            {
                                "block": serializers.BlockSerializer(block).data,
                                "type": relationship.type,
                            }
                        )
                return Response(
                    {
                        "content_type": serializers.ContentTypeSerializer(
                            local_content_type
                        ).data,
                        "relationships": blocks,
                    },
                    status=status.HTTP_200_OK,
                )
            raise InvalidParameterException()


class BlockFOOTERLINKSViewSet(ProtectedResourceViewSet):
    """
    Block Footer Links model\n
    GET: Shows all Block Footer Links created.\n
    POST: Adds a new Block Footer Links.\n
    GET{id}: Retrieves a specific Block Footer Links determined by id.\n
    PUT{id}: Modifies all fields of a specific Block Footer Links determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific Block Footer Links determined by id.\n
    DELETE{id}: Deletes a specific Block Footer Links determined by id.\n
    """

    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["cms.manage_footer"])
    ]
    queryset = models.BlockFOOTERLINKS.objects.all()
    serializer_class = serializers.BlockFOOTERLINKSSerializer


class BlockNAVBARViewSet(ProtectedResourceViewSet):
    """
    Block NAVBAR model\n
    GET: Shows all Block NAVBAR created.\n
    POST: Adds a new Block NAVBAR.\n
    GET{id}: Retrieves a specific Block NAVBAR determined by id.\n
    PUT{id}: Modifies all fields of a specific Block NAVBAR determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific Block NAVBAR determined by id.\n
    DELETE{id}: Deletes a specific Block NAVBAR determined by id.\n
    """

    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["user.manage_page"]),
    ]
    queryset = models.BlockNAVBAR.objects.all()
    serializer_class = serializers.BlockNAVBARSerializer


class BlockHEROViewSet(ProtectedResourceViewSet):
    """
    Block HERO model\n
    GET: Shows all Block HERO created.\n
    POST: Adds a new Block HERO.\n
    GET{id}: Retrieves a specific Block HERO determined by id.\n
    PUT{id}: Modifies all fields of a specific Block HERO determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific Block HERO determined by id.\n
    DELETE{id}: Deletes a specific Block HERO determined by id.\n
    """

    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["user.manage_page"]),
    ]
    queryset = models.BlockHERO.objects.all()

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return serializers.BlockHEROWriteSerializer
        return serializers.BlockHEROReadSerializer


class BlockCTAViewSet(ProtectedResourceViewSet):
    """
    Block CTA model\n
    GET: Shows all Block CTA created.\n
    POST: Adds a new Block CTA.\n
    GET{id}: Retrieves a specific Block CTA determined by id.\n
    PUT{id}: Modifies all fields of a specific Block CTA determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific Block CTA determined by id.\n
    DELETE{id}: Deletes a specific Block CTA determined by id.\n
    """

    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["user.manage_page"]),
    ]
    queryset = models.BlockCTA.objects.all()

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return serializers.BlockCTAWriteSerializer
        return serializers.BlockCTAReadSerializer


class BlockMarqueeViewSet(ProtectedResourceViewSet):
    """
    Block Marquee model\n
    GET: Shows all Block Marquee created.\n
    POST: Adds a new Block Marquee.\n
    GET{id}: Retrieves a specific Block Marquee determined by id.\n
    PUT{id}: Modifies all fields of a specific Block Marquee determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific Block Marquee determined by id.\n
    DELETE{id}: Deletes a specific Block Marquee determined by id.\n
    """

    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["user.manage_page"]),
    ]
    queryset = models.BlockMarquee.objects.all()

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return serializers.BlockMarqueeWriteSerializer
        return serializers.BlockMarqueeReadSerializer


class HeaderAPIView(RetrieveUpdateAPIView):
    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["cms.manage_header"]),
    ]
    serializer_class = serializers.HeaderSerializer

    def get_object(self):
        return get_object_or_404(models.Header, pk=1)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


class FooterAPIView(RetrieveUpdateAPIView):
    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["cms.manage_footer"]),
    ]

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return serializers.FooterWriteSerializer
        return serializers.FooterReadSerializer

    def get_object(self):
        return get_object_or_404(models.Footer, pk=1)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


class LandingAPIView(RetrieveUpdateAPIView):
    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["user.manage_page"])
    ]

    CACHE_KEY = "landing_response"

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return serializers.LandingWriteSerializer
        return serializers.LandingReadSerializer

    def get_object(self):
        return get_object_or_404(models.Landing, pk=1)

    def get(self, request, *args, **kwargs):
        cached_response = cache.get(self.CACHE_KEY)
        if cached_response:
            return Response(cached_response)

        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data

        cache.set(self.CACHE_KEY, data, timeout=60 * 60 * 24)  # timeout diario
        return Response(data)

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)

        cache.delete(self.CACHE_KEY)

        return response

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


class ShopPageAPIView(RetrieveUpdateAPIView):
    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["user.manage_page"])
    ]

    CACHE_KEY = "shop_page_response"

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return serializers.ShopPageWriteSerializer
        return serializers.ShopPageReadSerializer

    def get_object(self):
        return get_object_or_404(models.ShopPage, pk=1)

    def get(self, request, *args, **kwargs):
        cached_response = cache.get(self.CACHE_KEY)
        if cached_response:
            return Response(cached_response)

        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data

        cache.set(self.CACHE_KEY, data, timeout=None)
        return Response(data)

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)

        cache.delete(self.CACHE_KEY)

        return response

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


class BlogPageAPIView(RetrieveUpdateAPIView):
    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["user.manage_page"])
    ]

    CACHE_KEY = "blog_page_response"

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return serializers.BlogPageWriteSerializer
        return serializers.BlogPageReadSerializer

    def get_object(self):
        return get_object_or_404(models.BlogPage, pk=1)

    def get(self, request, *args, **kwargs):
        cached_response = cache.get(self.CACHE_KEY)
        if cached_response:
            return Response(cached_response)

        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data

        cache.set(self.CACHE_KEY, data, timeout=None)
        return Response(data)

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)

        cache.delete(self.CACHE_KEY)

        return response

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


class BlockFilterProductViewSet(ProtectedResourceViewSet):
    """
    Block Filter Product model\n
    GET: Shows all Block Filter Product created.\n
    POST: Adds a new Block Filter Product.\n
    GET{id}: Retrieves a specific Block Filter Product determined by id.\n
    PUT{id}: Modifies all fields of a specific Block Filter Product determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific Block Filter Product determined by id.\n
    DELETE{id}: Deletes a specific Block Filter Product determined by id.\n
    """

    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["user.manage_page"]),
    ]
    queryset = models.BlockFilterProduct.objects.all()
    serializer_class = serializers.BlockFilterProductSerializer


class BlockFilterPostViewSet(ProtectedResourceViewSet):
    """
    Block Filter Post model\n
    GET: Shows all Block Filter Post created.\n
    POST: Adds a new Block Filter Post.\n
    GET{id}: Retrieves a specific Block Filter Post determined by id.\n
    PUT{id}: Modifies all fields of a specific Block Filter Post determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific Block Filter Post determined by id.\n
    DELETE{id}: Deletes a specific Block Filter Post determined by id.\n
    """

    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["user.manage_page"]),
    ]
    queryset = models.BlockFilterPost.objects.all()
    serializer_class = serializers.BlockFilterPostSerializer


class BlockFilterBrandViewSet(ProtectedResourceViewSet):
    """
    Block Filter Brand model\n
    GET: Shows all Block Filter Brand created.\n
    POST: Adds a new Block Filter Brand.\n
    GET{id}: Retrieves a specific Block Filter Brand determined by id.\n
    PUT{id}: Modifies all fields of a specific Block Filter Brand determined by id.\n
    PATCH{id}: Partially modifies the fields of a specific Block Filter Brand determined by id.\n
    DELETE{id}: Deletes a specific Block Filter Brand determined by id.\n
    """

    permission_classes = [
        ReadOnlyPermission | CustomPermissionFactory(["user.manage_page"]),
    ]
    queryset = models.BlockFilterBrand.objects.all()
    serializer_class = serializers.BlockFilterBrandSerializer
