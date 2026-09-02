from abc import ABC
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from django.core.cache import cache
from django.db import transaction
from rest_framework.exceptions import APIException

from core.models import Order, OrderStatus, Config
from core.services import NotificationService, get_state_handler
from payments.models import (
    Payment,
    PaymentMethod,
    Wallet,
    TransactionLog,
    WalletOperationalLog,
)
from .exceptions import (
    NotSoportedPaymentMethodException,
    InsufficientWalletBalanceException,
    PaymentNotCompletedException,
)
from .gateways.enzona import EnzonaPaymentGateway
from .gateways.transfermovil import TransfermovilPaymentGateway
from .gateways.tropipay import TropipayPaymentGateway


def create_payment_object(
        payment_method: PaymentMethod,
        order: Order,
        total_amount: Decimal,
        transaction_id: str,
        data=None,
) -> Payment:
    if data is None:
        data = dict()
    config_settings = Config.objects.get()
    commission_applied = config_settings.ecommerce_commission_value
    commission_is_percentage = config_settings.ecommerce_commission_is_percentage
    commission_amount = commission_applied
    if commission_is_percentage:
        commission_amount = (total_amount * commission_applied) / 100
    return Payment.objects.create(
        order=order,
        amount=total_amount,
        ecommerce_commission_amount=commission_amount,
        ecommerce_commission_applied=commission_applied,
        ecommerce_commission_percentage=commission_is_percentage,
        status=Payment.PaymentStatus.Pending,
        payment_method_id=payment_method.id,
        currency_id=payment_method.currency.id,
        exchange_rate=payment_method.currency.exchange_rate,
        exchange_rate_date=payment_method.currency.exchange_rate_date,
        transaction_id=transaction_id,
        data=data,
    )


class IService(ABC):
    def create_payment(
            self,
            payment_method: PaymentMethod,
            order: Order,
            total_amount: Decimal,
            shipping_amount: Decimal = 0,
            discount_amount: Decimal = 0,
    ) -> (dict, Payment):
        transaction_id = f"{payment_method.code_name}_{order}_{total_amount}"
        payment = create_payment_object(payment_method, order, total_amount, transaction_id)
        TransactionLog.objects.create(
            transaction_id=payment.transaction_id,
            payment_status=payment.status,
            description=f"Pago creado de la solicitud {order.id} en el estado 'pendiente' por el monto {total_amount}",
        )
        return dict(to=dict(name="order-id", params=dict(id=order.id), query=dict(completed=True))), payment

    def check_payment_status(self, payment: Payment, user=None) -> str:
        if payment.status == Payment.PaymentStatus.Pending:
            payment.status = Payment.PaymentStatus.Completed
            payment.save()
            TransactionLog.objects.create(
                transaction_id=payment.transaction_id,
                payment_status=payment.status,
                description=f"Pago actualizado de la solicitud {payment.order.id} al estado 'completado' por el monto {payment.amount}. Cobro realizado por {user.first_name} {user.last_name}",
            )
            self.update_pending_amount(payment, user)
        return payment.status

    def callback_payment(self, payment: Payment, data=None) -> dict:
        """SE USA PARA PAGOS AUTOMATICOS"""
        return {}

    def cancel_payment(self, payment: Payment, user=None) -> dict:
        pass

    def complete_payment(self, payment: Payment, user=None) -> dict:
        """SE USA PARA PAGOS AUTOMATICOS"""
        pass

    def update_pending_amount(self, payment: Payment, user=None):
        with transaction.atomic():
            diference = payment.order.pending_amount - payment.amount
            order = payment.order
            if diference >= 0:
                order.pending_amount -= payment.amount
            else:
                order.pending_amount = Decimal("0.00")
                wallet = Wallet.objects.get(user=order.client)
                previous_amount = wallet.amount

                WalletOperationalLog.objects.create(
                    transaction_id=f"DEPOSITO_POR_EXCESO_DE_PAGO_{payment.currency.initials}_{abs(diference)}",
                    description=f"Depósito por exceso de pago a la solicitud {order.id}. Realizado por {user.first_name} {user.last_name}",
                    amount=abs(diference),
                    previous_amount=previous_amount,
                    exchange_rate=payment.exchange_rate,
                    exchange_rate_date=payment.exchange_rate_date,
                    wallet=wallet,
                    currency=payment.currency,
                    charge_for=user,
                )

                wallet.amount += abs(diference)
                wallet.save(update_fields=["amount"])

            order.save()
            if order.pending_amount == 0:
                completed_status = OrderStatus.objects.get(code_name="completed")
                handler = get_state_handler(completed_status, order.current_status.status)
                handler.handle_transition(order, None)

    def change_currency(self, payment_method: PaymentMethod, value: Decimal):
        return value * payment_method.currency.exchange_rate


