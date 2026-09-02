import datetime
import hashlib
from typing import Optional, Any

from data_fetcher.global_request_context import get_request
from django.core.cache import cache
from fpdf import FPDF

from core import models, serializers
from core.models import Order, Currency
from delivery.models import OrderShipping
from logistic_backend.settings import APPLICATION_DATA_PATH
from payments.models import Payment, TransactionLog, Wallet, WalletOperationalLog


class NomenclatorCacheManager:
    """Manager centralizado para cache de nomencladores"""

    # Tiempo de expiración por defecto (1 hora)
    DEFAULT_TIMEOUT = 3600

    @staticmethod
    def get_cache_key(
            model_name: str, action: str, user=None, pk: Optional[int] = None, **kwargs
    ) -> str:
        """
        Genera clave de cache CONSISTENTE con versión
        """
        user_type = "staff" if user and user.is_staff else "user"
        key_parts = [model_name.lower(), user_type, action]

        if pk:
            key_parts.append(str(pk))

        # Incluir parámetros de paginación y búsqueda para list
        if action == "list":
            page = kwargs.get("page")
            page_size = kwargs.get("page_size")
            search = kwargs.get("search", "")

            if page:
                key_parts.append(f"page_{page}")
            if page_size:
                key_parts.append(f"size_{page_size}")
            if search:
                search_normalized = search.strip().lower()
                search_hash = hashlib.md5(search_normalized.encode()).hexdigest()[:8]
                key_parts.append(f"search_{search_hash}")

        version_key = f"{model_name.lower()}_cache_version"
        current_version = cache.get(version_key, 0)
        key_parts.append(f"v{current_version}")

        return "_".join(key_parts)

    @staticmethod
    def invalidate_model_cache(model_name: str) -> None:
        """
        Invalida cache usando solo sistema de versionado
        Método SIMPLE y EFICIENTE para producción
        """
        model_name_lower = model_name.lower()
        version_key = f"{model_name_lower}_cache_version"

        current_version = cache.get(version_key, 0)
        # Incrementar versión - esto invalida automáticamente todas las claves antiguas
        cache.set(version_key, current_version + 1, timeout=None)

    @staticmethod
    def get_cached_data(
            model_name: str, action: str, user=None, pk: Optional[int] = None, **kwargs
    ) -> Any:
        """
        Obtiene datos del cache
        """
        cache_key = NomenclatorCacheManager.get_cache_key(
            model_name, action, user, pk, **kwargs
        )
        return cache.get(cache_key)

    @staticmethod
    def set_cached_data(
            data: Any,
            model_name: str,
            action: str,
            user=None,
            pk: Optional[int] = None,
            timeout: Optional[int] = None,
            **kwargs,
    ) -> str:
        """
        Guarda datos en cache
        """
        cache_key = NomenclatorCacheManager.get_cache_key(
            model_name, action, user, pk, **kwargs
        )

        if timeout is None:
            timeout = NomenclatorCacheManager.DEFAULT_TIMEOUT

        cache.set(cache_key, data, timeout)
        return cache_key


