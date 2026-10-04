from django.urls import include, path
from rest_framework import routers

from file_manager import views

router = routers.DefaultRouter()
router.register(r'folders', views.FolderViewSet, basename='folders')
router.register(r'files', views.FileViewSet, basename='files')

urlpatterns = [
    path("", include(router.urls)),
]
