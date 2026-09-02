"""
URL configuration for logistic_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from logistic_backend import settings

openapi_info = openapi.Info(
    title="FEROS LOGISTIC API",
    default_version="v1",
    description="FEROS LOGISTIC API Description",
    terms_of_service="https://www.google.com/policies/terms/",
    contact=openapi.Contact(email="contact@snippets.local"),
    license=openapi.License(name="BSD License"),
)

schema_view = get_schema_view(
    openapi_info,
    public=True,
    permission_classes=[
        permissions.AllowAny,
    ],
)

urlpatterns = (
    [
        path("admin/", admin.site.urls),
        path("user/", include("user.urls")),
        path("core/", include("core.urls")),
        path("cms/", include("cms.urls")),
        path("dashboard/", include("dashboard.urls")),
        path("blog/", include("blog.urls")),
        path("delivery/", include("delivery.urls")),
        path("payments/", include("payments.urls")),
        path("pos/", include("pos.urls")),
        path("promotions/", include("promotions.urls")),
        path(
            "swagger/",
            SpectacularSwaggerView.as_view(url_name="schema"),
            name="swagger-ui",
        ),
        path("schema/", SpectacularAPIView.as_view(), name="schema"),
    ]
    + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
)