class OrderInvoice(FPDF):
    def __init__(self, order):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.order = order
        self.config = models.Config.objects.first()
        self.config_data = serializers.ConfigSerializer(self.config).data
        self.add_font(
            "Roboto", "", APPLICATION_DATA_PATH + "/fonts/Roboto-Medium.ttf", uni=True
        )
        self.add_font(
            "Roboto", "B", APPLICATION_DATA_PATH + "/fonts/Roboto-Bold.ttf", uni=True
        )
        self.add_page()
        self.set_auto_page_break(auto=True, margin=25)
        self.generate_invoice()

    def header(self):
        logo = self.config.logo_light
        logo_path = logo.path
        logo_w = 20
        logo_h = 20
        logo_x = self.w - self.r_margin - logo_w
        logo_y = self.t_margin
        self.image(logo_path, x=logo_x, y=logo_y, w=logo_w, h=logo_h)
        self.ln(logo_y + logo_h - self.get_y() + 2)

    def footer(self):
        pass

    def generate_invoice(self):
        self.seller_info()
        self.buyer_info()
        self.products_table()
        self.signatures()

    def seller_info(self):
        self.set_font("Roboto", "B", 16)
        self.cell(0, 10, "M-3 MODELO DE FACTURA", 0, 1, "C")
        self.ln(5)

        self.set_font("Roboto", "", 11)
        self.cell(35, 8, f"No. Factura: {str(self.order.id)}", 0, 0, "L")
        self.cell(100, 8, f"No. Contrato: {self.get_contract_number()}", 0, 0, "R")
        self.ln(5)

        self.cell(35, 8, f"Vendedor: {self.get_seller_name()}", 0, 0, "L")
        self.ln(5)
        self.cell(35, 8, f"Dirección: {self.get_business_address()}", 0, 0, "L")
        self.ln(5)
        self.cell(
            45,
            8,
            "Actividad autorizada: Comercialización de alimentos.",
            0,
            0,
            "L",
        )
        self.ln(5)
        # self.cell(35, 8, f"No. licencia TCP: {self.get_business_licence()}", 0, 0, "L")
        self.cell(35, 8, f"NIT: {self.get_business_nit()}", 0, 0, "L")
        self.ln(5)
        self.cell(40, 8, f"Cuenta bancaria: {self.get_business_account()}", 0, 0, "L")
        self.ln(8)
        self.set_draw_color(0, 0, 0)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def get_seller_name(self):
        return "MIPYME FEROS GRUPO S.U.R.L."

    def get_contract_number(self):
        return "----------"

    def get_business_licence(self):
        return self.config.business_licence

    def get_business_nit(self):
        return self.config.business_nit

    def get_business_account(self):
        return self.config.business_account

    def get_business_address(self):
        return self.config.business_address

    def buyer_info(self):
        client = self.order.client
        self.cell(0, 8, f"Comprador: {self.get_client_name(client)}", 0, 0, "L")
        self.ln(5)

        self.cell(30, 7, f"Dirección: {self.get_client_address(client)}", 0, 0, "L")
        self.ln(5)

        self.cell(35, 7, f"Código REEUP: {self.get_reeup_code(client)}", 0, 0, "L")
        self.ln(5)

        self.cell(40, 7, f"Cuenta bancaria: {self.get_bank_account(client)}", 0, 0, "L")
        self.ln(8)

    def get_client_name(self, client):
        return (
            f"{client.first_name} {client.last_name}"
            if hasattr(client, "first_name") and hasattr(client, "last_name")
            else "----------"
        )

    def get_client_address(self, client):
        if hasattr(client, "address") and client.address:
            return client.address
        return "----------"

    def get_reeup_code(self, client):
        return "----------"

    def get_bank_account(self, client):
        return "----------"

    def table_header(self):
        self.set_font("Roboto", "B", 10)
        self.set_fill_color(240, 240, 240)
        self.cell(10, 8, "No", 1, 0, "C", 1)
        self.cell(25, 8, "Código de pieza", 1, 0, "C", 1)
        self.cell(70, 8, "Descripción", 1, 0, "C", 1)
        self.cell(15, 8, "U/M", 1, 0, "C", 1)
        self.cell(20, 8, "Cantidad", 1, 0, "C", 1)
        self.cell(25, 8, "Precio", 1, 0, "C", 1)
        self.cell(25, 8, "importe", 1, 1, "C", 1)
        self.set_font("Roboto", "", 9)

    def products_table(self):
        self.ln(5)
        self.table_header()
        counter = 1
        for item in self.order.order_products.all():
            if self.get_y() > 250:
                self.add_page()
                self.table_header()
            self.cell(10, 6, str(counter), 1, 0, "C")
            self.cell(25, 6, self.get_code_sku(item.product), 1, 0, "L")
            self.cell(70, 6, item.product.name[:30], 1, 0, "L")
            self.cell(15, 6, self.get_unit_measure(item.product), 1, 0, "C")
            self.cell(20, 6, f"{item.quantity:.2f}", 1, 0, "R")
            self.cell(25, 6, self.format_currency(item.price), 1, 0, "R")
            self.cell(25, 6, self.format_currency(item.amount), 1, 1, "R")
            counter += 1

        self.ln(10)

        self.set_font("Roboto", "B", 11)
        self.cell(140, 8, "SUBTOTAL:", 0, 0, "R")
        self.set_font("Roboto", "", 11)
        self.cell(40, 8, self.format_currency(self.order.amount), 0, 1, "R")

        if self.order.total_discount > 0:
            self.set_font("Roboto", "B", 11)
            self.cell(140, 8, "DESCUENTO:", 0, 0, "R")
            self.set_font("Roboto", "", 11)
            self.cell(
                40, 8, f"-{self.format_currency(self.order.total_discount)}", 0, 1, "R"
            )

        self.line(140, self.get_y(), 190, self.get_y())
        self.ln(2)

        self.set_font("Roboto", "B", 12)
        self.cell(140, 8, "TOTAL:", 0, 0, "R")
        self.cell(40, 8, self.format_currency(self.order.total_amount), 0, 1, "R")

        if self.order.pending_amount > 0:
            self.ln(5)
            self.set_font("Roboto", "B", 11)
            self.set_text_color(200, 0, 0)
            self.cell(140, 7, "PENDIENTE:", 0, 0, "R")
            self.cell(40, 7, self.format_currency(self.order.pending_amount), 0, 1, "R")
            self.set_text_color(0, 0, 0)

        self.ln(10)

    def get_code_sku(self, product):
        if hasattr(product, "code_sku") and product.code_sku:
            return product.code_sku
        return "----------"

    def get_unit_measure(self, product):
        if hasattr(product, "measurement_unit") and product.measurement_unit:
            return product.measurement_unit.abbreviation
        return "UND"

    def signatures(self):
        self.set_font("Roboto", "", 10)
        self.ln(10)
        self.cell(
            45,
            8,
            f"Entregado por: {self.get_seller_name().replace('TCP ', '')}",
            0,
            0,
            "L",
        )
        self.cell(
            140, 8, "Recibido por: _____________________________________", 0, 0, "R"
        )
        self.ln(6)
        self.cell(45, 8, "C.Identidad: ________________", 0, 0, "L")
        self.cell(110, 8, "C.Identidad: ____________________", 0, 0, "R")
        self.ln(6)
        self.cell(
            45, 8, f"Fecha: {self.order.creation_date.strftime('%d/%m/%Y')}", 0, 0, "L"
        )
        self.cell(102, 8, "Fecha: _______________", 0, 0, "R")
        self.ln(6)
        self.cell(45, 8, "Firma: _________________________", 0, 0, "L")
        self.cell(119, 8, "Firma: _________________________", 0, 0, "R")

    def format_currency(self, value):
        try:
            return f"${float(value):,.2f}".replace(",", " ")
        except:
            return f"${float(value):.2f}"


