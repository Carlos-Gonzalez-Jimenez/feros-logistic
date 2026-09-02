from django.urls import include, path
from rest_framework import routers
from payments import views

router = routers.DefaultRouter()

router.register(r"wallets", views.WalletViewSet, basename="wallets")
router.register(
    r"transaction-logs", views.TransactionLogViewSet, basename="transaction-logs"
)
router.register(
    r"operational-logs", views.WalletOperationalLogsViewSet, basename="operational-logs"
)
router.register(
    r"payment-methods", views.PaymentMethodViewSet, basename="payment-methods"
)
router.register(r"payments", views.PaymentViewSet, basename="payments")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "conciliation-report/",
        views.PaymentReportViewSet.as_view(),
        name="conciliation-report",
    ),
]
