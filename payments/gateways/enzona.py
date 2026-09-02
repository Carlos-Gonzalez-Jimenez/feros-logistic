import time
from typing import Optional

import requests

from core.exceptions import ConfigurationDoesNotExistException
from core.models import Config


class EnzonaPaymentGateway:
    _instance = None
    _token: Optional[str] = None
    _token_expiration: Optional[float] = None

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self._initialize_config()

    @classmethod
    def get_instance(cls) -> "EnzonaPaymentGateway":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _initialize_config(self) -> None:
        try:
            config = Config.objects.get()
            self._consumer_key = config.enzona_consumer_key
            self._consumer_secret = config.enzona_consumer_secret
            self._api_url = config.enzona_api_url.rstrip("/")
            self._initialized = True
        except Config.DoesNotExist as exc:
            raise ConfigurationDoesNotExistException() from exc

    def __is_valid_token(self):
        return self._token is not None and self._token_expiration is not None and time.time() < self._token_expiration

    def get_token(self, force_refresh: bool = False) -> str:
        if not force_refresh and self.__is_valid_token():
            return self._token

        data = {"grant_type": "client_credentials", "scope": "enzona_business_payment"}
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        try:
            response = requests.post(f"{self._api_url}/token", data=data, headers=headers, timeout=10,
                                     auth=(self._consumer_key, self._consumer_secret), verify=False)
            response.raise_for_status()

            json_response = response.json()
            self._token = json_response["access_token"]

            if "expires_in" in json_response:
                import time
                self._token_expiration = time.time() + json_response["expires_in"]
            return self._token

        except requests.exceptions.ConnectionError as error:
            raise ConnectionError(f"Network Error: {error}") from error
        except requests.exceptions.Timeout as error:
            raise requests.Timeout(f"Network Connection Timeout: {error}") from error
        except requests.exceptions.HTTPError as error:
            if response.status_code >= 500:
                raise ConnectionError(f"Server Error: {response.status_code}") from error
            else:
                raise ValueError(f"API Error {response.status_code}: {response.text}") from error

    def get_headers(self):
        return {"Authorization": f"Bearer {self.get_token()}", 'accept': 'application/json',
                'Content-Type': 'application/json'}

    def create_payment(self, payload):
        """
          {'transaction_uuid': '5afb04f7d09f4cc89a9179fe4f691dfa', 'currency': 'CUP',
         'created_at': '2025-10-25T18:54:56.000-04:00', 'updated_at': '2025-10-25T18:54:56.000-04:00',
         'status_code': 1113, 'status_denom': 'Pendiente', 'description': 'Pago del pedido 18',
         'invoice_number': '1212', 'merchant_op_id': 'qwertyuioplo', 'terminal_id': '12121',
         'amount': {'total': '29678.00',
                    'details': {'shipping': '7678.00', 'tax': '0.00', 'discount': '0.00', 'tip': '0.00'}}, 'items': [
            {'description': 'Pago del producto MASCARILLA DETOX', 'quantity': '1', 'price': '22000.00', 'tax': '0.00',
             'name': 'MASCARILLA DETOX'}], 'links': [{'rel': 'confirm', 'method': 'REDIRECT',
                                                      'href': 'https://www.enzona.net/checkout/01c047899e11c04ec7bfaf569f05d7e493/login'},
                                                     {'rel': 'complete', 'method': 'POST',
                                                      'href': 'https://api.enzona.net/payment/v1.0.0/payments/5afb04f7d09f4cc89a9179fe4f691dfa/complete'},
                                                     {'rel': 'cancel', 'method': 'POST',
                                                      'href': 'https://api.enzona.net/payment/v1.0.0/payments/5afb04f7d09f4cc89a9179fe4f691dfa/cancel'},
                                                     {'rel': 'refund', 'method': 'POST',
                                                      'href': 'https://api.enzona.net/payment/v1.0.0/payments/5afb04f7d09f4cc89a9179fe4f691dfa/refund'},
                                                     {'rel': 'self', 'method': 'GET',
                                                      'href': 'https://api.enzona.net/payment/v1.0.0/payments/5afb04f7d09f4cc89a9179fe4f691dfa'}],
         'commission': '', 'transaction_signature': ''}
        """

        headers = self.get_headers()
        return requests.post(f"{self._api_url}/payment/v1.0.0/payments", json=payload, headers=headers, timeout=10,
                             verify=False)

    def cancel_payment(self, payment_uuid: str):
        headers = self.get_headers()
        return requests.post(f"{self._api_url}/payment/v1.0.0/payments/{payment_uuid}/cancel", headers=headers,
                             timeout=10, verify=False)

    def complete_payment(self, payment_uuid: str):
        headers = self.get_headers()
        return requests.post(f"{self._api_url}/payment/v1.0.0/payments/{payment_uuid}/complete", headers=headers,
                             timeout=10, verify=False)
