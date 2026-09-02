import requests
from django.template import Template, Context
from django_q.tasks import async_task

from core.models import Currency, Order


class OdooAPIServices:
    _initialized = None
    _token = None
    _api_url = None

    def __init__(self, api_url, token):
        self._api_url = api_url
        self._token = token
        self._headers = {"X-API-KEY": self._token}

    @classmethod
    def initialize(cls):
        return cls.dev_initialize()
        # if not cls._initialized:
        #     config = Config.objects.get()
        #     cls._initialized = OdooAPIServices(config.odoo_url, config.odoo_token)
        # return cls._initialized

    @classmethod
    def dev_initialize(cls):
        if not cls._initialized:
            # cls._initialized = OdooAPIServices(
            #     "https://osmel810807f-odooferoz.odoo.com/api/v1",
            #     "XfmV9SbZsm5pKaE9mgagJQjpQThnqaA9TxJpAQb9")

            cls._initialized = OdooAPIServices(
                "https://osmel810807f-odooferoz-test-34211428.dev.odoo.com/api/v1",
                "c7n4Pv1tgDSvC7zXkLmFfewZR6JbLEUlW41prlNH")
        return cls._initialized

    def products(self, limit=20, offset=0):
        response = requests.get(self._api_url + '/products', headers=self._headers,
                                data={'limit': limit, 'offset': offset})
        response.raise_for_status()
        return response.json()

    def all_products(self):
        limit, offset = 100, 0
        products = []
        response = self.products(limit, offset)['data']['products']
        while len(response) > 0:
            products.extend(response)
            offset += limit
            response = self.products(limit, offset)['data']['products']
        return products

    def product_by_id(self, id: int):
        response = requests.get(self._api_url + f'/products/{id}', headers=self._headers)
        response.raise_for_status()
        return response.json()

    def categories(self):
        response = requests.get(self._api_url + f'/categories', headers=self._headers)
        response.raise_for_status()
        return response.json()

    def currencies(self):
        response = requests.get(self._api_url + f'/currencies', headers=self._headers)
        response.raise_for_status()
        return response.json()

    def customers(self, page=1, limit=50):
        response = requests.get(self._api_url + '/customers', headers=self._headers,
                                data={"page": page, "limit": limit})
        response.raise_for_status()
        return response.json()

    def customer_by_id(self, id: int):
        response = requests.get(self._api_url + f'/customers/{id}', headers=self._headers)
        response.raise_for_status()
        return response.json()

    def warehouses(self):
        response = requests.get(self._api_url + '/warehouses', headers=self._headers)
        response.raise_for_status()
        return response.json()

    def warehouse_by_id(self, id: int):
        response = requests.get(self._api_url + f'/warehouses/{id}', headers=self._headers)
        response.raise_for_status()
        return response.json()

    def sales(self, state, offset=0, limit=50):
        response = requests.get(
            self._api_url + f'/sales', headers=self._headers, data={
                "state": state, "offset": offset, "limit": limit
            })
        response.raise_for_status()
        return response.json()

    def sale_by_id(self, id):
        response = requests.get(self._api_url + f'/sales/{id}', headers=self._headers)
        response.raise_for_status()
        return response.json()

    def update_sale(self, id: int, data: dict):
        response = requests.patch(self._api_url + f'/sales/{id}', headers=self._headers, json=data)
        response.raise_for_status()
        return response.json()

    def create_sale(self, sale: dict):
        response = requests.post(self._api_url + f'/sales/create', headers=self._headers, json=sale)
        response.raise_for_status()
        return response.json()


