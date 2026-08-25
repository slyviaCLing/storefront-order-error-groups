"""Typed order operations and their error-grouping boundary."""

from __future__ import annotations

import hashlib
import traceback
from collections.abc import Callable
from enum import Enum
from typing import Any, TypeVar

from pydantic import BaseModel, Field

from infrai_client import Infrai


class OrderStage(str, Enum):
    CHECKOUT = "checkout"
    FULFILLMENT = "fulfillment"
    RECEIPT = "receipt"
    CUSTOMER_UPDATE = "customer_update"


class OrderOperation(BaseModel):
    order_id: str = Field(min_length=1)
    stage: OrderStage
    sku: str = Field(min_length=1)
    quantity: int = Field(gt=0)
    customer_email: str = Field(min_length=3)


class OperationResult(BaseModel):
    order_id: str
    stage: OrderStage
    status: str


ResultT = TypeVar("ResultT")


def error_fingerprint(operation: OrderOperation, exc: Exception) -> list[str]:
    """Group equivalent storefront failures across individual orders."""
    return [operation.stage.value, type(exc).__name__]


def run_order_operation(
    operation: OrderOperation,
    action: Callable[[OrderOperation], ResultT],
    tracker: Infrai,
) -> ResultT:
    try:
        return action(operation)
    except Exception as exc:
        fingerprint = error_fingerprint(operation, exc)
        request_id = hashlib.sha256(
            f"{operation.order_id}:{operation.stage.value}:{type(exc).__name__}".encode()
        ).hexdigest()
        infrai = tracker
        infrai.errors.capture(
            {
                "type": type(exc).__name__,
                "message": str(exc),
                "traceback": traceback.format_exc(),
                "fingerprint": fingerprint,
                "context": {
                    "order_id": operation.order_id,
                    "stage": operation.stage.value,
                    "sku": operation.sku,
                    "quantity": operation.quantity,
                },
            },
            request_id,
        )
        raise


def complete_operation(operation: OrderOperation) -> OperationResult:
    """Represent a successful handoff to the selected order subsystem."""
    return OperationResult(
        order_id=operation.order_id,
        stage=operation.stage,
        status="accepted",
    )