class DeliveryDrive(FPDF):
    def __init__(self, order):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.order = order
        self.config = models.Config.objects.first()
        self.config_data = serializers.ConfigSerializer(self.config).data
        self.add_font(
            "Roboto", "", APPLICATION_DATA_PATH + "/fonts/Roboto-Medium.ttf", uni=True
        )
        self.add_font(
            "Roboto", "B", APPLICATION_DATA_PATH + "/fonts/Roboto-Bold.ttf", uni=True
        )
        self.add_page()
        self.set_auto_page_break(auto=True, margin=20)
        self.generate_conduce()

    def header(self):
        logo = self.config.logo_light
        logo_path = logo.path
        logo_w = 20
        logo_h = 20
        logo_x = self.w - self.r_margin - logo_w
        logo_y = self.t_margin
        self.image(logo_path, x=logo_x, y=logo_y, w=logo_w, h=logo_h)
        self.ln(logo_y + logo_h - self.get_y() + 2)

        self.set_font("Roboto", "B", 20)
        self.cell(0, 15, "M-1 MODELO DE CONDUCE", 0, 1, "C")
        self.ln(5)

        self.set_draw_color(0, 0, 0)
        self.line(10, self.get_y(), 200, self.get_y())

    def footer(self):
        self.set_y(-20)
        self.set_font("Roboto", "B", 8)
        self.set_text_color(100, 100, 100)
        self.multi_cell(
            0,
            5,
            "Nota: Este conduce tiene valor solo para la transportación de la mercancía desde el origen hasta el destino.",
            0,
            "L",
        )

    def generate_conduce(self):
        self.origin_info()
        self.destination_info()
        self.products_table()
        self.signatures()

    def origin_info(self):
        self.set_font("Roboto", "", 12)
        self.cell(30, 8, f"Origen: {self.get_origin()}", 0, 0, "L")
        self.ln(10)

    def get_origin(self):
        return self.config.business_address

    def destination_info(self):
        self.cell(30, 8, f"Destino: {self.get_destination()}", 0, 0, "L")
        self.ln(8)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def get_destination(self):
        try:
            shipping = OrderShipping.objects.get(order=self.order)
        except OrderShipping.DoesNotExist:
            shipping = None
        if shipping:
            return shipping.delivery_address
        elif hasattr(self.order.client, "address") and self.order.client.address:
            return self.order.client.address
        else:
            return "-------------"

    def table_header(self):
        self.set_font("Roboto", "B", 10)
        self.set_fill_color(240, 240, 240)
        self.cell(10, 8, "No.", 1, 0, "C", 1)
        self.cell(25, 8, "Código", 1, 0, "C", 1)
        self.cell(110, 8, "Descripción del Producto", 1, 0, "C", 1)
        self.cell(15, 8, "U/M", 1, 0, "C", 1)
        self.cell(20, 8, "Cantidad", 1, 0, "C", 1)
        self.set_font("Roboto", "", 9)

    def products_table(self):
        self.table_header()
        self.ln(8)
        counter = 1
        for item in self.order.order_products.all():
            if self.get_y() > 250:
                self.add_page()
                self.table_header()
            self.cell(10, 6, str(counter), 1, 0, "C")
            self.cell(25, 6, self.get_product_code(item.product), 1, 0, "L")
            self.cell(110, 6, item.product.name[:70], 1, 0, "L")
            self.cell(15, 6, self.get_unit_measure(item.product), 1, 0, "C")
            self.cell(20, 6, f"{item.quantity:.2f}", 1, 0, "R")
            self.ln(6)
            counter += 1

        self.ln(10)

    def get_product_code(self, product):
        if hasattr(product, "code_sku") and product.code_sku:
            return product.code_sku
        return "----------"

    def get_unit_measure(self, product):
        if hasattr(product, "measurement_unit") and product.measurement_unit:
            return product.measurement_unit.abbreviation
        return "UND"

    def signatures(self):
        self.ln(5)
        self.cell(35, 8, f"Vendedor: {self.get_seller_name()}", 0, 0, "L")
        self.cell(140, 8, f"Comprador: {self.get_buyer_name()}", 0, 0, "R")
        self.ln(5)
        self.cell(35, 8, f"C.Identidad: {self.get_seller_id()}", 0, 0, "L")
        self.cell(121, 8, f"C.Identidad: {self.get_buyer_id()}", 0, 0, "R")
        self.ln(5)
        self.cell(156, 8, f"Chapa: {self.get_license_plate()}", 0, 0, "R")
        self.ln(5)

        self.ln(10)
        self.set_font("Roboto", "B", 10)
        self.cell(95, 8, "_________________________", 0, 0, "C")
        self.cell(95, 8, "_________________________", 0, 1, "C")

        self.set_font("Roboto", "", 9)
        self.cell(95, 5, "Firma del Vendedor", 0, 0, "C")
        self.cell(95, 5, "Firma del Comprador", 0, 1, "C")

        self.ln(2)
        self.set_font("Roboto", "", 8)
        self.cell(95, 4, self.order.creation_date.strftime("%d/%m/%Y"), 0, 0, "C")
        self.cell(95, 4, "____________", 0, 1, "C")

    def get_seller_name(self):
        return "MIPYME FEROS GRUPO S.U.R.L."

    def get_buyer_name(self):
        client = self.order.client
        if hasattr(client, "first_name") and hasattr(client, "last_name"):
            return f"{client.first_name} {client.last_name}"
        return "------------"

    def get_seller_id(self):
        return "______________"

    def get_buyer_id(self):
        client = self.order.client
        if hasattr(client, "dni"):
            return f"{client.dni}"
        return "------------"

    def get_license_plate(self):
        return "_______________"


