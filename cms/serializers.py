import mimetypes
import os

from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.serializers import ALL_FIELDS

from blog.models import Post
from cms import models
from cms.exceptions import (
    UnexpectedRelatedObjectException,
    InvalidContentTypeException,
    ErrorProcessingBlockException,
    UnsupportedModelException,
    ItemRequiredForModelException,
)
from core.models import Product, Brand


class BlockMEDIASerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    media = serializers.FileField(read_only=True)
    media_file = serializers.FileField(write_only=True, source="media")
    name = serializers.SerializerMethodField()
    size = serializers.SerializerMethodField()
    mime_type = serializers.SerializerMethodField()

    class Meta:
        model = models.BlockMEDIA
        fields = [
            "id",
            "name",
            "media",
            "media_file",
            "size",
            "mime_type",
            "media_group",
        ]

    def validate_media_file(self, value):
        filename = value.name
        if models.BlockMEDIA.objects.filter(media__endswith=filename).exists():
            raise serializers.ValidationError(
                _("A file with that name already exists.")
            )
        return value

    def get_size(self, obj) -> str:
        x = obj.media.size
        y = 512000
        if x < y:
            value = round(x / 1024, 2)
            ext = " KB"
        elif x < y * 1024:
            value = round(x / (1024 * 1024), 2)
            ext = " MB"
        else:
            value = round(x / (1024 * 1024 * 1024), 2)
            ext = " GB"
        return str(value) + ext

    def get_name(self, obj) -> str:
        return os.path.basename(obj.media.name)

    def get_mime_type(self, obj) -> str:
        return mimetypes.guess_type(obj.media.path)[0]


class BlockHTMLSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    class Meta:
        model = models.BlockHTML
        fields = "__all__"


class BlockMarkdownSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    class Meta:
        model = models.BlockMarkdown
        fields = "__all__"


def handle_serializer_processing(model_name, data, item_id, serializer_mapping):
    """Maneja la lógica de serialización para modelos que la requieren."""
    model = ContentType.objects.get(model=model_name.lower()).model_class()
    serializer_class = serializer_mapping[model_name]

    if item_id:
        obj = model.objects.get(id=item_id)
        serializer = serializer_class(obj, data=data)
    else:
        serializer = serializer_class(data=data)

    if serializer.is_valid(raise_exception=True):
        return serializer.save()
    return None


def handle_reference_model(model_name, item_id):
    """Maneja modelos que solo necesitan referencia."""
    if not item_id:
        raise ItemRequiredForModelException()

    model = ContentType.objects.get(model=model_name.lower()).model_class()
    return model.objects.get(id=item_id)


def process_block_item(model_name, data, item_id, serializer_mapping, reference_models):
    """Procesa un ítem individual del bloque."""
    if model_name in serializer_mapping:
        return handle_serializer_processing(
            model_name, data, item_id, serializer_mapping
        )
    elif model_name in reference_models:
        return handle_reference_model(model_name, item_id)
    else:
        raise UnsupportedModelException()


def create_composer_record(instance, item_obj, order, block, field_name):
    """Crea el registro en el Composer."""
    models.Composer.objects.create(
        local_id=instance.id,
        item_id=item_obj.id,
        order=order,
        block_id=block["block"]["id"],
        local_content_type_id=block["local_content_type"],
        field_name=field_name,
    )


