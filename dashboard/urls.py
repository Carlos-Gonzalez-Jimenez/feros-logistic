from django.urls import include, path
from rest_framework.routers import DefaultRouter

from core.models import ProviderInvoice, ShippingCompanyInvoice
from core.serializers import ProviderInvoiceSerializer, ShippingCompanyInvoiceSerializer
from dashboard import views

router = DefaultRouter()
router.register(r"bookings", views.DashboardBookingViewSet, basename="bookings")
router.register(r"invoices", views.DashboardInvoiceViewSet, basename="invoices")
# router.register(r"orders", views.DashboardOrdersViewSet, basename="orders")
# router.register(r"users", views.DashboardUsersViewSet, basename="users")

urlpatterns = [
    path(r"", include(router.urls)),
    # path(r"invoices/provider/expired", views.ExpiredInvoicesReports.as_view(
    #     queryset=ProviderInvoice.objects.all(),
    #     serializer_class=ProviderInvoiceSerializer
    # ), name="invoices-provider-expired"),
    # path(r"invoices/shipping-company/expired", views.ExpiredInvoicesReports.as_view(
    #     queryset=ShippingCompanyInvoice.objects.all(),
    #     serializer_class=ProviderInvoiceSerializer
    # ), name="invoices-provider-expired"),
    # path(r"invoices/provider/unpaid", views.UnpaidInvoicesReports.as_view(
    #     queryset=ProviderInvoice.objects.all(),
    #     serializer_class=ProviderInvoiceSerializer
    # ), name="invoices-provider-unpaid"),
    # path(r"invoices/shipping-company/unpaid", views.UnpaidInvoicesReports.as_view(
    #     queryset=ShippingCompanyInvoice.objects.all(),
    #     serializer_class=ShippingCompanyInvoiceSerializer
    # ), name="invoices-shipping-company-unpaid")



    #TODO PROGRAMAR LOS PROXIMOS CUTOFF
    #TODO PROGRAMAR LOS PROXIMOS ETA
    #TODO PROGRAMAR LOS CONTENEDORES SIN DEVOLVER Y EL TIEMPO DE ESTADIA
]
