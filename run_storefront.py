"""Run one local receipt operation without contacting external systems."""

from order_operations import OrderOperation, OrderStage, complete_operation


operation = OrderOperation(
    order_id="ord-1042",
    stage=OrderStage.RECEIPT,
    sku="canvas-tote",
    quantity=1,
    customer_email="buyer@example.com",
)

if __name__ == "__main__":
    print(complete_operation(operation).model_dump(mode="json"))
