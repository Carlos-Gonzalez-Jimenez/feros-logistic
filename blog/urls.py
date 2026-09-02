from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework import routers
from blog import views

router = routers.DefaultRouter()

router.register(
    r"blog-categories", views.BlogCategoryViewSet, basename="blog-categories"
)
router.register(r"tags", views.TagViewSet, basename="tags")
router.register(r"posts", views.PostViewSet, basename="posts")
router.register(r"comments", views.CommentViewSet, basename="comments")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "post/<slug:slug>/",
        views.PostSlugView.as_view(),
        name="post-slug-detail",
    ),
]
