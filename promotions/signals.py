from django.db import transaction
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from promotions.exceptions import AssignCouponsException

from user.models import User
from promotions import models


@receiver(post_save, sender=User)
def assign_coupons_on_signup(sender, instance, created, **kwargs):
    """
    Asigna cupones automáticamente cuando un usuario se registra
    """
    if not created:
        return

    try:
        with transaction.atomic():
            signup_coupons = models.Coupon.objects.filter(
                auto_assign_on_signup=True, active=True
            )

            assigned_count = 0
            for coupon in signup_coupons:
                is_valid, message = coupon.is_valid()

                if is_valid:
                    models.CouponAssignment.objects.create(
                        user=instance,
                        coupon=coupon,
                        assigned_type="signup",
                        notes=f"Cupón asignado automáticamente al registrarse el {timezone.now().strftime('%Y-%m-%d')}",
                    )
                    coupon.users_used.add(instance)
                    assigned_count += 1
    except Exception as exception:
        raise AssignCouponsException from exception
