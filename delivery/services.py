import requests
from websocket import WebSocketApp


class AsTrackCubaServices:
    def __init__(self, http_url: str, socket_url: str, token: str):
        self._http_url = http_url
        self._socket_url = socket_url
        self._token = token

        self._cookies = None

    def _set_cookies(self, cookies):
        self._cookies = cookies

    def session(self):
        data = requests.get(self._http_url + "/api/session", params={"token": self._token})
        data.raise_for_status()
        self._set_cookies(data.cookies)
        return data.json()

    def devices(self):
        self.__init_cookies()
        data = requests.get(self._http_url + "/api/devices", cookies=self._cookies)
        data.raise_for_status()
        return data.json()

    def socket(self, **kwargs):
        self.__init_cookies()
        cookie_str = '; '.join([f'{name}={value}' for name, value in self._cookies.items()])
        return WebSocketApp(url=self._socket_url + '/api/socket', cookie=cookie_str, **kwargs)

    def socket_using_token(self, **kwargs):
        return WebSocketApp(url=self._socket_url + f'/api/socket?token={self._token}', **kwargs)

    def __init_cookies(self):
        if not self._cookies:
            self.session()