class ProductReport(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.config = models.Config.objects.first()
        self.add_font(
            "Roboto", "", APPLICATION_DATA_PATH + "/fonts/Roboto-Medium.ttf", uni=True
        )
        self.add_font(
            "Roboto", "B", APPLICATION_DATA_PATH + "/fonts/Roboto-Bold.ttf", uni=True
        )
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        logo = self.config.logo_light
        logo_path = logo.path
        logo_w = 20
        logo_h = 20
        logo_x = self.w - self.r_margin - logo_w
        logo_y = self.t_margin
        self.image(logo_path, x=logo_x, y=logo_y, w=logo_w, h=logo_h)
        self.ln(logo_y + logo_h - self.get_y() + 2)

        self.set_font("Roboto", "B", 12)
        self.cell(0, 10, "Productos por categorías", 0, 1, "C")
        self.set_font("Roboto", "", 8)
        self.cell(
            0,
            8,
            f'Fecha: {datetime.datetime.now().strftime("%d/%m/%Y %H:%M")}',
            0,
            1,
            "R",
        )
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(2)

    def footer(self):
        self.set_y(-15)
        self.set_font("Roboto", "B", 8)
        self.cell(0, 10, f"Pág. {self.page_no()}", 0, 0, "R")

    def category_header(self, category_name, level=0):
        self.set_font("Roboto", "B", 9)
        indent = 10 + level * 5
        self.set_x(indent)
        self.set_fill_color(240, 240, 240)
        self.cell(0, 8, f"{category_name}", 0, 1, "L", 1)
        if level == 0:
            self.ln(1)

    def product_row(self, product, level=0):
        indent = 10 + level * 5
        self.ln(5)
        self.set_font("Roboto", "", 9)
        start_x = indent
        self.set_x(start_x)

        col_code = 20
        col_name = 70
        col_price = 25
        col_minimum = 25
        col_stock = 25

        self.cell(
            col_code,
            8,
            (
                product.code_sku[:15] + "..."
                if len(product.code_sku) > 15
                else product.code_sku
            ),
        )
        self.cell(
            col_name,
            8,
            product.name[:40] + "..." if len(product.name) > 40 else product.name,
        )
        self.cell(col_price, 8, f"${product.unit_price}", 0, 0, "R")
        self.cell(col_price, 8, f"${product.wholesale_price}", 0, 0, "R")
        self.cell(col_minimum, 8, str(product.wholesale_minimum), 0, 0, "R")
        stock_color = (
            (255, 0, 0) if product.quantity < product.minimal_stock else (0, 0, 0)
        )
        self.set_text_color(*stock_color)
        self.cell(col_stock, 8, str(product.quantity), 0, 0, "R")
        self.set_text_color(0, 0, 0)

    def summary_section(
            self, total_products, total_categories, total_value, total_wholesale
    ):
        self.ln(10)
        self.set_font("Roboto", "B", 12)
        self.cell(0, 10, "Resumen:", 0, 1, "L")

        self.set_font("Roboto", "", 10)
        self.cell(0, 8, f"Total Productos: {total_products}", 0, 1)
        self.cell(0, 8, f"Total Categorías: {total_categories}", 0, 1)
        self.cell(0, 8, f"Valor Total Precio Unitario: ${total_value:,.2f}", 0, 1)
        self.cell(0, 8, f"Valor Total Precio Mayorista: ${total_wholesale:,.2f}", 0, 1)


def increase_stock(order: Order):
    product_batchs = models.ProductBatch.objects.select_related('batch_item', 'order_product') \
        .filter(order_product__order=order, reserved=False).all()
    for product_batch in product_batchs:
        batch_item = product_batch.batch_item
        batch_item.quantity_sold -= product_batch.quantity
        batch_item.amount_sold -= product_batch.quantity * product_batch.order_product.price
        batch_item.save()


def decrease_stock(order: Order):
    product_batchs = models.ProductBatch.objects.select_related('batch_item', 'order_product') \
        .filter(order_product__order=order, reserved=True).all()
    for product_batch in product_batchs:
        batch_item = product_batch.batch_item
        batch_item.quantity_sold += product_batch.quantity
        batch_item.amount_sold += product_batch.quantity * product_batch.order_product.price
        batch_item.save()
    models.ProductBatch.objects.filter(order_product__order=order).update(reserved=False)


def refund_order(order):
    wallet, _ = Wallet.objects.select_for_update().get_or_create(user_id=order.client_id, defaults={"amount": 0})
    user = get_request().user
    _payments = Payment.objects.select_related('currency', 'order__client') \
        .filter(order=order, status=Payment.PaymentStatus.Completed).all()

    for payment in _payments:
        payment.status = Payment.PaymentStatus.Refunded
        TransactionLog.objects.create(
            transaction_id=payment.transaction_id,
            payment_status=payment.status,
            charge_for=user,
            description=f"Pago reembolsado del pedido {order.id} por {payment.amount}. Reembolso realizado por {user.first_name} {user.last_name}",
        )
        WalletOperationalLog.objects.create(
            transaction_id=f"REEMBOLSO_{payment.currency.initials}_{round(payment.amount * payment.exchange_rate, 2)}",
            description=f"Reembolso del pedido {order.id}. Realizado por {user.first_name} {user.last_name}",
            amount=payment.amount,
            previous_amount=wallet.amount,
            exchange_rate=payment.exchange_rate,
            exchange_rate_date=payment.exchange_rate_date,
            wallet=wallet,
            currency=payment.currency,
            charge_for=user,
        )
        wallet.amount += payment.amount
    Payment.objects.bulk_update(_payments, ['status'])

    shipping = OrderShipping.objects.filter(order=order).first()
    if shipping:
        currency = Currency.objects.get(default=True)
        WalletOperationalLog.objects.create(
            transaction_id=f"DESCUENTO_ENTREGA",
            description=f"Descuento de entrega del pedido {order.id}. Realizado por {user.first_name} {user.last_name}",
            amount=shipping.shipping_price * -1,
            previous_amount=wallet.amount,
            exchange_rate=1,
            exchange_rate_date=shipping.created_at,
            wallet=wallet,
            currency=currency,
            charge_for=user,
        )
        wallet.amount -= shipping.shipping_price

    wallet.save(update_fields=['amount'])
