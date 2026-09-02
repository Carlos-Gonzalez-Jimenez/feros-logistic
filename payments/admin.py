from django.contrib import admin
from payments.models import (
    Wallet,
    Payment,
    TransactionLog,
    PaymentMethod,
    WalletOperationalLog,
)

admin.site.register(Wallet)
admin.site.register(TransactionLog)
admin.site.register(Payment)
admin.site.register(PaymentMethod)
admin.site.register(WalletOperationalLog)
