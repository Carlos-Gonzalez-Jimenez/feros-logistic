from django.urls import include, path
from rest_framework.routers import DefaultRouter

from dashboard import views

router = DefaultRouter()
router.register(r"products", views.DashboardProductsViewSet, basename="products")
router.register(r"orders", views.DashboardOrdersViewSet, basename="orders")
router.register(r"users", views.DashboardUsersViewSet, basename="users")

urlpatterns = [
    path("", include(router.urls)),
]
