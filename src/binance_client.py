import time
import hmac
import hashlib
import requests
from urllib.parse import urlencode
from typing import Any, Dict, Optional

from src.common.logger import get_logger


class BinanceFuturesClient:
    """
    Minimal REST client for Binance USDT-M Futures.
    Defaults to Testnet base URL per requirements.
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str = "https://testnet.binancefuture.com",
        recv_window: int = 5000,
        log_file_path: str = "bot.log",
    ) -> None:
        self.api_key = api_key
        self.api_secret = api_secret.encode()
        self.base_url = base_url.rstrip("/")
        self.recv_window = recv_window
        self.logger = get_logger("bot", log_file_path)
        self._fapi_prefix = "/fapi"

    def _sign(self, params: Dict[str, Any]) -> str:
        query = urlencode(params, doseq=True)
        return hmac.new(self.api_secret, query.encode("utf-8"), hashlib.sha256).hexdigest()

    def _headers(self, private: bool = True) -> Dict[str, str]:
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        if private:
            headers["X-MBX-APIKEY"] = self.api_key
        return headers

    def _request(self, method: str, path: str, params: Optional[Dict[str, Any]] = None, private: bool = False) -> Dict[str, Any]:
        url = f"{self.base_url}{self._fapi_prefix}{path}"
        params = params or {}
        if private:
            params["timestamp"] = int(time.time() * 1000)
            params["recvWindow"] = self.recv_window
            params["signature"] = self._sign(params)
        self.logger.info(
            "sending request",
            extra={"event": "api_request", "data": {"method": method, "url": url, "params": params}},
        )
        resp = requests.request(method, url, headers=self._headers(private), params=params if method == "GET" else None, data=params if method != "GET" else None, timeout=10)
        try:
            payload = resp.json()
        except Exception:
            payload = {"status_code": resp.status_code, "text": resp.text}
        if resp.ok:
            self.logger.info("received response", extra={"event": "api_response", "data": payload})
        else:
            self.logger.error("api error", extra={"event": "api_error", "data": payload})
        return payload

    # Public endpoints
    def exchange_info(self) -> Dict[str, Any]:
        return self._request("GET", "/v1/exchangeInfo")

    # Private endpoints
    def place_order(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/v1/order", params=params, private=True)

    def cancel_order(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("DELETE", "/v1/order", params=params, private=True)