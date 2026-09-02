import hashlib
from datetime import datetime, timedelta

import requests

from core.exceptions import ConfigurationDoesNotExistException
from core.models import Config


class TropipayPaymentGateway:
    _instance = None

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self._initialize_config()

    @classmethod
    def get_instance(cls) -> "TropipayPaymentGateway":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _initialize_config(self) -> None:
        try:
            config = Config.objects.first()
            self._api_url = config.tropipay_api_url
            self._client_secret = config.tropipay_client_secret
            self._client_id = config.tropipay_client_id
            self._token = None
            self._token_expiration = None
            self._initialized = True
        except Config.DoesNotExist as exc:
            raise ConfigurationDoesNotExistException() from exc

    def get_token(self):
        return requests.post(f"{self._api_url}/api/v3/access/token", json={
            "grant_type": "client_credentials",
            "client_id": self._client_id,
            "client_secret": self._client_secret
        }, headers={'Content-Type': 'application/json', 'Accept': 'application/json'})

    def createpaymentcards(self, payload):
        print(payload)
        return requests.post(f"{self._api_url}/api/v3/paymentcards", json=payload, headers=self._get_headers())

    def get_paymentcard(self, paymentcard_id):
        return requests.get(f"{self._api_url}/api/v3/paymentcards/{paymentcard_id}", headers=self._get_headers())

    def _get_headers(self):
        if self._token_expiration is None or self._token_expiration <= datetime.now():
            self._token = self.get_token().json()
            print(self._token)
            self._token_expiration = datetime.now() + timedelta(seconds=float(self._token.get("expires_in")))
        return {'Authorization': f"Bearer {self._token.get('access_token')}", 'Content-Type': 'application/json',
                'Accept': 'application/json'}

    def is_valid_notify_payload(self, payload, originalCurrencyAmount):
        signaturev3 = payload.get('signaturev3')
        bankOrderCode = payload.get('data').get("bankOrderCode")

        secret = hashlib.sha1(self._client_secret.encode())
        signature = f"{bankOrderCode}{self._client_id}{secret}{originalCurrencyAmount}".encode()
        return signaturev3 == hashlib.sha256(signature).hexdigest()