class CashPayment(IService):
    pass


class WalletPayment(IService):

    def create_payment(
            self,
            payment_method: PaymentMethod,
            order: Order,
            total_amount: Decimal,
            shipping_amount: Decimal = 0,
            discount_amount: Decimal = 0,
    ) -> (dict, Payment):
        response, payment = super().create_payment(payment_method, order,
                                                   total_amount, shipping_amount,
                                                   discount_amount)
        self.check_payment_status(payment, order.client)
        return response, payment

    def check_payment_status(self, payment: Payment, user=None) -> str:
        if payment.status == Payment.PaymentStatus.Pending:
            wallet = Wallet.objects.get(user_id=payment.order.client_id)
            if wallet.amount >= payment.amount:
                previous_amount = wallet.amount
                wallet.amount -= payment.amount
                wallet.save()
                payment.status = Payment.PaymentStatus.Completed
                payment.save()
                TransactionLog.objects.create(
                    transaction_id=payment.transaction_id,
                    payment_status=payment.status,
                    description=f"Pago actualizado de la solicitud {payment.order.id} al estado 'completado' por el monto {payment.amount}",
                )
                WalletOperationalLog.objects.create(
                    transaction_id=f"PAGO_{payment.currency.initials}_{payment.amount}",
                    description=f"Pago de la solicitud de compra {payment.order.id}. Realizado por {payment.order.client.first_name} {payment.order.client.last_name}",
                    amount=payment.amount,
                    previous_amount=previous_amount,
                    exchange_rate=payment.exchange_rate,
                    exchange_rate_date=payment.exchange_rate_date,
                    wallet=wallet,
                    currency=payment.currency,
                    charge_for=payment.order.client,
                )
                self.update_pending_amount(payment, user)
            else:
                raise InsufficientWalletBalanceException()
        return payment.status


