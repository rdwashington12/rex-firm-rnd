from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from app.domain.models import TradeIdea

LOGGER = logging.getLogger(__name__)


class AlpacaPaperClient:
    def __init__(
        self,
        api_key: str,
        secret_key: str,
        base_url: str,
        timeout_seconds: float,
        max_retries: int,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.headers = {
            "APCA-API-KEY-ID": api_key,
            "APCA-API-SECRET-KEY": secret_key,
            "Content-Type": "application/json",
        }

    async def _request(self, method: str, path: str, json_payload: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    response = await client.request(
                        method,
                        url,
                        headers=self.headers,
                        json=json_payload,
                    )
                response.raise_for_status()
                return response.json() if response.content else {}
            except (httpx.TimeoutException, httpx.HTTPError) as exc:
                if attempt == self.max_retries:
                    LOGGER.error("alpaca_request_failed", extra={"path": path, "error": str(exc)})
                    raise
                backoff = min(2 ** attempt, 10)
                LOGGER.warning(
                    "alpaca_request_retry",
                    extra={"path": path, "attempt": attempt, "backoff_seconds": backoff},
                )
                await asyncio.sleep(backoff)
        return {}

    async def submit_options_order(self, idea: TradeIdea, client_order_id: str) -> dict[str, Any]:
        order_class = "simple"
        legs: list[dict[str, Any]] = []
        if "spread" in idea.strategy:
            order_class = "multileg"
            legs = [
                {
                    "symbol": idea.symbol,
                    "qty": "1",
                    "side": "buy",
                    "type": "limit",
                    "time_in_force": "day",
                },
                {
                    "symbol": idea.symbol,
                    "qty": "1",
                    "side": "sell",
                    "type": "limit",
                    "time_in_force": "day",
                },
            ]

        payload: dict[str, Any] = {
            "symbol": idea.symbol,
            "qty": "1",
            "side": "buy",
            "type": "market",
            "time_in_force": "day",
            "order_class": order_class,
            "client_order_id": client_order_id,
        }
        if legs:
            payload["legs"] = legs

        return await self._request("POST", "/v2/orders", payload)

    async def get_order(self, order_id: str) -> dict[str, Any]:
        return await self._request("GET", f"/v2/orders/{order_id}")

    async def list_open_orders(self) -> list[dict[str, Any]]:
        data = await self._request("GET", "/v2/orders?status=open")
        if isinstance(data, list):
            return data
        return []

    async def list_positions(self) -> list[dict[str, Any]]:
        data = await self._request("GET", "/v2/positions")
        if isinstance(data, list):
            return data
        return []
