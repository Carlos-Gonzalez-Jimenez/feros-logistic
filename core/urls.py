from django.urls import include, path
from rest_framework import routers

from core import views

router = routers.DefaultRouter()

router.register(r"currencies", views.CurrencyViewSet, basename="currencies")
router.register(r"countries", views.CountryViewSet, basename="countries")
router.register(r"brands", views.BrandViewSet, basename="brands")
router.register(r"providers", views.ProviderViewSet, basename="providers")
router.register(r"categories", views.CategoryViewSet, basename="categories")
router.register(r"notifications", views.NotificationViewSet, basename="notifications")
router.register(
    r"notification-types", views.NotificationTypeViewSet, basename="notification-types"
)
router.register(
    r"notification-users", views.NotificationUserViewSet, basename="notification-users"
)
router.register(
    r"measurement-units", views.MeasurementUnitViewSet, basename="measurement-units"
)
router.register(r"products", views.ProductViewSet, basename="products")
router.register(
    r"specifications", views.SpecificationsViewSet, basename="specifications"
)
router.register(
    r"specification-details",
    views.SpecificationDetailsViewSet,
    basename="specification-details",
)
router.register(r"presentations", views.PresentationViewSet, basename="presentations")
router.register(
    r"product-providers",
    views.ProductProviderViewSet,
    basename="product-providers",
)
router.register(r"ports", views.PortViewSet, basename="ports")
router.register(r"incoterms", views.IncotermsViewSet, basename="incoterms")
router.register(
    r"processing-plants", views.ProcessingPlantViewSet, basename="processing-plants"
)
router.register(
    r"purchase-orders", views.PurchaseOrderViewSet, basename="purchase-orders"
)
router.register(r"sale-orders", views.SaleOrderViewSet, basename="sale-orders")
router.register(r"vessels", views.VesselViewSet, basename="vessels")
router.register(
    r"container-types", views.ContainerTypeViewSet, basename="container-types"
)
router.register(
    r"shipping-companies", views.ShippingCompanyViewSet, basename="shipping-companies"
)
router.register(
    r"payment-agreements", views.PaymentAgreementViewSet, basename="payment-agreements"
)
router.register(r"bookings", views.BookingViewSet, basename="bookings")
router.register(r"containers", views.ContainerViewSet, basename="containers")
router.register(
    r"shipping-company-invoices",
    views.ShippingCompanyInvoiceViewSet,
    basename="shipping-company-invoices",
)
router.register(
    r"provider-invoices", views.ProviderInvoiceViewSet, basename="provider-invoices"
)
router.register(
    r"invoice-payments", views.InvoicePaymentViewSet, basename="invoice-payments"
)

urlpatterns = [
    path("", include(router.urls)),
    path(
        r"product-provider-presentations",
        views.ProductProviderPresentationsListAPIView.as_view(),
        name="product-provider-presentations",
    ),
    path(
        "product/<slug:slug>/",
        views.ProductSlugView.as_view(),
        name="product-slug-detail",
    ),
    path(
        "categories-with-products/",
        views.CategoriesWithProductsView.as_view(),
        name="categories-with-products",
    ),
    path(
        "countries-with-products/",
        views.CountriesWithProductsView.as_view(),
        name="countries-with-products",
    ),
    path("configs/", views.ConfigAPIView.as_view(), name="configs"),
]
