from django.urls import include, path
from rest_framework.routers import DefaultRouter

from dashboard import views

router = DefaultRouter()
router.register("bookings", views.DashboardBookingViewSet, basename="bookings")
router.register("invoices", views.DashboardInvoiceViewSet, basename="invoices")
router.register("containers", views.DashboardContainerViewSet, basename="containers")
# router.register(r"orders", views.DashboardOrdersViewSet, basename="orders")
# router.register(r"users", views.DashboardUsersViewSet, basename="users")

urlpatterns = [
    path(r"", include(router.urls)),
]
