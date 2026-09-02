from django.urls import include, path
from rest_framework import routers
from promotions import views

router = routers.DefaultRouter()

router.register(r"coupons", views.CouponViewSet, basename="coupons")
router.register(r"coupon-usage", views.CouponUsageViewSet, basename="coupon-usage")

urlpatterns = [
    path(
        "coupons/valid/",
        views.UserValidCouponsAPIView.as_view(),
        name="user-valid-coupons",
    ),
    path("", include(router.urls)),
]
