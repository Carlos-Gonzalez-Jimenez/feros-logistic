from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db import transaction

from cms.models import Blocks, RelationShips


class Command(BaseCommand):
    PAGES_RELATIONSHIPS = {
        "blockmarkdown": "A",
        "blockhtml": "A",
        "blockmedia": "S",
        "blockmediacard": "A",
        "blockbutton": "A",
        "blockcarousel": "A",
        "blockcard": "A",
        "blockcardgroup": "A",
        "blockcontainer": "A",
        "blockhero": "A",
        "blockcta": "A",
        "category": "S",
        "product": "S",
        "post": "S",
        "brand": "S",
        "blockfilterproduct": "A",
        "blockfilterpost": "A",
        "blockfilterbrand": "A"
    }

    relationships = {
        # COMPONENTS
        "blockcarousel": {
            "blockhtml": "A",
            "blockmedia": "S",
            "blockmediacard": "A",
            "blockcard": "A",
            "blockcardgroup": "A",
            "blockcontainer": "A",
            "blockhero": "A",
            "blockcta": "A",
            "category": "S",
            "product": "S",
            "post": "S",
            "blockfilterproduct": "A",
            "blockfilterpost": "A",
            "blockfilterbrand": "A"
        },
        "blockcardgroup": {
            "blockmedia": "S",
            "blockmediacard": "A",
            "blockcard": "A",
            "category": "S",
            "product": "S",
            "post": "S",
            "brand": "S",
            "blockfilterproduct": "A",
            "blockfilterpost": "A",
            "blockfilterbrand": "A"
        },
        "blockcontainer": {
            "blockhtml": "A",
            "blockmarkdown": "A",
            "blockmedia": "S",
            "blockmediacard": "A",
            "blockcarousel": "A",
            "blockcard": "A",
            "blockcardgroup": "A",
            "blockhero": "A",
            "blockcta": "A",
            "category": "S",
            "product": "S",
            "post": "S",
            "blockfilterproduct": "A",
            "blockfilterpost": "A",
            "blockfilterbrand": "A"
        },
        "blockhero": {
            "blockhtml": "A",
            "blockmedia": "S",
            "blockmediacard": "A",
            "blockcarousel": "A",
            "blockcard": "A",
            "blockcardgroup": "A",
            "blockcontainer": "A",
            "blockfooterlinks": "A",
            "blockcta": "A",
            "category": "S",
            "product": "S",
            "post": "S",
            "blockfilterproduct": "A",
            "blockfilterpost": "A",
            "blockfilterbrand": "A"
        },
        "blockcta": {
            "blockhtml": "A",
            "blockmedia": "S",
            "blockmediacard": "A",
            "blockcarousel": "A",
            "blockcard": "A",
            "blockcardgroup": "A",
            "blockcontainer": "A",
            "blockhero": "A",
            "category": "S",
            "product": "S",
            "post": "S",
            "blockfilterproduct": "A",
            "blockfilterpost": "A",
            "blockfilterbrand": "A"
        },

        # PAGES
        "landing": {
            "blockhtml__guess": "A",
            "blockmedia__guess": "S",
            "blockmediacard__guess": "A",
            "blockbutton__guess": "A",
            "blockcarousel__guess": "A",
            "blockcard__guess": "A",
            "blockcardgroup__guess": "A",
            "blockcontainer__guess": "A",
            "blockhero__guess": "A",
            "blockcta__guess": "A",
            "category__guess": "S",
            "product__guess": "S",
            "post__guess": "S",
            "blockfilterproduct__guess": "A",
            "blockfilterpost__guess": "A",
            "blockfilterbrand__guess": "A",
            # CUSTOMER
            "blockhtml__customer": "A",
            "blockmedia__customer": "S",
            "blockmediacard__customer": "A",
            "blockbutton__customer": "A",
            "blockcarousel__customer": "A",
            "blockcard__customer": "A",
            "blockcardgroup__customer": "A",
            "blockcontainer__customer": "A",
            "blockhero__customer": "A",
            "blockcta__customer": "A",
            "category__customer": "S",
            "product__customer": "S",
            "post__customer": "S",
            "blockfilterproduct__customer": "A",
            "blockfilterpost__customer": "A",
            "blockfilterbrand__customer": "A",

        },
        "blogpage": PAGES_RELATIONSHIPS,
        "shoppage": PAGES_RELATIONSHIPS,
        "page": PAGES_RELATIONSHIPS,
        "product": PAGES_RELATIONSHIPS,
        "post": PAGES_RELATIONSHIPS,
        "footer": {
            "blockfooterlinks": "A"
        }
    }
    help = "Upgrade the relationships table"

    def parse_relationship_key(self, relationship__item):
        if '__' in relationship__item:
            block_type, field_name = relationship__item.split('__', 1)
        else:
            block_type, field_name = relationship__item, None
        return block_type, field_name

    def handle(self, *args, **options):
        with transaction.atomic():
            content_types = dict()
            for content_type in ContentType.objects.all():
                content_types.setdefault(content_type.model, content_type)

            blocks = dict()
            for block in Blocks.objects.select_related('content_type').all():
                blocks.setdefault(block.content_type.model, block)

            RelationShips.objects.all().delete()
            for item in self.relationships.keys():
                local_content_type = content_types[item]
                for relationship__item in self.relationships[item]:
                    block_type, field_name = self.parse_relationship_key(relationship__item)
                    block = blocks[block_type]
                    _type = self.relationships[item][relationship__item]

                    RelationShips.objects.create(block=block, local_content_type=local_content_type, type=_type,
                                                 field_name=field_name)
