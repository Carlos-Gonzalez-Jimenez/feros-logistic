from django.contrib import admin
from django.db import models
from blog.models import BlogCategory, Tag, Post, Comment

admin.site.register(Post)
admin.site.register(BlogCategory)
admin.site.register(Tag)
admin.site.register(Comment)
