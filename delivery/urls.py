from django.urls import include, path
from rest_framework import routers
from delivery import views

router = routers.DefaultRouter()

router.register(
    r"shipping-methods", views.ShippingMethodViewSet, basename="shipping-methods"
)
router.register(r"shipping-zones", views.ShippingZoneViewSet, basename="shipping-zones")
router.register(r"shipping-rates", views.ShippingRateViewSet, basename="shipping-rates")
router.register(
    r"shipping-orders", views.OrderShippingViewSet, basename="shipping-orders"
)

urlpatterns = [
    path("assign-orders-to-deliverer", views.AssignOrdersToDelivererView.as_view()),
    path("orders-ready-to-ship", views.OrdersReadyToShipWithoutDelivererView.as_view()),
    path("", include(router.urls)),
]