def blocks_process(blocks, instance, field_name=None) -> None:
    """Procesa bloques de contenido y los asocia a una instancia.

    Args:
        blocks: Lista de bloques a procesar
        instance: Instancia a la que asociar los bloques
        field_name: Nombre del campo opcional para identificación
    """

    # Configuración centralizada de serializers
    SERIALIZER_MAPPING = {
        "BlockHTML": BlockHTMLSerializer,
        "BlockMarkdown": BlockMarkdownSerializer,
        "BlockBUTTON": BlockBUTTONSerializer,
        "BlockCAROUSEL": BlockCAROUSELWriteSerializer,
        "BlockCARDGROUP": BlockCARDGROUPWriteSerializer,
        "BlockCARD": BlockCARDSerializer,
        "BlockMEDIACARD": BlockMEDIACARDSerializer,
        "BlockCONTAINER": BlockCONTAINERWriteSerializer,
        "BlockHERO": BlockHEROWriteSerializer,
        "BlockFOOTERLINKS": BlockFOOTERLINKSSerializer,
        "BlockCTA": BlockCTAWriteSerializer,
        "BlockMarquee": BlockMarqueeWriteSerializer,
        "BlockFilterProduct": BlockFilterProductSerializer,
        "BlockFilterPost": BlockFilterPostSerializer,
        "BlockFilterBrand": BlockFilterBrandSerializer,
    }

    # Modelos que solo necesitan referencia (no serialización)
    REFERENCE_MODELS = {"Product", "Category", "Post", "Brand", "BlockMEDIA"}

    order = 1
    for block in blocks:
        data = block.get("item")
        item_id = block.get("item_id")
        content_type = block["block"]["content_type"]["model"]

        try:
            model = ContentType.objects.get(model=content_type).model_class()
            model_name = model.__name__

            item_obj = process_block_item(
                model_name, data, item_id, SERIALIZER_MAPPING, REFERENCE_MODELS
            )

            if item_obj:
                create_composer_record(instance, item_obj, order, block, field_name)
                order += 1

        except Exception as exception:
            raise ErrorProcessingBlockException() from exception


def get_any_blocks(obj, block_type, context, field_name=None) -> list:
    """Obtiene bloques de cualquier tipo especificado."""
    try:
        content_type = ContentType.objects.get(model=block_type)
        blocks = models.Composer.objects.filter(
            local_id=obj.id, local_content_type=content_type, field_name=field_name
        ).order_by("order")

        serializer = ComposerSerializer(blocks, many=True, context=context)
        return serializer.data

    except ContentType.DoesNotExist as exception:
        raise InvalidContentTypeException() from exception


class BlockCONTAINERWriteSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    back_image = BlockMEDIASerializer(read_only=True)
    back_image_id = serializers.PrimaryKeyRelatedField(
        required=False,
        allow_null=True,
        queryset=models.BlockMEDIA.objects.all(),
        source="back_image",
    )

    blocks = serializers.ListField(write_only=True)

    class Meta:
        model = models.BlockCONTAINER
        fields = ["id", "label", "back_image", "back_image_id", "wide", "blocks"]

    def create(self, validated_data):
        with transaction.atomic():
            blocks = validated_data.pop("blocks", None)
            container = models.BlockCONTAINER.objects.create(**validated_data)
            if blocks:
                blocks_process(blocks, container)
            return container

    def update(self, instance, validated_data):
        with transaction.atomic():
            blocks = validated_data.pop("blocks", None)
            instance = super(BlockCONTAINERWriteSerializer, self).update(
                instance, validated_data
            )
            models.Composer.objects.filter(
                local_id=instance.id,
                local_content_type=ContentType.objects.get(model="blockcontainer"),
            ).delete()
            if blocks:
                blocks_process(blocks, instance)
            return instance


class BlockCONTAINERReadSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_

    Raises:
        InvalidContentTypeException: _description_
        UnexpectedRelatedObjectException: _description_

    Returns:
        _type_: _description_
    """

    back_image = BlockMEDIASerializer(read_only=True)
    back_image_id = serializers.PrimaryKeyRelatedField(
        required=False,
        allow_null=True,
        queryset=models.BlockMEDIA.objects.all(),
        source="back_image",
    )

    blocks = serializers.SerializerMethodField()

    class Meta:
        model = models.BlockCONTAINER
        fields = [
            "id",
            "label",
            "back_image",
            "back_image_id",
            "wide",
            "blocks",
        ]

    def get_blocks(self, obj) -> list:
        return get_any_blocks(
            obj, "blockcontainer", context={"request": self.context.get("request")}
        )


class BlockMEDIACARDSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_

    Raises:
        InvalidContentTypeException: _description_
        UnexpectedRelatedObjectException: _description_

    Returns:
        _type_: _description_
    """

    image = BlockMEDIASerializer(read_only=True)
    image_id = serializers.PrimaryKeyRelatedField(
        required=False, queryset=models.BlockMEDIA.objects.all(), source="image", allow_null=True
    )
    image_sm = BlockMEDIASerializer(read_only=True)
    image_sm_id = serializers.PrimaryKeyRelatedField(
        required=False, queryset=models.BlockMEDIA.objects.all(), source="image_sm", allow_null=True
    )
    image_md = BlockMEDIASerializer(read_only=True)
    image_md_id = serializers.PrimaryKeyRelatedField(
        required=False, queryset=models.BlockMEDIA.objects.all(), source="image_md", allow_null=True
    )
    image_lg = BlockMEDIASerializer(read_only=True)
    image_lg_id = serializers.PrimaryKeyRelatedField(
        required=False, queryset=models.BlockMEDIA.objects.all(), source="image_lg", allow_null=True
    )

    class Meta:
        model = models.BlockMEDIACARD
        fields = '__all__'


class BlockBUTTONSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    class Meta:
        model = models.BlockBUTTON
        fields = "__all__"


class BlockCAROUSELReadSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    blocks = serializers.SerializerMethodField()

    class Meta:
        model = models.BlockCAROUSEL
        fields = ALL_FIELDS

    def get_blocks(self, obj) -> list:
        return get_any_blocks(
            obj, "blockcarousel", context={"request": self.context.get("request")}
        )


class BlockCAROUSELWriteSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    blocks = serializers.ListField(write_only=True)

    class Meta:
        model = models.BlockCAROUSEL
        fields = ALL_FIELDS

    def create(self, validated_data):
        with transaction.atomic():
            blocks = validated_data.pop("blocks", None)
            carousel = models.BlockCAROUSEL.objects.create(**validated_data)
            if blocks:
                blocks_process(blocks, carousel)
            return carousel

    def update(self, instance, validated_data):
        with transaction.atomic():
            blocks = validated_data.pop("blocks", None)
            instance = super(BlockCAROUSELWriteSerializer, self).update(
                instance, validated_data
            )
            models.Composer.objects.filter(
                local_id=instance.id,
                local_content_type=ContentType.objects.get(model="blockcarousel"),
            ).delete()
            if blocks:
                blocks_process(blocks, instance)
            return instance


class BlockCARDSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    image = BlockMEDIASerializer(read_only=True)
    image_id = serializers.PrimaryKeyRelatedField(
        required=False,
        queryset=models.BlockMEDIA.objects.all(),
        source="image",
        allow_null=True,
    )

    class Meta:
        model = models.BlockCARD
        fields = ALL_FIELDS


class ContentTypeSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    class Meta:
        model = models.ContentType
        fields = "__all__"


class BlockSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_

    Raises:
        UnexpectedRelatedObjectException: _description_

    Returns:
        _type_: _description_
    """

    content_type = ContentTypeSerializer(read_only=True)
    content_type_id = serializers.PrimaryKeyRelatedField(
        required=False,
        queryset=models.ContentType.objects.all(),
        source="content_type",
    )

    class Meta:
        model = models.Blocks
        fields = [
            "id",
            "name",
            "label",
            "color",
            "icon",
            "content_type",
            "content_type_id",
        ]


class RelationShipsSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    block = BlockSerializer(read_only=True)
    block_id = serializers.PrimaryKeyRelatedField(
        required=False,
        queryset=models.Blocks.objects.all(),
        source="block",
    )
    local_content_type = ContentTypeSerializer(read_only=True)
    local_content_type_id = serializers.PrimaryKeyRelatedField(
        required=False,
        queryset=models.ContentType.objects.all(),
        source="local_content_type",
    )

    class Meta:
        model = models.RelationShips
        fields = [
            "id",
            "type",
            "block",
            "block_id",
            "local_content_type",
            "local_content_type_id",
            "field_name",
        ]


class BlockCARDGROUPReadSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    blocks = serializers.SerializerMethodField()

    class Meta:
        model = models.BlockCARDGROUP
        fields = '__all__'

    def get_blocks(self, obj) -> list:
        return get_any_blocks(
            obj, "blockcardgroup", context={"request": self.context.get("request")}
        )


class BlockCARDGROUPWriteSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    blocks = serializers.ListField(write_only=True)

    class Meta:
        model = models.BlockCARDGROUP
        fields = '__all__'

    def create(self, validated_data):
        with transaction.atomic():
            blocks = validated_data.pop("blocks", None)
            card_group = models.BlockCARDGROUP.objects.create(**validated_data)
            if blocks:
                blocks_process(blocks, card_group)
            return card_group

    def update(self, instance, validated_data):
        with transaction.atomic():
            blocks = validated_data.pop("blocks", None)
            instance = super(BlockCARDGROUPWriteSerializer, self).update(
                instance, validated_data
            )
            models.Composer.objects.filter(
                local_id=instance.id,
                local_content_type=ContentType.objects.get(model="blockcardgroup"),
            ).delete()
            if blocks:
                blocks_process(blocks, instance)
            return instance


class PageReadSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    blocks = serializers.SerializerMethodField()

    class Meta:
        model = models.Page
        fields = [
            "id",
            "name",
            "slug",
            "active",
            "creation_date",
            "updated_date",
            "blocks",
        ]

    def get_blocks(self, obj) -> list:
        return get_any_blocks(
            obj, "page", context={"request": self.context.get("request")}
        )


class PageWriteSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    blocks = serializers.ListField(write_only=True)

    class Meta:
        model = models.Page
        fields = [
            "id",
            "name",
            "slug",
            "active",
            "creation_date",
            "updated_date",
            "blocks",
        ]

    def create(self, validated_data):
        with transaction.atomic():
            blocks = validated_data.pop("blocks", None)
            page = models.Page.objects.create(**validated_data)
            if blocks:
                blocks_process(blocks, page)
            return page

    def update(self, instance, validated_data):
        with transaction.atomic():
            blocks = validated_data.pop("blocks", None)
            instance = super(PageWriteSerializer, self).update(instance, validated_data)
            models.Composer.objects.filter(
                local_id=instance.id,
                local_content_type=ContentType.objects.get(model="page"),
            ).delete()
            if blocks:
                blocks_process(blocks, instance)
            return instance


class ComposerSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    block = BlockSerializer(read_only=True)
    block_id = serializers.PrimaryKeyRelatedField(
        required=False,
        queryset=models.Blocks.objects.all(),
        source="block",
    )
    item = serializers.SerializerMethodField()
    deleted = serializers.SerializerMethodField()

    class Meta:
        model = models.Composer
        fields = [
            "id",
            "order",
            "local_content_type",
            "local_id",
            "block",
            "block_id",
            "item",
            "item_id",
            "deleted",
            "field_name",
        ]

    def get_deleted(self, obj) -> bool:
        return False

    def get_item(self, obj) -> dict:
        """Obtiene y serializa el ítem asociado al bloque."""

        # Importaciones lazy para evitar circular imports
        from core.serializers import ProductReadMinimalSerializer, CategorySerializer, BrandSerializer
        from blog.serializers import PostReadMinimalSerializer

        # Configuración centralizada de serializers
        SERIALIZER_MAPPING = {
            "BlockHTML": BlockHTMLSerializer,
            "BlockMarkdown": BlockMarkdownSerializer,
            "BlockBUTTON": BlockBUTTONSerializer,
            "BlockCAROUSEL": BlockCAROUSELReadSerializer,
            "BlockMEDIA": BlockMEDIASerializer,
            "BlockMEDIACARD": BlockMEDIACARDSerializer,
            "BlockCONTAINER": BlockCONTAINERReadSerializer,
            "BlockCARDGROUP": BlockCARDGROUPReadSerializer,
            "BlockCARD": BlockCARDSerializer,
            "BlockHERO": BlockHEROReadSerializer,
            "BlockCTA": BlockCTAReadSerializer,
            "BlockMarquee": BlockMarqueeReadSerializer,
            "BlockFOOTERLINKS": BlockFOOTERLINKSSerializer,
            "Product": ProductReadMinimalSerializer,
            "Category": CategorySerializer,
            "Brand": BrandSerializer,
            "Post": PostReadMinimalSerializer,
            "BlockFilterProduct": BlockFilterProductFullSerializer,
            "BlockFilterPost": BlockFilterPostFullSerializer,
            "BlockFilterBrand": BlockFilterBrandFullSerializer,
        }

        # Obtener el content_type y modelo
        content_type = models.ContentType.objects.get(
            id=models.Blocks.objects.get(id=obj.block_id).content_type_id
        )
        model = content_type.model_class()
        model_name = model.__name__

        # Verificar si el modelo está soportado
        if model_name not in SERIALIZER_MAPPING:
            raise UnexpectedRelatedObjectException()

        # Obtener y serializar el objeto
        model_obj = model.objects.get(id=obj.item_id)
        serializer_class = SERIALIZER_MAPPING[model_name]

        serializer = serializer_class(
            model_obj, context={"request": self.context.get("request")}
        )

        return serializer.data


class BlockFOOTERLINKSSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    class Meta:
        model = models.BlockFOOTERLINKS
        fields = "__all__"


class BlockNAVBARSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    class Meta:
        model = models.BlockNAVBAR
        fields = "__all__"


class BlockFilterProductFullSerializer(serializers.ModelSerializer):
    results = serializers.SerializerMethodField()

    class Meta:
        model = models.BlockFilterProduct
        fields = ALL_FIELDS

    def get_results(self, obj):
        from core.serializers import ProductReadMinimalSerializer

        results = Product.objects.all()

        if obj.filters:
            if isinstance(obj.filters, dict):
                results = results.filter(**obj.filters)

        if obj.exclude:
            if isinstance(obj.exclude, dict):
                results = results.exclude(**obj.exclude)

        if obj.order_by:
            if isinstance(obj.order_by, str):
                order_fields = [field.strip() for field in obj.order_by.split(",")]
                results = results.order_by(*order_fields)

        if obj.limit and obj.limit > 0:
            results = results[: obj.limit]
        return ProductReadMinimalSerializer(
            results, many=True, context={"request": self.context.get("request")}
        ).data


class BlockFilterProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.BlockFilterProduct
        fields = ALL_FIELDS


class BlockFilterPostFullSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    results = serializers.SerializerMethodField()

    class Meta:
        model = models.BlockFilterPost
        fields = ALL_FIELDS

    def get_results(self, obj):
        from blog.serializers import PostReadMinimalSerializer

        results = Post.objects.all()

        if obj.filters:
            if isinstance(obj.filters, dict):
                results = results.filter(**obj.filters)

        if obj.exclude:
            if isinstance(obj.exclude, dict):
                results = results.exclude(**obj.exclude)

        if obj.order_by:
            if isinstance(obj.order_by, str):
                order_fields = [field.strip() for field in obj.order_by.split(",")]
                results = results.order_by(*order_fields)

        if obj.limit and obj.limit > 0:
            results = results[: obj.limit]

        return PostReadMinimalSerializer(
            results, many=True, context={"request": self.context.get("request")}
        ).data


class BlockFilterPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.BlockFilterPost
        fields = ALL_FIELDS


class BlockFilterBrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.BlockFilterBrand
        fields = ALL_FIELDS


class BlockFilterBrandFullSerializer(serializers.ModelSerializer):
    results = serializers.SerializerMethodField()

    class Meta:
        model = models.BlockFilterBrand
        fields = ALL_FIELDS

    def get_results(self, obj):
        from core.serializers import BrandSerializer

        results = Brand.objects.all()

        if obj.filters:
            if isinstance(obj.filters, dict):
                results = results.filter(**obj.filters)

        if obj.exclude:
            if isinstance(obj.exclude, dict):
                results = results.exclude(**obj.exclude)

        if obj.order_by:
            if isinstance(obj.order_by, str):
                order_fields = [field.strip() for field in obj.order_by.split(",")]
                results = results.order_by(*order_fields)

        if obj.limit and obj.limit > 0:
            results = results[: obj.limit]
        return BrandSerializer(results, many=True, context={"request": self.context.get("request")}).data


class BlockHEROReadSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    image = BlockMEDIASerializer(read_only=True, required=False)
    image_id = serializers.PrimaryKeyRelatedField(
        required=False,
        queryset=models.BlockMEDIA.objects.all(),
        source="image",
    )
    gallery = BlockMEDIASerializer(read_only=True, many=True, required=False)
    gallery_ids = serializers.PrimaryKeyRelatedField(
        required=False,
        many=True,
        queryset=models.BlockMEDIA.objects.all(),
        source="gallery",
    )
    blocks = serializers.SerializerMethodField()

    class Meta:
        model = models.BlockHERO
        fields = [
            "id",
            "name",
            "hero_type",
            "location",
            "image",
            "image_id",
            "gallery",
            "gallery_ids",
            "blocks",
        ]

    def get_blocks(self, obj) -> list:
        return get_any_blocks(
            obj, "blockhero", context={"request": self.context.get("request")}
        )


class BlockHEROWriteSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    image = BlockMEDIASerializer(read_only=True)
    image_id = serializers.PrimaryKeyRelatedField(
        required=False,
        allow_null=True,
        queryset=models.BlockMEDIA.objects.all(),
        source="image",
    )
    gallery = BlockMEDIASerializer(read_only=True, many=True)
    gallery_ids = serializers.PrimaryKeyRelatedField(
        required=False,
        many=True,
        queryset=models.BlockMEDIA.objects.all(),
        source="gallery",
    )
    blocks = serializers.ListField(write_only=True)

    class Meta:
        model = models.BlockHERO
        fields = [
            "id",
            "name",
            "hero_type",
            "location",
            "image",
            "image_id",
            "gallery",
            "gallery_ids",
            "blocks",
        ]

    def create(self, validated_data):
        with transaction.atomic():
            blocks = validated_data.pop("blocks", None)
            gallery = validated_data.pop("gallery", None)
            hero = models.BlockHERO.objects.create(**validated_data)
            if gallery:
                hero.gallery.set(gallery)
            if blocks:
                blocks_process(blocks, hero)
            return hero

    def update(self, instance, validated_data):
        with transaction.atomic():
            blocks = validated_data.pop("blocks", None)
            gallery = validated_data.pop("gallery_ids", None)
            instance = super(BlockHEROWriteSerializer, self).update(
                instance, validated_data
            )
            if gallery:
                instance.gallery.clear()
                instance.gallery.set(gallery)
            models.Composer.objects.filter(
                local_id=instance.id,
                local_content_type=ContentType.objects.get(model="blockhero"),
            ).delete()
            if blocks:
                blocks_process(blocks, instance)
            return instance


class BlockCTAReadSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    extra_blocks = serializers.SerializerMethodField()
    inner_blocks = serializers.SerializerMethodField()

    class Meta:
        model = models.BlockCTA
        fields = [
            "id",
            "title",
            "size",
            "description",
            "orientation",
            "reverse",
            "variant",
            "extra_blocks",
            "inner_blocks",
            "buttons",
        ]

    def get_extra_blocks(self, obj) -> list:
        return get_any_blocks(
            obj, "blockcta", {"request": self.context.get("request")}, "extra"
        )

    def get_inner_blocks(self, obj) -> list:
        return get_any_blocks(
            obj, "blockcta", {"request": self.context.get("request")}, None
        )


class BlockCTAWriteSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    extra_blocks = serializers.ListField(write_only=True)
    inner_blocks = serializers.ListField(write_only=True)

    class Meta:
        model = models.BlockCTA
        fields = [
            "id",
            "title",
            "size",
            "description",
            "orientation",
            "reverse",
            "variant",
            "extra_blocks",
            "inner_blocks",
            "buttons",
        ]

    def create(self, validated_data):
        with transaction.atomic():
            extra_blocks = validated_data.pop("extra_blocks", None)
            inner_blocks = validated_data.pop("inner_blocks", None)
            cta = models.BlockCTA.objects.create(**validated_data)
            if extra_blocks:
                blocks_process(extra_blocks, cta, "extra")
            if inner_blocks:
                blocks_process(inner_blocks, cta, None)
            return cta

    def update(self, instance, validated_data):
        with transaction.atomic():
            extra_blocks = validated_data.pop("extra_blocks", None)
            inner_blocks = validated_data.pop("inner_blocks", None)
            instance = super(BlockCTAWriteSerializer, self).update(
                instance, validated_data
            )
            try:
                local_content_type = ContentType.objects.get(model="blockcta")
            except ContentType.DoesNotExist as exception:
                raise ItemRequiredForModelException() from exception
            models.Composer.objects.filter(local_id=instance.id, local_content_type=local_content_type).delete()
            if extra_blocks:
                blocks_process(extra_blocks, instance, "extra")
            if inner_blocks:
                blocks_process(inner_blocks, instance, None)
            return instance


class BlockMarqueeReadSerializer(serializers.ModelSerializer):
    blocks = serializers.SerializerMethodField()

    class Meta:
        model = models.BlockMarquee
        fields = [
            "id",
            "repeat",
            "label",
            "overlay",
            "pauseOnHover",
            "orientation",
            "reverse",
            "blocks",
        ]

    def get_blocks(self, obj) -> list:
        return get_any_blocks(
            obj, "blockmarquee", context={"request": self.context.get("request")}
        )


class BlockMarqueeWriteSerializer(serializers.ModelSerializer):
    blocks = serializers.ListField(write_only=True)

    class Meta:
        model = models.BlockMarquee
        fields = [
            "id",
            "label",
            "repeat",
            "overlay",
            "pauseOnHover",
            "orientation",
            "reverse",
            "blocks",
        ]

    def create(self, validated_data):
        with transaction.atomic():
            blocks = validated_data.pop("blocks", None)
            marquee = models.BlockMarquee.objects.create(**validated_data)
            if blocks:
                blocks_process(blocks, marquee)
            return marquee

    def update(self, instance, validated_data):
        with transaction.atomic():
            blocks = validated_data.pop("blocks", None)
            instance = super(BlockMarqueeWriteSerializer, self).update(
                instance, validated_data
            )
            models.Composer.objects.filter(
                local_id=instance.id,
                local_content_type=ContentType.objects.get(model="blockmarquee"),
            ).delete()
            if blocks:
                blocks_process(blocks, instance)
            return instance


class HeaderSerializer(serializers.ModelSerializer):
    in_menu = BlockNAVBARSerializer(read_only=True)
    in_menu_id = serializers.PrimaryKeyRelatedField(
        required=False,
        queryset=models.BlockNAVBAR.objects.all(),
        source="in_menu",
    )
    out_menu = BlockNAVBARSerializer(read_only=True)
    out_menu_id = serializers.PrimaryKeyRelatedField(
        required=False,
        queryset=models.BlockNAVBAR.objects.all(),
        source="out_menu",
    )

    class Meta:
        model = models.Header
        fields = ["id", "in_menu", "in_menu_id", "out_menu", "out_menu_id"]


class FooterReadSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    back_image = BlockMEDIASerializer(read_only=True)
    back_image_id = serializers.PrimaryKeyRelatedField(
        allow_null=True,
        required=False,
        queryset=models.BlockMEDIA.objects.all(),
        source="back_image",
    )
    blocks = serializers.SerializerMethodField()

    class Meta:
        model = models.Footer
        fields = [
            "id",
            "design",
            "back_image",
            "back_image_id",
            "blocks",
        ]

    def get_blocks(self, obj) -> list:
        return get_any_blocks(
            obj, "footer", context={"request": self.context.get("request")}
        )


class FooterWriteSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    back_image = BlockMEDIASerializer(read_only=True)
    back_image_id = serializers.PrimaryKeyRelatedField(
        allow_null=True,
        required=False,
        queryset=models.BlockMEDIA.objects.all(),
        source="back_image",
    )
    blocks = serializers.ListField(write_only=True)

    class Meta:
        model = models.Footer
        fields = [
            "id",
            "design",
            "back_image",
            "back_image_id",
            "blocks",
        ]

    def update(self, instance, validated_data):
        with transaction.atomic():
            blocks = validated_data.pop("blocks", None)
            instance = super(FooterWriteSerializer, self).update(
                instance, validated_data
            )
            models.Composer.objects.filter(
                local_id=instance.id,
                local_content_type=ContentType.objects.get(model="footer"),
            ).delete()
            if blocks:
                blocks_process(blocks, instance)
            return instance


class LandingReadSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    customers_blocks = serializers.SerializerMethodField()
    guess_blocks = serializers.SerializerMethodField()

    class Meta:
        model = models.Landing
        fields = [
            "id",
            "customers_blocks",
            "guess_blocks",
        ]

    def get_customers_blocks(self, obj) -> list:
        return get_any_blocks(
            obj, "landing", self.context, "customer"
        )

    def get_guess_blocks(self, obj) -> list:
        return get_any_blocks(
            obj, "landing", self.context, "guess"
        )


class LandingWriteSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    customers_blocks = serializers.ListField(write_only=True)
    guess_blocks = serializers.ListField(write_only=True)

    class Meta:
        model = models.Landing
        fields = [
            "id",
            "customers_blocks",
            "guess_blocks",
        ]

    def update(self, instance, validated_data):
        with transaction.atomic():
            customers_blocks = validated_data.pop("customers_blocks", None)
            guess_blocks = validated_data.pop("guess_blocks", None)
            instance = super(LandingWriteSerializer, self).update(
                instance, validated_data
            )
            try:
                local_content_type = ContentType.objects.get(model="landing")
            except ContentType.DoesNotExist as exception:
                raise ItemRequiredForModelException() from exception
            models.Composer.objects.filter(
                local_id=instance.id,
                local_content_type=local_content_type,
                field_name="customer",
            ).delete()
            if customers_blocks:
                blocks_process(customers_blocks, instance, "customer")
            models.Composer.objects.filter(
                local_id=instance.id,
                local_content_type=local_content_type,
                field_name="guess",
            ).delete()
            if guess_blocks:
                blocks_process(guess_blocks, instance, "guess")
            return instance


class ShopPageReadSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    blocks = serializers.SerializerMethodField()

    class Meta:
        model = models.ShopPage
        fields = [
            "id",
            "title",
            "design",
            "orientation",
            "blocks",
        ]

    def get_blocks(self, obj) -> list:
        return get_any_blocks(
            obj, "shoppage", context={"request": self.context.get("request")}
        )


class ShopPageWriteSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    blocks = serializers.ListField(write_only=True)

    class Meta:
        model = models.ShopPage
        fields = [
            "id",
            "title",
            "design",
            "orientation",
            "blocks",
        ]

    def update(self, instance, validated_data):
        with transaction.atomic():
            blocks = validated_data.pop("blocks", None)
            instance = super(ShopPageWriteSerializer, self).update(
                instance, validated_data
            )
            models.Composer.objects.filter(
                local_id=instance.id,
                local_content_type=ContentType.objects.get(model="shoppage"),
            ).delete()
            if blocks:
                blocks_process(blocks, instance)
            return instance


class BlogPageReadSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    header_blocks = serializers.SerializerMethodField()
    footer_blocks = serializers.SerializerMethodField()

    class Meta:
        model = models.BlogPage
        fields = [
            "id",
            "title",
            "design",
            "orientation",
            "header_blocks",
            "footer_blocks",
        ]

    def get_header_blocks(self, obj) -> list:
        return get_any_blocks(
            obj, "blogpage", {"request": self.context.get("request")}, "header"
        )

    def get_footer_blocks(self, obj) -> list:
        return get_any_blocks(
            obj, "blogpage", {"request": self.context.get("request")}, "footer"
        )


class BlogPageWriteSerializer(serializers.ModelSerializer):
    """_summary_

    Args:
        serializers (_type_): _description_
    """

    header_blocks = serializers.ListField(write_only=True)
    footer_blocks = serializers.ListField(write_only=True)

    class Meta:
        model = models.BlogPage
        fields = [
            "id",
            "title",
            "design",
            "orientation",
            "header_blocks",
            "footer_blocks",
        ]

    def update(self, instance, validated_data):
        with transaction.atomic():
            header_blocks = validated_data.pop("header_blocks", None)
            footer_blocks = validated_data.pop("footer_blocks", None)
            instance = super(BlogPageWriteSerializer, self).update(
                instance, validated_data
            )
            try:
                local_content_type = ContentType.objects.get(model="blogpage")
            except ContentType.DoesNotExist as exception:
                raise ItemRequiredForModelException() from exception
            models.Composer.objects.filter(
                local_id=instance.id,
                local_content_type=local_content_type,
                field_name="header",
            ).delete()
            if header_blocks:
                blocks_process(header_blocks, instance, "header")
            models.Composer.objects.filter(
                local_id=instance.id,
                local_content_type=local_content_type,
                field_name="footer",
            ).delete()
            if footer_blocks:
                blocks_process(footer_blocks, instance, "footer")
            return instance