class TransfermovilPayment(IService):

    def _create_transfermovil_payment(
            self, payment_method: PaymentMethod, order: Order, total_amount: Decimal
    ):
        config = Config.objects.first()
        total_amount = str(self.__change_currecy(total_amount, payment_method))
        callback_url = cache.get_or_set(
            "transfermovil_callback", config.transfermovil_callback_url
        )
        payload = {
            "request": {
                "Amount": str(total_amount),
                # "Amount": "1.00",
                # "Phone": "54266836",  # TODO BUSCAR LA FORMA DE HACERLO DINAMICO
                "Currency": payment_method.currency.initials,
                "Description": f"Pago del pedio {order.pk}",
                "ExternalId": f"{order.pk}",
                "Source": config.transfermovil_source,
                "UrlResponse": f"{callback_url}/order/{order.pk}/notify",
                "ValidTime": 0,
            }
        }

        return TransfermovilPaymentGateway.get_instance().create_payment(payload)

    def create_payment(
            self,
            payment_method: PaymentMethod,
            order: Order,
            total_amount: Decimal,
            shipping_amount: Decimal = 0,
            discount_amount: Decimal = 0,
    ) -> (dict, Payment):
        transaction_id = f"transfermovil_{order}"
        transfermovil_payment = self._create_transfermovil_payment(payment_method, order, total_amount).json()
        if not transfermovil_payment.get("PayOrderResult").get("Success"):
            raise APIException("Error al conectar con transfermovil", 400)

        payment = create_payment_object(payment_method, order, total_amount, transaction_id, transfermovil_payment)
        TransactionLog.objects.create(
            transaction_id=payment.transaction_id,
            payment_status=payment.status,
            description=f"Pago creado de la solicitud {order.id} en el estado 'pendiente' por el monto {total_amount}",
        )
        return dict(
            to=dict(name="payment-id-transfermovil", params=dict(id=payment.id))
        )

    def check_payment_status(self, payment: Payment, user=None) -> str:
        payment_status = (
            TransfermovilPaymentGateway.get_instance()
            .get_payment_status(payment.order.id)
            .json()
        )
        payment.data = payment_status.get("GetStatusOrderResult")
        if payment.data.get("BankId"):
            payment.status = Payment.PaymentStatus.Completed
            self.update_pending_amount(payment, user)
        payment.save()
        return payment.status

    def complete_payment(self, payment: Payment, user=None) -> dict:
        if self.check_payment_status(payment, user) != Payment.PaymentStatus.Completed:
            raise PaymentNotCompletedException()
        TransactionLog.objects.create(
            transaction_id=payment.transaction_id,
            payment_status=payment.status,
            description=f"Pago actualizado de la solicitud {payment.order.id} al estado 'completado' por el monto {payment.amount}",
        )
        return dict()

    def callback_payment(self, payment: Payment, data=None) -> dict:
        payment.status = self.check_payment_status(payment)

        success_message = f"Pago actualizado de la solicitud {payment.order.id} al estado 'completado' por el monto {payment.amount}"
        failed_message = (
            f"Pago actualizado de la solicitud {payment.order.id} al estado 'cancelado' por el monto {payment.amount}",
        )

        transaction_log = TransactionLog.objects.create(
            transaction_id=payment.transaction_id,
            payment_status=payment.status,
            description=(
                success_message if payment.status == Payment.PaymentStatus.Completed else failed_message
            ),
        )

        is_success = payment.status == Payment.PaymentStatus.Completed
        if is_success:
            order = payment.order
            NotificationService.send_notification(
                "Solicitud pagada",
                f"La solicitud de compra <b>{order}</b> ha sido <b>pagada</b> correctamente",
                [order.client],
                "Informativo",
                ["IN_APP", "WHATSAPP"],
            )

        return {
            "data": {
                "Success": is_success,
                "Status": int(is_success),
                "Resultmsg": transaction_log.description,
            }
        }

    def __change_currecy(self, value: Decimal, payment_method: PaymentMethod):
        return self.change_currency(payment_method, value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class EnzonaPayment(IService):

    def __change_currecy(self, value: Decimal, payment_method: PaymentMethod):
        return self.change_currency(payment_method, value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def _create_enzona_payment(
            self,
            payment_method: PaymentMethod,
            order: Order,
            total_amount: Decimal,
            shipping_amount: Decimal = 0,
            discount_amount: Decimal = 0,
    ):
        items = []
        total = str(self.__change_currecy(total_amount, payment_method))
        shipping = str(self.__change_currecy(shipping_amount, payment_method))
        discount = str(self.__change_currecy(discount_amount, payment_method))
        zero = str(Decimal("0.00"))

        order_products = order.order_products.all()
        for product in order_products:
            price = str(
                self.__change_currecy(
                    product.price * (1 + order.percentual_fee) + order.fixed_fee,
                    payment_method,
                )
            )
            quantity = str(
                product.quantity.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
            )
            items.append(
                dict(
                    quantity=quantity,
                    price=price,
                    name=product.product.name,
                    tax=zero,
                    description=f"Pago del producto {product.product.name}",
                )
            )

        config = Config.objects.first()
        payload = {
            "merchant_uuid": "f2b94d3cb5cd40f59b48b8fb2bc7dedc",  # ID DEL COMERCIO ENZONA
            "merchant_op_id": str(order.id).zfill(12),
            "amount": {
                "total": total,
                "details": {
                    "shipping": shipping,
                    "discount": discount,
                    "tax": zero,
                    "tip": zero,
                },
            },
            "description": f"Pago del pedido {order}",
            "currency": "CUP",
            "items": items,
            "invoice_number": order.id,
            "terminal_id": "ecommerce_website",
            "return_url": f"{config.front_url}/order/{order}/completed",
            "cancel_url": f"{config.front_url}/order/{order}/cancel",
        }
        return EnzonaPaymentGateway.get_instance().create_payment(payload)

    def create_payment(
            self,
            payment_method: PaymentMethod,
            order: Order,
            total_amount: Decimal,
            shipping_amount: Decimal = 0,
            discount_amount: Decimal = 0,
    ) -> (dict, Payment):
        transaction_id = f"enzona_{order}"

        enzona_payment = self._create_enzona_payment(
            payment_method, order, total_amount, shipping_amount
        ).json()
        payment = create_payment_object(
            payment_method, order, total_amount, transaction_id, enzona_payment
        )
        TransactionLog.objects.create(
            transaction_id=payment.transaction_id,
            payment_status=payment.status,
            description=f"Pago creado de la solicitud {order.id} en el estado 'pendiente' por el monto {total_amount}",
        )
        return_url = enzona_payment.get("links")[0].get("href")
        return dict(to=return_url, options=dict(external=True)), payment

    def complete_payment(self, payment: Payment, user=None) -> dict:
        enzona_payment_uuid = payment.data.get("transaction_uuid")
        response = EnzonaPaymentGateway.get_instance().complete_payment(
            enzona_payment_uuid
        )
        if response.status_code != 200:
            raise PaymentNotCompletedException()
        payment.data = response.json()
        payment.status = Payment.PaymentStatus.Completed
        self.update_pending_amount(payment, user)
        payment.save()
        TransactionLog.objects.create(
            transaction_id=payment.transaction_id,
            payment_status=payment.status,
            description=f"Pago actualizado de la solicitud {payment.order.id} al estado 'completado' por el monto {payment.amount}",
        )
        return dict()

    def cancel_payment(self, payment: Payment, user=None) -> dict:
        enzona_payment_uuid = payment.data.get("transaction_uuid")
        response = (
            EnzonaPaymentGateway.get_instance()
            .cancel_payment(enzona_payment_uuid)
            .json()
        )
        payment.data = response
        payment.status = Payment.PaymentStatus.Failed
        payment.save()
        TransactionLog.objects.create(
            transaction_id=payment.transaction_id,
            payment_status=payment.status,
            description=f"Pago actualizado de la solicitud {payment.order.id} al estado 'cancelado' por el monto {payment.amount}",
        )
        return dict()


class TropipayPayment(IService):

    def _create_tropipay_payment(self, payment_method, order, total_amount):
        config = Config.objects.first()

        payload = {
            "concept": f"Pago del pedido {order.pk}",
            "description": f"Completar el pago del pedido {order.pk}",
            "amount": int(total_amount * 100),
            "currency": payment_method.currency.initials,
            "singleUse": True,
            "favorite": False,
            "reasonId": 4,
            # "accountId": config.tropipay_paymentcards_account_id,
            "reference": f"order-{order.pk}",
            "serviceDate": date.today().strftime("%Y-%m-%d"),
            "expirationDays": 1,
            "lang": "es",
            "urlSuccess": f"{config.front_url}/order/{order}/completed",
            "urlFailed": f"{config.front_url}/order/{order}/failed",
            "urlNotification": f"{config.backend_url}/payments/payments/{order.pk}/callback",
            # FOTO DEL NEGOCIO
            # "imageBase":''
            # "paymentMethods": ['EXT', 'TPP'],
            "strictPostalCodeCheck": False,
            "strictAddressCheck": False,
            "client": None,
        }

        return TropipayPaymentGateway.get_instance().createpaymentcards(payload)

    def create_payment(
            self,
            payment_method: PaymentMethod,
            order: Order,
            total_amount: Decimal,
            shipping_amount: Decimal = 0,
            discount_amount: Decimal = 0,
    ) -> (dict, Payment):
        transaction_id = f"tropipay_{order}"
        tropipay_payment = self._create_tropipay_payment(
            payment_method, order, total_amount
        ).json()
        if not tropipay_payment:
            raise APIException("Error al conectar con tropipay", 400)

        print(tropipay_payment)
        payment = create_payment_object(
            payment_method, order, total_amount, transaction_id, tropipay_payment
        )
        TransactionLog.objects.create(
            transaction_id=payment.transaction_id,
            payment_status=payment.status,
            description=f"Pago creado de la solicitud {order.id} en el estado 'pendiente' por el monto {total_amount}",
        )
        return dict(to=tropipay_payment["shortUrl"], options=dict(external=True)), payment

    def check_payment_status(self, payment: Payment, user=None) -> str:
        # TODO COMPROBAR SI PUDE OBTENER CORRECTAMENTE LOS DATOS DEL PAGO Y SI ESTA PAGO
        payment_status = (
            TropipayPaymentGateway.get_instance()
            .get_paymentcard(payment.data.get("id"))
            .json()
        )
        return Payment.PaymentStatus.Completed

    def complete_payment(self, payment: Payment, user=None) -> dict:
        # TODO COMPROBAR SI PUDE OBTENER CORRECTAMENTE LOS DATOS DEL PAGO Y SI ESTA PAGO
        payment_status = (
            TropipayPaymentGateway.get_instance()
            .get_paymentcard(payment.data.get("id"))
            .json()
        )
        payment.status = Payment.PaymentStatus.Completed
        payment.data = payment_status
        payment.save()
        TransactionLog.objects.create(
            transaction_id=payment.transaction_id,
            payment_status=payment.status,
            description=f"Pago actualizado de la solicitud {payment.order.id} al estado 'completado' por el monto {payment.amount}",
        )
        return dict()

    def callback_payment(self, payment: Payment, data=None) -> dict:
        if not TropipayPaymentGateway.get_instance().is_valid_notify_payload(
                data, payment.amount
        ):
            raise APIException("Payload invalido, no pertenece a Tropipay", 400)

        payment.status = Payment.PaymentStatus.Completed if data.get("status") == "OK" else Payment.PaymentStatus.Failed
        payment.data = data
        payment.save()

        success_message = f"Pago actualizado de la solicitud {payment.order.id} al estado 'completado' por el monto {payment.amount}"
        failed_message = (
            f"Pago actualizado de la solicitud {payment.order.id} al estado 'cancelado' por el monto {payment.amount}",
        )

        TransactionLog.objects.create(
            transaction_id=payment.transaction_id,
            payment_status=payment.status,
            description=(
                success_message if payment.status == Payment.PaymentStatus.Completed else failed_message
            ),
        )

        if payment.status == Payment.PaymentStatus.Completed:
            order = payment.order
            NotificationService.send_notification(
                "Solicitud pagada",
                f"La solicitud de compra <b>{order}</b> ha sido <b>pagada</b> correctamente",
                [order.client],
                "Informativo",
                ["IN_APP", "WHATSAPP"],
            )

        return dict()


class PaymentFactory:
    @staticmethod
    def create_payment_service(payment_type: str) -> IService:
        """
        Factory method para crear instancias de servicios de pago
        según el tipo especificado.

        Args:
            payment_type (str): Tipo de pago ('wallet', 'transfermovil', etc.)

        Returns:
            IService: Instancia del servicio de pago correspondiente

        Raises:
            NotSoportedPaymentMethodException: Si el tipo de pago no es soportado
        """
        payment_services = {
            "bank_transfer": CashPayment,
            # "usd_cash": USDCashPayment,
            # "cup_cash": CUPCashPayment,
            "wallet": WalletPayment,
            "transfermovil": TransfermovilPayment,
            "en_zona": EnzonaPayment,
            # "zelle": ZellePayment,
            # "stripe": StripePayment,
            # "paypal": PayPalPayment,
            # "tropipay": TropipayPayment,
        }

        service_class = payment_services.get(payment_type.lower(), CashPayment)
        if not service_class:
            raise NotSoportedPaymentMethodException()

        return service_class()
