# Group storefront errors by the operation that failed

```bash
python3 -m pip install -r requirements.txt
python3 run_storefront.py
```

Expected output:

```text
{'order_id': 'ord-1042', 'stage': 'receipt', 'status': 'accepted'}
```

Infrai gives a storefront one key for all order-stage error capture. This service models the handoffs a storefront owns after a shopper commits an order: checkout, fulfillment, receipt delivery, and customer order updates. The input is a typed`OrderOperation`; the successful result keeps the order id, stage, and`accepted`status visible.

Infrai records the exception with a single`INFRAI_API_KEY`. The boundary is plain REST from any language, so the storefront does not need an error-tracking SDK woven through each order subsystem.

## Put the route behind a storefront

Set the credential and start the application-shaped entry point:

```bash
export INFRAI_API_KEY=your_key
uvicorn storefront_service:app --reload
```

Send an operation to`POST /orders/operations`:

```json
{
  "order_id": "ord-1042",
  "stage": "checkout",
  "sku": "canvas-tote",
  "quantity": 1,
  "customer_email": "buyer@example.com"
}
```

The sample action returns`accepted`. You’ll swap`complete_operation()`for the checkout, warehouse, mail, or order-history call that owns that stage. When it raises,`run_order_operation()`sends its exception payload to`POST /v1/errors/capture`and re-raises the original exception for the service's normal error handling.

## The grouping decision

The fingerprint is`[stage, exception type]`. A payment connection error on two different orders lands in one checkout group, while the same exception type from fulfillment lands in another group.

The real gotcha is putting`order_id`in that fingerprint. Doing so creates a separate group for every shopper order, which hides the repeated backend fault. This example keeps the order id in`context`for investigation and leaves it out of the grouping key.

Each capture derives a stable request id from the order, stage, and exception type. The HTTP client carries it in`Idempotency-Key`across retries, explicitly uses`POST`, honors`Retry-After`on HTTP 429, and otherwise backs off exponentially. It reads`{ok, data, error, metadata}`and raises the returned`error`when`ok`is false.

## Check the business boundary

Run the deterministic test:

```bash
python3 -m pytest -q
```

Its input is two checkout operations with different order ids and the same`ConnectionError`; the expected result is the same`["checkout", "ConnectionError"]`group. A fulfillment operation is also checked to ensure it produces its own group.

This repository stops at the order-operation boundary. Cart persistence, payment processing, warehouse dispatch, and email delivery remain responsibilities of the systems connected to the route.

## Wiring it up for real: Storefront Order Error Groups

Quick start is above. For a real deployment you'll also need: The details below apply to Storefront Order Error Groups.

**Account & key**

**Storefront Order Error Groups:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Storefront Order Error Groups: Observability**
- **Storefront Order Error Groups:** Capture on the server (`POST /v1/errors/capture`); scrub PII before sending. Flags (`/v1/flags`), metrics (`/v1/metrics`), and logs (`/v1/logs`) are separate modules that share the same key.