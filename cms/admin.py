from django.contrib import admin
from django.db import models
from cms.models import (
    Page,
    BlockHTML,
    BlockMEDIA,
    BlockMEDIACARD,
    BlockBUTTON,
    BlockCAROUSEL,
    BlockCARDGROUP,
    BlockCARD,
    BlockHERO,
    BlockCTA,
    BlockNAVBAR,
    BlockFOOTERLINKS,
    BlockCONTAINER,
    BlockMarquee,
    Composer,
    RelationShips,
    Blocks,
    Header,
    Footer,
    Landing,
    ShopPage,
    BlogPage,
    BlockFilterProduct,
    BlockFilterPost, BlockFilterBrand, BlockMarkdown,
)


def CustomModelAdmin(model):
    return type(
        "SubClass" + model.__name__,
        (admin.ModelAdmin,),
        {
            "list_display": [x.name for x in model._meta.fields],
            "list_select_related": [
                x.name
                for x in model._meta.fields
                if isinstance(
                    x,
                    (
                        models.ManyToOneRel,
                        models.ForeignKey,
                        models.OneToOneField,
                    ),
                )
            ],
            "search_fields": ["id"],
            "list_display_links": ["id"],
        },
    )


admin.site.site_header = "Administración ECOMMERCE"
admin.site.index_title = "Panel de control del ECOMMERCE"

admin.site.register(Page, CustomModelAdmin(Page))
admin.site.register(BlockHTML, CustomModelAdmin(BlockHTML))
admin.site.register(BlockMarkdown, CustomModelAdmin(BlockMarkdown))
admin.site.register(BlockMEDIA, CustomModelAdmin(BlockMEDIA))
admin.site.register(BlockBUTTON, CustomModelAdmin(BlockBUTTON))
admin.site.register(BlockCAROUSEL, CustomModelAdmin(BlockCAROUSEL))
admin.site.register(BlockCARDGROUP, CustomModelAdmin(BlockCARDGROUP))
admin.site.register(BlockCARD, CustomModelAdmin(BlockCARD))
admin.site.register(BlockHERO, CustomModelAdmin(BlockHERO))
admin.site.register(BlockCTA, CustomModelAdmin(BlockCTA))
admin.site.register(BlockMarquee, CustomModelAdmin(BlockMarquee))
admin.site.register(BlockNAVBAR, CustomModelAdmin(BlockNAVBAR))
admin.site.register(BlockFOOTERLINKS, CustomModelAdmin(BlockFOOTERLINKS))
admin.site.register(Composer, CustomModelAdmin(Composer))
admin.site.register(RelationShips, CustomModelAdmin(RelationShips))
admin.site.register(Blocks, CustomModelAdmin(Blocks))
admin.site.register(Header, CustomModelAdmin(Header))
admin.site.register(Footer, CustomModelAdmin(Footer))
admin.site.register(Landing, CustomModelAdmin(Landing))
admin.site.register(BlockMEDIACARD, CustomModelAdmin(BlockMEDIACARD))
admin.site.register(BlockCONTAINER, CustomModelAdmin(BlockCONTAINER))
admin.site.register(ShopPage, CustomModelAdmin(ShopPage))
admin.site.register(BlogPage, CustomModelAdmin(BlogPage))
admin.site.register(BlockFilterProduct, CustomModelAdmin(BlockFilterProduct))
admin.site.register(BlockFilterPost, CustomModelAdmin(BlockFilterPost))
admin.site.register(BlockFilterBrand, CustomModelAdmin(BlockFilterBrand))
