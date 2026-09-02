from PIL import Image
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
import io

from cms.models import BlockMEDIA


class Command(BaseCommand):
    """script to seed database

    Args:
        BaseCommand (_type_): _description_
    """

    help = "Upgrade the database with data for fix and generate information."

    def handle(self, *args, **options):
        images = BlockMEDIA.objects.filter(media_group='products').all()

        for block in images:
            img = Image.open(block.media)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            buffer = io.BytesIO()

            img.save(buffer, format=img.format, optimize=True)
            buffer.seek(0)

            filename = block.media.name.split('/')[-1]
            block.media.delete()
            block.media.save(filename, ContentFile(buffer.read()))

            print(f"Comprimida: {block.media.name}")
