import datetime
import random
import time
from abc import ABC, abstractmethod
from math import ceil

import requests
from django_q.tasks import async_task

from core import tasks
from core.exceptions import (
    StatusNotAllowedException,
    ConfigurationDoesNotExistException,
)
from core.models import (
    OrderTracking,
    Notification,
    NotificationUser,
    NotificationType,
    Product,
    OrderProducts,
    Config,
    Order,
    OrderStatus,
)
from core.odoo import sync_order_with_odoo_task
from delivery.exceptions import (
    OrderShippingDoesNotExistException,
    OrderHasNotShipingRateException,
)
from delivery.models import OrderShipping
from payments.exceptions import (
    PaymentNotCompletedException,
)


class WAHAService:
    """
    Wrapper para la API WAHA, envia mensajes via WhatsApp

    Raises:
        ConfigurationDoesNotExistException: No existe el archivo de configuración
        ErrorContactingMessagingAPIException: Problemas al contactar la API WAHA

    Returns:
        _type_: _description_
    """

    _initialized = False
    _auth = None
    _api_url = None
    _api_session_name = None

    @classmethod
    def _ensure_initialized(cls):
        if not cls._initialized:
            try:
                config = Config.objects.get()
                cls._auth = (config.waha_api_user, config.waha_api_password)
                cls._headers = {"X-Api-Key": config.waha_api_apikey}
                cls._api_url = config.waha_api_url
                cls._api_session_name = config.waha_api_session
                cls._initialized = True
            except Config.DoesNotExist as exception:
                raise ConfigurationDoesNotExistException() from exception

    @classmethod
    def dev_initialized(cls):
        cls._auth = ("pavelcode5426", "pavelcode5426")
        cls._headers = {"X-Api-Key": "admin"}
        cls._api_url = "https://whatsapp.ferosgrupo.cloud"
        cls._api_session_name = "default"
        cls._initialized = True

    @staticmethod
    def check_exist(phone_number: str) -> dict:
        """
        Verifica si el número telefónico está registrado en WhatsApp

        Args:
            phone_number (str): Número telefónico del cliente

        Returns:
            bool: True | False
        """
        WAHAService._ensure_initialized()
        response = requests.get(
            f"{WAHAService._api_url}/api/contacts/check-exists",
            auth=WAHAService._auth,
            headers=WAHAService._headers,
            params={
                "phone": phone_number,
                "session": WAHAService._api_session_name,
            },
        )
        response.raise_for_status()
        return response.json()

    @staticmethod
    def start_typing(chat_id: str) -> int:
        """
        WhatsApp comienzo de escritura

        Args:
            phone_number (str): Número telefónico del cliente

        Returns:
            int: HTTP código de estado
        """
        WAHAService._ensure_initialized()
        response = requests.post(
            f"{WAHAService._api_url}/api/startTyping",
            auth=WAHAService._auth,
            headers=WAHAService._headers,
            data={"chatId": chat_id, "session": WAHAService._api_session_name},
        )
        response.raise_for_status()
        return response.status_code

    @staticmethod
    def stop_typing(chat_id: str) -> int:
        """
        WhatsApp detener la escrituea

        Args:
            phone_number (str): Número telefónico del cliente

        Returns:
            int: HTTP código de estado
        """
        WAHAService._ensure_initialized()
        response = requests.post(
            f"{WAHAService._api_url}/api/stopTyping",
            headers=WAHAService._headers,
            auth=WAHAService._auth,
            data={"chatId": chat_id, "session": WAHAService._api_session_name},
        )
        response.raise_for_status()
        return response.status_code

    @staticmethod
    def send_text(chat_id: str, message: str) -> int:
        """
        WhatsApp envío de mensaje
        Args:
            phone_number (str): Número telefónico del cliente
            message (str): Mensaje a enviar

        Returns:
            int: HTTP código de estado
        """
        WAHAService._ensure_initialized()
        response = requests.post(
            f"{WAHAService._api_url}/api/sendText",
            headers=WAHAService._headers,
            auth=WAHAService._auth,
            json={
                "chatId": chat_id,
                "reply_to": None,
                "text": message,
                "session": "default",
                "linkPreview": False,
                "linkPreviewHighQuality": False,
            },
        )
        response.raise_for_status()
        return response.status_code

    @staticmethod
    def send_image(chat_id: str, image_url: str, caption: str) -> int:
        """
        WhatsApp enviar imagen

        Args:
            phone_number (str): Número telefónico del cliente
            image_url (str): Imagen a enviar
            caption (str): Texto que acompaña a la imagen
        Returns:
            int: HTTP código de estado
        """

        WAHAService._ensure_initialized()
        response = requests.post(
            f"{WAHAService._api_url}/api/sendImage",
            headers=WAHAService._headers,
            auth=WAHAService._auth,
            data={
                "chatId": chat_id,
                "image": image_url,
                "caption": caption,
                "session": WAHAService._api_session_name,
            },
        )
        response.raise_for_status()
        return response.status_code


