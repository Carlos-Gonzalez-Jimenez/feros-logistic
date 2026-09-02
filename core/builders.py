import datetime
from decimal import Decimal

from django.utils.timezone import now

from core.models import (
    OrderTracking,
    Product,
    OrderProducts,
    BatchItem, ProductBatch,
    Config,
    Order,
    OrderStatus,
)
from core.odoo import sync_order_with_odoo_task
from delivery.models import OrderShipping
from payments.services import PaymentFactory
from promotions.models import CouponUsage


class CreateOrderBuilder:

    def __init__(self, cart_class, validated_data, client, seller=None):
        self.client = client
        self.seller = seller
        self.cart_products = cart_class.objects.filter(client=client)

        self.delivery_address = validated_data.get("delivery_address_id")
        self.shipping_rate = validated_data.get("shipping_rate_id")
        self.payment_method = validated_data.get("payment_method_id")
        self.credit_type = validated_data.get("credit_type_id")
        self.observations = validated_data.get("observations")
        self.coupons = validated_data.get("coupons_ids", [])
        self.is_paid = validated_data.get('paid')

        self.payment_service = PaymentFactory.create_payment_service(self.payment_method.code_name)

        self.order = None
        self.order_amount = 0
        self.discount_amount = 0
        self.shipping_amount = 0
        self.credit_amount = 0

        self.total_amount = 0

    def __check_order(self):
        if not self.order:
            raise Exception("No order to apply")

    def create_order(self):
        percentual_fee = 0
        fixed_fee = 0
        if self.client.fee is not None:
            percentual_fee = self.client.fee.percentual_fee
            fixed_fee = self.client.fee.fixed_fee

        self.order = Order.objects.create(
            seller=self.seller,
            client=self.client, percentual_fee=percentual_fee, fixed_fee=fixed_fee, observations=self.observations,
        )

    def append_order_products(self):
        self.order_amount = 0
        for cart_product in self.cart_products:
            if cart_product.product.quantity > 0:
                product = cart_product.product
                if product.has_wholesale_price and cart_product.quantity >= product.wholesale_minimum:
                    sell_price = product.sell_wholesale_price(self.client.fee)
                else:
                    sell_price = product.sell_price(self.client.fee)

                order_product = OrderProducts.objects.create(
                    quantity=cart_product.quantity,
                    cost=cart_product.product.cost_price,
                    price=sell_price,
                    order=self.order,
                    product=cart_product.product,
                )
                self.order_amount += cart_product.quantity * sell_price

                batch_items = BatchItem.objects.filter(
                    product=order_product.product, sold=False).order_by("batch__created_at")
                order_product_quantity = order_product.quantity
                for batch_item in batch_items:
                    current_quantity = batch_item.quantity - batch_item.quantity_sold
                    if order_product_quantity <= current_quantity:
                        ProductBatch.objects.create(
                            order_product=order_product,
                            batch_item=batch_item,
                            quantity=order_product_quantity,
                        )
                        break
                    else:
                        ProductBatch.objects.create(
                            order_product=order_product,
                            batch_item=batch_item,
                            quantity=current_quantity,
                        )
                        order_product_quantity -= current_quantity

            product = Product.objects.get(id=cart_product.product.id)
            current_quantity = product.quantity - cart_product.quantity
            product.quantity = (current_quantity if current_quantity >= 0 else Decimal("0.00"))
            if current_quantity == 0:
                product.active = False
            product.save()

        self.total_amount += self.order_amount
        self.order.amount = self.order_amount

    def clear_cart(self):
        self.cart_products.delete()

    def apply_discount(self):
        self.discount_amount = 0
        applied_coupons = []
        for coupon in self.coupons:
            discount_value = 0
            if coupon.is_valid(self.client, self.order_amount, self.cart_products):
                if coupon.coupon_type == "percentage":
                    discount_value = self.order_amount * coupon.discount_value
                else:
                    discount_value = coupon.discount_value

                coupon.uses_count += 1
                applied_coupons.append(
                    CouponUsage(
                        coupon=coupon, user=self.client, order=self.order, discount_amount=discount_value,
                    )
                )
                self.discount_amount += discount_value
        self.total_amount -= self.discount_amount
        CouponUsage.objects.bulk_create(applied_coupons)

    def add_initial_state(self, observations):
        initial_status = OrderStatus.objects.get(initial_status=True)
        OrderTracking.objects.create(order=self.order, status_id=initial_status.id, observations=observations)

    def add_shipping(self):
        if self.delivery_address is not None:
            reference = (f"[{self.delivery_address.reference}]" if self.delivery_address.reference is not None else "")
            OrderShipping.objects.create(
                order=self.order,
                shipping_rate=self.shipping_rate,
                delivery_address=f"{self.delivery_address.address} {self.delivery_address.municipality.name}, {self.delivery_address.municipality.province.name} {reference}",
                shipping_price=self.shipping_rate.price,
            )
            self.shipping_amount = self.shipping_rate.price
            self.total_amount += self.shipping_amount

    def add_credit(self):
        if self.credit_type is not None:
            self.credit_amount = self.total_amount * self.credit_type.percentual_fee + self.credit_type.fixed_fee
            self.total_amount += self.credit_amount

            self.order.credit_type = self.credit_type
            self.order.payment_deadline = (now().date() + datetime.timedelta(days=self.credit_type.total_days))
            self.order.credit_amount = self.credit_amount

    def create_payment(self):
        if self.credit_amount > 0:
            create_payment_args = (
                self.payment_method,
                self.order,
                Decimal(self.credit_amount),
                Decimal(0),
                Decimal(0),
            )
        else:
            create_payment_args = (
                self.payment_method,
                self.order,
                Decimal(self.total_amount),
                Decimal(self.shipping_amount),
                Decimal(self.discount_amount),
            )

        response, payment = self.payment_service.create_payment(*create_payment_args)

        if self.is_paid and payment.status == "pending":
            self.payment_service.check_payment_status(payment, self.seller)

        return response, payment

    def update_order_amounts(self):
        self.order.amount = self.order_amount
        self.order.credit_amount = self.credit_amount
        self.order.total_discount = self.discount_amount
        self.order.pending_amount = self.order.total_amount = Decimal(self.total_amount)
        self.order.save()

    def add_expiration_days(self):
        expiration_days = Config.objects.get().order_expiration_days
        self.order.expiration_date = now() + datetime.timedelta(days=expiration_days)

    def sync_with_odoo(self):
        sync_order_with_odoo_task(self.order)
