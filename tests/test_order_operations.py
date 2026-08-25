from order_operations import OrderOperation, OrderStage, error_fingerprint


def test_checkout_failures_group_across_orders() -> None:
    first = OrderOperation(
        order_id="ord-1001",
        stage=OrderStage.CHECKOUT,
        sku="canvas-tote",
        quantity=1,
        customer_email="first@example.com",
    )
    second = first.model_copy(update={"order_id": "ord-1002"})

    first_group = error_fingerprint(first, ConnectionError("payment provider declined"))
    second_group = error_fingerprint(second, ConnectionError("payment provider declined"))

    assert first_group == ["checkout", "ConnectionError"]
    assert second_group == first_group


def test_fulfillment_is_a_separate_group() -> None:
    operation = OrderOperation(
        order_id="ord-1001",
        stage=OrderStage.FULFILLMENT,
        sku="canvas-tote",
        quantity=1,
        customer_email="buyer@example.com",
    )

    assert error_fingerprint(operation, ConnectionError("warehouse unavailable")) == [
        "fulfillment",
        "ConnectionError",
    ]