def create_notification_task(
        user_ids: list, title: str, final_message: str, notification_type: NotificationType
) -> bool:
    """Crea notificación en BD"""

    notification = Notification.objects.create(title=title, message=final_message, notification_type=notification_type)

    notification_users = []
    for user_id in user_ids:
        notification_users.append(NotificationUser(notification=notification, user_id=user_id))

    NotificationUser.objects.bulk_create(notification_users)
    return True


def create_whatsapp_task(
        whatsapp_chat_id: str,
        final_message: str,
        notification_type: NotificationType,
        typing_duration: float,
) -> bool:
    """Envía notificación por WhatsApp"""
    typing_timer = max(10, ceil(typing_duration))

    while typing_timer > 0:
        WAHAService.start_typing(whatsapp_chat_id)
        typing_timer -= 5
        time.sleep(5)

    WAHAService.stop_typing(whatsapp_chat_id)
    time.sleep(0.5)
    WAHAService.send_text(whatsapp_chat_id, final_message)
    return True


class BaseNotificationChannel(ABC):
    """
    Interfaz base para todos los canales de notificación
    """

    def __init__(self):
        self.channel_type = self.get_channel_type()

    @abstractmethod
    def send(
            self, users, title: str, message: str, notification_type_name: str
    ) -> bool:
        """
        Envía notificación a través del canal seleccionado a todos los destinatarios

        Args:
            users: Destinatarios
            title: Título de la notificación
            message: Mensaje de la notificación
            notification_type_name: Tipo de notificación

        Returns:
            bool: True si se envió correctamente
        """

    @abstractmethod
    def can_send(self, user) -> bool:
        """
        Verifica si el canal puede enviar notificaciones al usuario

        Args:
            user: Usuario a verificar

        Returns:
            bool: True si puede enviar
        """

    @abstractmethod
    def get_channel_type(self) -> str:
        """
        Retorna el tipo de canal

        Returns:
            str: Identificador del canal
        """


class InAppNotificationChannel(BaseNotificationChannel):
    """
    Canal de notificaciones dentro de la aplicación [IN_APP]
    """

    def send(
            self, users: list, title: str, message: str, notification_type_name: str
    ) -> bool:
        """
        Envia notificación

        Args:
            users (list): Lista de destinatarios
            title (str): título de la notificación
            message (str): mensaje
            notification_type_name (str): tipo de notificación

        Returns:
            bool: True si fue posible enviar la notificación
        """
        if not users:
            return True
        try:
            notification_type = NotificationType.objects.get(
                name=notification_type_name
            )
        except NotificationType.DoesNotExist:
            return False
        user_ids = [user.id for user in users]
        async_task(create_notification_task, user_ids, title, message, notification_type)
        return True

    def can_send(self, user):
        return True

    def get_channel_type(self):
        return "IN_APP"