def sync_inventory():
    currencies = {currency.initials: currency for currency in Currency.objects.all()}

    data = []
    products = OdooAPIServices.initialize().all_products()
    for product in products:
        update_fields = dict()

        for price_list in product.get('prices'):
            if price_list['pricelist_id'] == 1:  # Lista de precios por defecto.
                price = price_list['price']
                if price > 0:
                    update_fields.update(price=price)
                break

        for warehouse in product.get('stock_by_warehouse'):
            if warehouse['warehouse_id'] == 16:  # Ventas mayoristas (EN PUERTO).
                update_fields.update(quantity=warehouse['qty_available'])
                price = warehouse['precio_usd']
                if price is not None and price > 0:
                    update_fields.update(price=warehouse['precio_usd'])
                break

        data.append(dict(name=product['name'], category=product['category']))
        # Product.objects.update_or_create(
    #     defaults=update_fields,
    #     create_defaults={
    #         'name': product['name'], 'odoo_product_id': product['id'], 'active': False,
    #         'currency': currencies[product['currency']], **update_fields
    #     },
    #     odoo_product_id=product['id']
    # )
    return data


def sync_new_sale(order: Order):
    order.refresh_from_db()
    order_products = order.order_products.all()
    customer = order.client
    fee = customer.fee
    payment = order.payment.first()
    delivery = order.shipping

    percentual_fee = order.percentual_fee * 100

    observations = Template("""
        Pedido recibido automaticamente desde el "Sistema de Reserva en Línea"
            
        Cliente: {{customer.get_full_name}}
        Método de pago: {{payment.payment_method}}
        Moneda: {{payment.currency}}
        Monto a pagar: {{payment.amount}} {{payment.currency}}
        Tarifa aplicada: {{fee|default_if_none:'Sin tarifa aplicada'}}
        {% if fee %}
        - Monto porcentual: {{percentual_fee}}%
        - Monto fijo: {{order.fixed_fee}}
        {% endif %}
        
        {% if delivery %}
        SERVICIO DE MENSAJERIA
        Tipo de entrega: {{delivery.shipping_rate.shipping_method}}
        Precio de mensajería: {{delivery.shipping_price}} {{payment.currency}}
        Dirección de entrega: {{delivery.delivery_address}}
        {% else %}
        RECOGIDA EN ALMACÉN
        {% endif %}
    """).render(Context(dict(
        customer=customer, payment=payment, delivery=delivery, order=order, fee=fee,
        percentual_fee=percentual_fee)
    ))

    odoo_sale = {
        # "partner_name": "string",
        # "partner_email": "user@example.com",
        # "partner_phone": "string",
        "buyer_name": customer.first_name,
        "buyer_lastname": customer.last_name,
        "buyer_phone": customer.phone_number,
        "buyer_id_number": customer.dni,
        "client_order_ref": order.pk,
        "pickup_date": order.expiration_date,
        "warehouse_id": 16,  # Ventas mayoristas (EN PUERTO)
        "pricelist_id": 1,  # Venta en USD
        "order_lines": [
            {
                'product_id': order_product.product.odoo_product_id,
                'price': order_product.price,  # ODOO DEBE AGREGAR ESTE CAMPO
                'quantity': order_product.quantity,
            } for order_product in order_products
        ],
        "observations": observations,
        "total_amount": order.total_amount,  # VALORES OPCIONALES POR AHORA
        "total_discount": order.total_discount,  # VALORES OPCIONALES POR AHORA
        "shipping_amount": delivery.shipping_price  # VALORES OPCIONALES POR AHORA
    }

    response = OdooAPIServices.initialize().create_sale(odoo_sale)
    order.odoo_order_id = response['data']['order_id']
    order.save()


def update_sale(order: Order):
    order.refresh_from_db()
    current_status = order.current_status.status

    OdooAPIServices.initialize().update_sale(order.odoo_order_id, {
        "state": current_status.code_name,
        "pickup_date": order.expiration_date,
        # AGREGAR MAS CAMPOS PRÓXIMAMENTE.
    })


def sync_order_with_odoo_task(order: Order):
    group = 'sync_order_with_odoo'
    if order.odoo_order_id is None:
        async_task(sync_new_sale, order, group=group, task_name=f'create_order_{order.pk}')
    else:
        async_task(update_sale, order, group=group, task_name=f'update_order_{order.pk}')
