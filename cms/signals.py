from django.core.cache import cache
from django.db.models.signals import post_save
from cms import models
from django.apps import apps


def refresh_cache_for_related_blocks(sender, instance, created, **kwargs):
    if cache.add('clearing-cms', 1, timeout=2):
        pass
        #cache.delete_pattern('cms.*')


cms_config = apps.get_app_config('cms')

for key,model_class in cms_config.models.items():
    if 'block' in key:
        post_save.connect(refresh_cache_for_related_blocks, sender=model_class)