class WhatsAppNotificationChannel(BaseNotificationChannel):
    """
    Canal de notificaciones por WhatsApp [WHATSAPP]

    """

    def send(
            self, users: list, title: str, message: str, notification_type_name: str
    ) -> bool:
        """
        Envia notificación

        Args:
            users (list): Lista de destinatarios
            title (str): título de la notificación
            message (str): mensaje
            notification_type_name (str): tipo de notificación

        Returns:
            bool: True
        """
        try:
            notification_type = NotificationType.objects.get(
                name=notification_type_name
            )
        except NotificationType.DoesNotExist:
            return False
        final_message = self._build_message(title, message)
        typing_duration = self._calculate_typing_duration(final_message)
        for user in users:
            phone_number = self._get_user_chat_id(user)
            if phone_number:
                async_task(
                    create_whatsapp_task,
                    phone_number,
                    final_message,
                    notification_type,
                    typing_duration,
                )
        return True

    def _build_message(self, title: str, message: str) -> str:
        final_message = ""
        if title:
            final_message += f"*{title}*\n\n"
        final_message += self._clean_html_formatting(message)
        return final_message

    def _clean_html_formatting(self, message: str) -> str:
        replacements = {
            "<b>": "*",
            "</b>": "*",
            "<i>": "_",
            "</i>": "_",
            "<br>": "\n",
            "<br/>": "\n",
        }

        for html_tag, whatsapp_tag in replacements.items():
            message = message.replace(html_tag, whatsapp_tag)
        return message.strip()

    def _calculate_typing_duration(self, message: str) -> float:
        """
        Calcula duración realista de escritura
        """
        words = len(message.split())

        # Velocidad humana promedio: 40-60 palabras/minuto
        base_time = words * 1.5  # 1.5 segundos por palabra

        # Añade variabilidad
        variability = random.uniform(0.7, 1.3)
        duration = base_time * variability

        # Limita entre 2 y 15 segundos
        return max(2, min(duration, 15))

    def _get_user_chat_id(self, user):
        return getattr(user, "whatsapp_chat_id", None)

    def can_send(self, user) -> bool:
        return bool(self._get_user_chat_id(user))

    def get_channel_type(self) -> str:
        return "WHATSAPP"


class NotificationMediator:
    """
    Mediator
    """

    def __init__(self):
        self.channels = {
            "IN_APP": InAppNotificationChannel(),
            "WHATSAPP": WhatsAppNotificationChannel(),
        }

    def send_notification(
            self,
            title: str,
            message: str,
            users: list,
            notification_type_name: str,
            channels=None,
    ) -> bool:
        """
        Enviar notificaciones

        Args:
            title (str): Título de la notificación
            message (str): Mensaje
            users (list): Lista de destinatarios
            notification_type_name (str): Tipo de notificación
            channels (str, optional): Lista de canales. Defaults to None.

        Returns:
            bool: success
        """
        if channels is None:
            channels = ["IN_APP"]

        for channel_type in channels:
            if channel_type in self.channels:
                canal = self.channels[channel_type]
                canal.send(users, title, message, notification_type_name)

        return True


class NotificationService:
    """
    Servicio centralizado para enviar notificaciones
    """

    @staticmethod
    def send_notification(
            title: str,
            message: str,
            users,
            notification_type_name: str,
            channels=None,
    ) -> bool:
        """
        Método estático para crear y enviar notificaciones

        Args:
            title: Título de la notificación
            message: Mensaje de la notificación
            users: Usuario o lista de usuarios a notificar
            notification_type_name: Tipo de notificación
            channels: Canales a usar (None = solo IN_APP)

        Returns:
            bool: Resultado del envío
        """
        notification_mediator = NotificationMediator()
        return notification_mediator.send_notification(
            title=title,
            message=message,
            users=users,
            notification_type_name=notification_type_name,
            channels=channels,
        )


def get_state_handler(next_status, current_status):
    handlers = [
        NormalStateHandler(next_status),
        SpecialTransitionHandler(next_status),
        FinalStateHandler(next_status),
    ]

    for handler in handlers:
        if handler.can_transition_from(current_status):
            return handler

    raise StatusNotAllowedException()


class OrderStateHandler(ABC):
    """_summary_

    Args:
        ABC (_type_): _description_
    """

    @abstractmethod
    def can_transition_from(self, current_status):
        pass

    @abstractmethod
    def handle_transition(self, order, observations):
        pass

    def _create_tracking(self, order, next_status, observations):
        OrderTracking.objects.create(
            order_id=order.id,
            status_id=next_status.id,
            observations=(
                f"Cambio automático de estado [{next_status.name}]"
                if observations is None
                else observations
            ),
        )

    def _send_notification(self, order, next_status):
        NotificationService.send_notification(
            "Solicitud actualizada",
            f"La solicitud de compra <b>{order.id}</b> ha sido cambiada a un nuevo estado: <b>{next_status.name}</b>",
            [order.client],
            "Informativo",
            ["IN_APP", "WHATSAPP"],
        )


