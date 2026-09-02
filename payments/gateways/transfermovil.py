import hashlib
import base64

import requests
from dateutil.utils import today

from core.exceptions import ConfigurationDoesNotExistException
from core.models import Config


class TransfermovilPaymentGateway:
    _instance = None

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self._initialize_config()

    @classmethod
    def get_instance(cls) -> "TransfermovilPaymentGateway":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _initialize_config(self) -> None:
        try:
            config = Config.objects.first()
            self._username = config.transfermovil_username
            self._source = config.transfermovil_source
            self._seed = config.transfermovil_seed
            self._api_url = config.transfermovil_api_url
            self._initialized = True
        except Config.DoesNotExist as exc:
            raise ConfigurationDoesNotExistException() from exc

    def get_token(self) -> str:
        __today = today()
        token = f"{self._username}{__today.day}{__today.month}{__today.year}{self._seed}{self._source}"
        token_512 = hashlib.sha512(token.encode()).digest()
        return base64.b64encode(token_512).decode()

    def get_headers(self):
        return {
            "username": self._username,
            "source": self._source,
            "password": self.get_token(),
        }

    def create_payment(self, payload):
        headers = self.get_headers()
        return requests.post(f"{self._api_url}/RestExternalPayment.svc/payOrder", json=payload, headers=headers,
                             verify=False)

    def get_payment_status(self, external_payment_id):
        headers = self.get_headers()
        return requests.get(
            f"{self._api_url}/RestExternalPayment.svc/getStatusOrder/{external_payment_id}/{self._source}",
            headers=headers, verify=False)
