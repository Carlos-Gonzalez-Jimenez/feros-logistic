from django.contrib import admin
from django.db import models
from parler.admin import TranslatableAdmin

from blog.models import BlogCategory, Tag, Post, Comment

admin.site.register(Comment)
admin.site.register(Post, TranslatableAdmin)
admin.site.register(Tag, TranslatableAdmin)
admin.site.register(BlogCategory, TranslatableAdmin)
