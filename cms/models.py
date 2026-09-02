from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.generics import PermissionsMeta


class BlockHTML(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    label = models.CharField(max_length=1024, blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    styles = models.JSONField(default=dict)

    def __str__(self):
        return self.label

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Block HTML"
        verbose_name_plural = "Blocks HTML"
        ordering = ["-id"]


MEDIA_GROUP_CHOICES = (
    ("products", "Productos"),
    ("cms", "Contenido"),
    ("blog", "Publicaciones"),
)

ORIENTATION_CHOICES = (("horizontal", "Horizontal"), ("vertical", "Vertical"))

MEDIA_CARD_TYPES_CHOICES = (("simple", "Simple"), ("responsive", "Responsive"))


def media_group_directory_path(instance, filename):
    return f"{instance.media_group}/pics/{filename}"


class BlockMEDIA(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    media_group = models.CharField(
        max_length=255, choices=MEDIA_GROUP_CHOICES, default=""
    )
    media = models.FileField(upload_to=media_group_directory_path)

    def __str__(self):
        return "Media"

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Block MEDIA"
        verbose_name_plural = "Blocks MEDIA"
        ordering = ["-id"]


class BlockMEDIACARD(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    label = models.CharField(max_length=1024, blank=True, null=True)
    type = models.CharField(
        choices=MEDIA_CARD_TYPES_CHOICES, default="simple", max_length=25
    )

    image = models.ForeignKey(
        BlockMEDIA,
        related_name="media_card_blocks",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    image_sm = models.ForeignKey(
        BlockMEDIA,
        related_name="media_card_blocks_sm",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    image_md = models.ForeignKey(
        BlockMEDIA,
        related_name="media_card_blocks_md",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    image_lg = models.ForeignKey(
        BlockMEDIA,
        related_name="media_card_blocks_lg",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    url = models.CharField(max_length=1024)

    def __str__(self):
        return self.label

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Block MEDIA CARD"
        verbose_name_plural = "Blocks MEDIA CARD"
        ordering = ["-id"]


class BlockBUTTON(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    label = models.CharField(max_length=255)
    color = models.CharField(max_length=255)
    url = models.CharField(max_length=255)

    def __str__(self):
        return self.label

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Block BUTTON"
        verbose_name_plural = "Blocks BUTTON"
        ordering = ["-id"]


DESIGN_CHOICES = (
    ("1/10", "One tenth"),
    ("1/9", "One ninth"),
    ("1/8", "One eighth"),
    ("1/7", "One seventh"),
    ("1/6", "One sixth"),
    ("1/5", "One fifth"),
    ("1/4", "One fourth"),
    ("1/3", "One third"),
    ("1/2", "One half"),
    ("1", "Full width"),
)
TYPE_CHOICES = (("GR", "Grid"), ("FX", "Flex"))
RELATIONSHIP_CHOICES = (("L", "List"), ("C", "Creation"), ("A", "All"))


def default_autoplay_props():
    return {"delay": 3000}


def default_autoscroll_props():
    return {"speed": 2}


class BlockCAROUSEL(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    label = models.CharField(max_length=1024, blank=True, null=True)
    name = models.CharField(max_length=255)
    design = models.CharField(max_length=20, choices=DESIGN_CHOICES)
    indicators = models.BooleanField(default=False)
    autoplay = models.BooleanField(default=False)
    autoplay_props = models.JSONField(default=default_autoplay_props)
    autoscroll = models.BooleanField(default=False)
    autoscroll_props = models.JSONField(default=default_autoscroll_props)
    arrows = models.BooleanField(default=False)
    blocks_orientation = models.CharField(
        max_length=15, choices=ORIENTATION_CHOICES, default="vertical"
    )

    def __str__(self):
        return self.name

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Block CAROUSEL"
        verbose_name_plural = "Blocks CAROUSEL"
        ordering = ["-id"]


class BlockCARD(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    label = models.CharField(max_length=1024, blank=True, null=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    image = models.ForeignKey(
        BlockMEDIA,
        related_name="cards",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    reverse = models.BooleanField(default=False)
    spotlight = models.BooleanField(default=False)
    spotlight_color = models.CharField(max_length=50, blank=True, null=True)
    highlight = models.BooleanField(default=False)
    highlight_color = models.CharField(max_length=50, blank=True, null=True)
    variant = models.CharField(max_length=50, blank=True, null=True)
    url = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.label

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Block CARD"
        verbose_name_plural = "Blocks CARD"
        ordering = ["-id"]


class BlockCARDGROUP(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    title = models.CharField(max_length=255, blank=True, null=True)
    label = models.CharField(max_length=1024, blank=True, null=True)
    subtitle = models.TextField(blank=True, null=True)
    card_group_type = models.CharField(max_length=5, choices=TYPE_CHOICES)
    design = models.CharField(max_length=20, choices=DESIGN_CHOICES)
    justify = models.CharField(max_length=20, default="center")
    orientation = models.CharField(
        max_length=15, choices=ORIENTATION_CHOICES, default="vertical"
    )
    size = models.CharField(max_length=10, blank=True, null=True, default="md")

    def __str__(self):
        return "Block CARD GROUP"

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Block CARD GROUP"
        verbose_name_plural = "Blocks CARD GROUP"
        ordering = ["-id"]


class Blocks(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    name = models.CharField(max_length=255)
    label = models.CharField(max_length=1024)
    color = models.CharField(max_length=255)
    icon = models.CharField(max_length=255)
    content_type = models.ForeignKey(
        ContentType, related_name="content_types", on_delete=models.CASCADE
    )

    def __str__(self):
        return self.content_type.model

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Block"
        verbose_name_plural = "Blocks"
        ordering = ["-id"]


class Composer(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    local_id = models.IntegerField(default=0)
    local_content_type = models.ForeignKey(
        ContentType,
        related_name="local_items",
        on_delete=models.CASCADE,
    )
    item_id = models.IntegerField(default=0)
    block = models.ForeignKey(
        Blocks,
        related_name="related_blocks",
        on_delete=models.CASCADE,
    )
    order = models.IntegerField(default=0)
    field_name = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.local_content_type} [{self.local_id}] => {self.block} [{self.item_id}]"

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Composer"
        verbose_name_plural = "Composers"
        ordering = ["-id"]


class RelationShips(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    local_content_type = models.ForeignKey(
        ContentType, related_name="local_ids", on_delete=models.CASCADE, null=True
    )
    block = models.ForeignKey(
        Blocks, related_name="blocks", on_delete=models.CASCADE, null=True
    )
    type = models.CharField(max_length=5, choices=RELATIONSHIP_CHOICES, default="A")
    field_name = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.local_content_type} => {self.block}"

    class Meta(PermissionsMeta.Meta):
        verbose_name = "RelationShip"
        verbose_name_plural = "RelationShips"
        ordering = ["-id"]


class Page(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    name = models.CharField(max_length=255)
    slug = models.CharField(max_length=255, blank=True, null=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Page"
        verbose_name_plural = "Pages"
        ordering = ["-id"]


class BlockCONTAINER(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    label = models.CharField(max_length=1024, blank=True, null=True)
    back_image = models.ForeignKey(
        BlockMEDIA,
        related_name="container_blocks",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    wide = models.BooleanField(default=True)

    def __str__(self):
        return self.label

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Block Container"
        verbose_name_plural = "Blocks Container"
        ordering = ["-id"]


class BlockFOOTERLINKS(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    title = models.CharField(max_length=255)
    links = models.JSONField(default=list)

    def __str__(self):
        return self.title

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Block FOOTER LINKS"
        verbose_name_plural = "Blocks FOOTER LINKS"
        ordering = ["-id"]


class BlockNAVBAR(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    label = models.CharField(max_length=255)
    items = models.JSONField(default=list)

    def __str__(self):
        return self.label

    class Meta(PermissionsMeta.Meta):
        permissions = [("manage_blocknavbar", _("Can manage nav bar"))]
        verbose_name = "Nav bar"
        verbose_name_plural = "Nav bars"
        ordering = ["-id"]


HERO_TYPE_CHOICES = (("IMG", "Image"), ("GAL", "Gallery"))
HERO_LOCATION_CHOICES = (("Left", "Left"), ("Right", "Right"))


class BlockHERO(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    label = models.CharField(max_length=1024, blank=True, null=True)
    name = models.CharField(max_length=255, default="Bloque HERO")
    hero_type = models.CharField(max_length=5, choices=HERO_TYPE_CHOICES)
    location = models.CharField(max_length=10, choices=HERO_LOCATION_CHOICES)
    image = models.ForeignKey(
        BlockMEDIA,
        related_name="hero_blocks",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    gallery = models.ManyToManyField(BlockMEDIA, related_name="hero")

    def __str__(self):
        return self.name

    class Meta(PermissionsMeta.Meta):
        verbose_name = "HERO block"
        verbose_name_plural = "HERO blocks"
        ordering = ["-id"]


class BlockCTA(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    label = models.CharField(max_length=1024, blank=True, null=True)
    size = models.CharField(max_length=10, blank=True, null=True)
    title = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    orientation = models.CharField(max_length=20, choices=ORIENTATION_CHOICES)
    reverse = models.BooleanField(default=False)
    variant = models.CharField(max_length=25, blank=True, null=True)
    buttons = models.JSONField(default=list)

    def __str__(self):
        return self.description

    class Meta(PermissionsMeta.Meta):
        verbose_name = "CTA block"
        verbose_name_plural = "CTA blocks"
        ordering = ["-id"]


class BlockMarquee(models.Model):
    label = models.CharField(max_length=1024, blank=True, null=True)
    orientation = models.CharField(max_length=20, choices=ORIENTATION_CHOICES)
    reverse = models.BooleanField(default=False)
    overlay = models.BooleanField(default=True)
    pauseOnHover = models.BooleanField(default=True)
    repeat = models.IntegerField(default=4)

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Marquee block"
        verbose_name_plural = "Marquee block"
        ordering = ["-id"]


class Footer(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    design = models.CharField(max_length=10, choices=DESIGN_CHOICES)
    back_image = models.ForeignKey(
        BlockMEDIA,
        related_name="footer",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )

    def __str__(self):
        return "Footer"

    class Meta(PermissionsMeta.Meta):
        permissions = [("manage_footer", _("Can manage footer"))]
        verbose_name = "Footer"
        verbose_name_plural = "Footers"
        ordering = ["-id"]


class Header(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    out_menu = models.ForeignKey(
        BlockNAVBAR, related_name="header_out_menu", on_delete=models.PROTECT
    )
    in_menu = models.ForeignKey(
        BlockNAVBAR, related_name="header_in_menu", on_delete=models.PROTECT
    )

    def __str__(self):
        return "Header"

    class Meta(PermissionsMeta.Meta):
        permissions = [("manage_header", _("Can manage header"))]
        verbose_name = "Header"
        verbose_name_plural = "Headers"
        ordering = ["-id"]


class Landing(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    def __str__(self):
        return "Landing Page"

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Landing Page"
        verbose_name_plural = "Landing Pages"
        ordering = ["-id"]


class ShopPage(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    title = models.CharField(max_length=1024)
    design = models.CharField(max_length=5, choices=DESIGN_CHOICES)
    orientation = models.CharField(
        max_length=15, choices=ORIENTATION_CHOICES, default="vertical"
    )

    def __str__(self):
        return self.title

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Shop Page"
        verbose_name_plural = "Shop Pages"
        ordering = ["-id"]


class BlogPage(models.Model):
    """_summary_

    Args:
        models (_type_): _description_

    Returns:
        _type_: _description_
    """

    title = models.CharField(max_length=1024)
    design = models.CharField(max_length=5, choices=DESIGN_CHOICES)
    orientation = models.CharField(
        max_length=15, choices=ORIENTATION_CHOICES, default="vertical"
    )

    def __str__(self):
        return self.title

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Blog Page"
        verbose_name_plural = "Blog Pages"
        ordering = ["-id"]


class BlockFilter(models.Model):
    label = models.CharField(max_length=1024, blank=True, null=True, default="")
    filters = models.JSONField(null=True, blank=True, default=None)
    exclude = models.JSONField(null=True, blank=True, default=None)
    limit = models.PositiveIntegerField(default=10)
    order_by = models.CharField(max_length=1024, blank=True, null=True)

    class Meta(PermissionsMeta.Meta):
        abstract = True


class BlockFilterProduct(BlockFilter):

    def __str__(self):
        return "Block Filter Product"

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Blog Filter Product"
        verbose_name_plural = "Blog Filter Products"
        ordering = ["-id"]


class BlockFilterPost(BlockFilter):

    def __str__(self):
        return "Block Filter Post"

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Blog Filter Post"
        verbose_name_plural = "Blog Filter Post"
        ordering = ["-id"]


class BlockFilterBrand(BlockFilter):
    variant = models.CharField(max_length=25, blank=True, null=True, default="ghost")
    show_link = models.BooleanField(default=True)

    def __str__(self):
        return "Block Filter Brand"

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Blog Filter Brand"
        verbose_name_plural = "Blog Filter Brands"
        ordering = ["-id"]


class BlockMarkdown(models.Model):
    label = models.CharField(max_length=1024, blank=True, null=True)
    content = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.label

    class Meta(PermissionsMeta.Meta):
        verbose_name = "Block Markdown"
        verbose_name_plural = "Blocks Markdown"
        ordering = ["-id"]
