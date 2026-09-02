from django.urls import include, path
from rest_framework import routers

from core import views
from core import webhooks

router = routers.DefaultRouter()

router.register(r"batchs", views.BatchViewSet, basename="batchs")
router.register(r"batch-items", views.BatchItemViewSet, basename="batch-items")
router.register(r"currencies", views.CurrencyViewSet, basename="currencies")
router.register(r"countries", views.CountryViewSet, basename="countries")
router.register(r"brands", views.BrandViewSet, basename="brands")
router.register(r"providers", views.ProviderViewSet, basename="providers")
router.register(r"categories", views.CategoryViewSet, basename="categories")
router.register(r"order-statuses", views.OrderStatusViewSet, basename="order-statuses")
router.register(r"credit-types", views.CreditTypeViewSet, basename="credit-types")
router.register(r"notifications", views.NotificationViewSet, basename="notifications")
router.register(r"notification-types", views.NotificationTypeViewSet, basename="notification-types")
router.register(r"notification-users", views.NotificationUserViewSet, basename="notification-users")
router.register(r"measurement-units", views.MeasurementUnitViewSet, basename="measurement-units")
router.register(r"products", views.ProductViewSet, basename="products")
router.register(r"reviews", views.ReviewViewSet, basename="reviews")
router.register(r"provinces", views.ProvinceViewSet, basename="provinces")
router.register(r"municipalities", views.MunicipalityViewSet, basename="municipalities")
router.register(r"carts", views.CartViewSet, basename="carts")
router.register(r"orders", views.OrderViewSet, basename="orders")
router.register(r"specifications", views.SpecificationsViewSet, basename="specifications")
router.register(r"specification-details", views.SpecificationDetailsViewSet, basename="specification-details")
router.register(r"vehicle-types", views.VehicleTypeViewSet, basename="vehicle-types")
router.register(r"vehicles", views.VehicleViewSet, basename="vehicles")
router.register(r"order-products", views.OrderProductsViewSet, basename="order-products")
router.register(r"addresses", views.ContactAddressViewSet, basename="addresses")

urlpatterns = [
    path("", include(router.urls)),
    path("product/<slug:slug>/", views.ProductSlugView.as_view(), name="product-slug-detail"),
    path("shops", views.ShopViewSet.as_view(), name="shops"),
    path("categories-with-products/", views.CategoriesWithProductsView.as_view(), name="categories-with-products"),
    path("countries-with-products/", views.CountriesWithProductsView.as_view(), name="countries-with-products"),
    path("products-profit/", views.OrderProfitReportViewSet.as_view(), name="products-profit"),
    path("batch-sales/", views.BatchSalesReportView.as_view(), name="batch-sales"),
    path("configs/", views.ConfigAPIView.as_view(), name="configs"),
    path("webhooks/odoo", webhooks.OdooSaleWebhook.as_view(), name='odoo-webhooks')
]
