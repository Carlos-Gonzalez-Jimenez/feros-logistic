from django.urls import include, path
from rest_framework import routers
from pos import views

router = routers.DefaultRouter()
router.register(r"carts", views.PosCartViewSet, basename="carts")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "shops",
        views.PosShopViewSet.as_view(),
        name="shops",
    ),
    path(
        "coupons/valid/",
        views.UserValidPosCouponsAPIView.as_view(),
        name="user-valid-coupons",
    ),
]
