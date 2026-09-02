from django.contrib import admin
from delivery.models import (
    ShippingMethod,
    ShippingRate,
    ShippingZone,
    OrderShipping,
)

admin.site.register(ShippingZone)
admin.site.register(ShippingMethod)
admin.site.register(ShippingRate)
admin.site.register(OrderShipping)
