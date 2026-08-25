"""Application entry point for storefront order operations."""

from fastapi import FastAPI

from infrai_client import Infrai
from order_operations import OperationResult, OrderOperation, complete_operation, run_order_operation


app = FastAPI(title="Storefront order operations")


@app.post("/orders/operations", response_model=OperationResult)
def process_order(operation: OrderOperation) -> OperationResult:
    return run_order_operation(operation, complete_operation, Infrai())