class NormalStateHandler(OrderStateHandler):
    """_summary_

    Args:
        OrderStateHandler (_type_): abstract base class
    """

    def __init__(self, next_status):
        self.next_status = next_status

    def _handle_on_way_status(self, order, observations: str = None):
        try:
            self._create_tracking(order, self.next_status, observations)
            self._send_notification(order, self.next_status)
            order_shipping = OrderShipping.objects.select_related("shipping_rate").get(order=order)

            if not order_shipping.shipping_rate:
                raise OrderHasNotShipingRateException()

            current_time = datetime.datetime.now()
            estimated_delivery_time = (
                order_shipping.shipping_rate.estimated_delivery_time
            )

            OrderShipping.objects.filter(id=order_shipping.id).update(
                shipped_at=current_time,
                estimated_delivery_at=current_time
                                      + datetime.timedelta(minutes=estimated_delivery_time),
            )
        except OrderShipping.DoesNotExist as exception:
            raise OrderShippingDoesNotExistException() from exception

    def _handle_delivered_status(self, order, observations: str = None):
        self._create_tracking(order, self.next_status, observations)
        self._send_notification(order, self.next_status)
        order_shipping = OrderShipping.objects.filter(order=order).first()

        if order_shipping:
            current_time = datetime.datetime.now()
            order_shipping.delivered_at = current_time
            order_shipping.save(update_fields=["delivered_at"])

        if order.pending_amount == 0:
            self.next_status = OrderStatus.objects.get(code_name="completed")
            self._handle_completed_status(order, None)

    def _handle_completed_status(self, order: Order, observations: str = None):
        if order.pending_amount != 0:
            raise PaymentNotCompletedException()

        try:
            shipping = order.shipping
        except Exception as e:
            shipping = None
        if not shipping or (shipping and shipping.delivered_at):
            self._create_tracking(
                order,
                self.next_status,
                f"Cambio automático de estado [{self.next_status.name}]",
            )
            self._send_notification(order, self.next_status)
            tasks.decrease_stock(order)

    def can_transition_from(self, current_status):
        return abs(self.next_status.order - current_status.order) == 1

    def handle_transition(self, order, observations):
        special_handlers = {
            "on_way": self._handle_on_way_status,
            "delivered": self._handle_delivered_status,
            "completed": self._handle_completed_status,
        }

        if self.next_status.code_name not in special_handlers:
            self._create_tracking(order, self.next_status, observations)
            self._send_notification(order, self.next_status)

        handler = special_handlers.get(self.next_status.code_name)
        if handler:
            handler(order, observations)
        sync_order_with_odoo_task(order)


class SpecialTransitionHandler(OrderStateHandler):
    """Class to handler special transition

    Args:
        OrderStateHandler (_type_): abstract base class
    """

    def __init__(self, next_status):
        self.next_status = next_status

    def can_transition_from(self, current_status):
        cs = current_status.code_name
        ns = self.next_status.code_name

        return any([
            (cs == 'pick_up' and ns == 'delivered')
        ])

    def handle_transition(self, order, observations):
        self._create_tracking(order, self.next_status, observations)
        self._send_notification(order, self.next_status)

        sync_order_with_odoo_task(order)


class FinalStateHandler(NormalStateHandler):
    """_summary_

    Args:
        OrderStateHandler (_type_): abstract base class
    """

    def __init__(self, next_status):
        self.next_status = next_status

    def can_transition_from(self, current_status):
        return self.next_status.final_status

    def _handle_cancelled_or_returned_status(self, order, observations: str = None):
        self._create_tracking(order, self.next_status, observations)
        self._send_notification(order, self.next_status)

        order_products = OrderProducts.objects.select_related("product").filter(order_id=order.id)
        products_to_update = []

        for op in order_products:
            product = op.product
            product.quantity += op.quantity

            if product.quantity > 0:
                product.active = True

            products_to_update.append(product)

        if products_to_update:
            Product.objects.bulk_update(products_to_update, ["quantity", "active"])

        tasks.increase_stock(order)
        tasks.refund_order(order)
        NotificationService.send_notification(
            "Solicitud reembolsada",
            f"La solicitud de compra {order.id} ha sido reembolsada y cancelada.",
            [order.client],
            "Informativo",
            ["IN_APP", "WHATSAPP"],
        )

    def handle_transition(self, order, observations):
        if self.next_status.code_name in ["cancelled", "returned"]:
            self._handle_cancelled_or_returned_status(order, observations)
        elif self.next_status.code_name == "completed":
            self._handle_completed_status(order)

        sync_order_with_odoo_task(order)
