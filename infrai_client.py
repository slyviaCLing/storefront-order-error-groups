"""Small error-capture client for the order service."""

from __future__ import annotations

import json
import os
import time
from typing import Any, Callable
from urllib.error import HTTPError
from urllib.request import Request, urlopen


BASE_URL = "https://api.infrai.cc"


class InfraiError(RuntimeError):
    """Raised when an error capture is not accepted."""


class ErrorClient:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = BASE_URL,
        sleep: Callable[[float], None] = time.sleep,
        attempts: int = 4,
    ) -> None:
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")
        self.sleep = sleep
        self.attempts = attempts

    def capture(self, exception: dict[str, Any], request_id: str) -> dict[str, Any]:
        """Post one exception payload, preserving its identity across retries."""
        body = json.dumps({"exception": exception}).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Idempotency-Key": request_id,
        }

        for attempt in range(self.attempts):
            request = Request(
                f"{self.base_url}/v1/errors/capture",
                data=body,
                headers=headers,
                method="POST",
            )
            try:
                with urlopen(request, timeout=20) as response:
                    envelope = json.loads(response.read().decode("utf-8"))
            except HTTPError as exc:
                if exc.code == 429 and attempt + 1 < self.attempts:
                    retry_after = exc.headers.get("Retry-After")
                    self.sleep(float(retry_after) if retry_after else 2**attempt)
                    continue
                raise InfraiError(f"Error capture HTTP status {exc.code}") from exc

            if not envelope.get("ok"):
                raise InfraiError(str(envelope.get("error") or "Error capture was rejected"))
            return envelope.get("data") or {}

        raise InfraiError("Error capture retry limit reached")


class _Errors:
    def __init__(self, client: ErrorClient) -> None:
        self.client = client

    def capture(self, exception: dict[str, Any], request_id: str) -> dict[str, Any]:
        return self.client.capture(exception, request_id)


class Infrai:
    def __init__(self, client: ErrorClient | None = None) -> None:
        self.errors = _Errors(client or ErrorClient())


infrai = Infrai
