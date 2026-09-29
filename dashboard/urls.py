from django.urls import include, path
from rest_framework.routers import DefaultRouter

from dashboard import views

router = DefaultRouter()
router.register("bookings", views.DashboardBookingViewSet, basename="bookings")
router.register("invoices", views.DashboardInvoiceViewSet, basename="invoices")
router.register("containers", views.DashboardContainerViewSet, basename="containers")

urlpatterns = [
    path(r"", include(router.urls)),
]
