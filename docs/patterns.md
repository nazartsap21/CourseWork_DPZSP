# Design patterns in Forkful

Forkful uses twelve GoF patterns. Each one solves a concrete problem in a food delivery service and runs on real request paths; none exists only as a demo. The patterns work together: placing a single order goes through eight of them.

All paths below are relative to `backend/app/`. In the class diagrams every pattern has its own color (see the legend):

- [`diagrams/class-diagram.png`](diagrams/class-diagram.png): the whole backend.
- [`diagrams/class-diagram-checkout.png`](diagrams/class-diagram-checkout.png): the checkout patterns.
- [`diagrams/class-diagram-lifecycle.png`](diagrams/class-diagram-lifecycle.png): order lifecycle, events, commands and reports.

| # | Pattern | Category | Where | Color |
|---|---|---|---|---|
| 1 | [Strategy](#1-strategy--delivery-options) | Behavioral | `domain/delivery/strategies.py` | yellow |
| 2 | [Decorator](#2-decorator--stacking-discounts) | Structural | `domain/pricing/decorators.py`, `policy.py` | orange |
| 3 | [Builder](#3-builder--assembling-an-order) | Creational | `domain/orders/builder.py` | green |
| 4 | [Chain of Responsibility](#4-chain-of-responsibility--order-validation) | Behavioral | `domain/orders/validation.py` | blue |
| 5 | [State](#5-state--order-lifecycle) | Behavioral | `domain/orders/states.py` | red |
| 6 | [Observer](#6-observer--reacting-to-status-changes) | Behavioral | `domain/events/observers.py` | violet |
| 7 | [Singleton](#7-singleton--one-event-publisher) | Creational | `domain/events/publisher.py` | teal |
| 8 | [Factory Method](#8-factory-method--payment-gateways) | Creational | `domain/payments/factory.py` | tan |
| 9 | [Adapter](#9-adapter--stripe-and-osrm) | Structural | `domain/payments/stripe_adapter.py`, `domain/delivery/routing.py` | pink |
| 10 | [Facade](#10-facade--placing-an-order) | Structural | `services/checkout_facade.py` | grey |
| 11 | [Command](#11-command--reorder-and-cancel) | Behavioral | `domain/orders/commands.py`, `services/order_actions.py` | orchid |
| 12 | [Template Method](#12-template-method--reports) | Behavioral | `domain/reports/base.py`, `reports.py` | lime |

## How the patterns collaborate

```
POST /orders ─► CheckoutFacade.place_order                                  (Facade)
                 ├─ PaymentGatewayFactory.for_method("stripe")              (Factory Method)
                 │     → StripeGateway / MockGateway                         (Adapter)
                 ├─ OrderQuoteService.quote
                 │     ├─ OrderBuilder ... .build() → OrderDraft             (Builder)
                 │     ├─ DeliveryStrategyResolver.resolve(method).quote()   (Strategy)
                 │     ├─ OrderValidator chain .validate()                   (Chain of Responsibility)
                 │     └─ build_order_price → PriceComponent decorators      (Decorator)
                 ├─ initial_state(pays_online) → PendingPayment / Accepted   (State)
                 ├─ OrderRepository.create_from_draft
                 ├─ OrderEventPublisher.instance().publish(...)              (Singleton + Observer)
                 │     → StatusHistoryObserver, NotificationObserver, LoyaltyObserver
                 └─ PaymentService.start → PaymentGateway.start              (Adapter)
```

After checkout:

- **Status changes:** staff and couriers move the order with `PATCH /orders/{id}/status`. The State allows or refuses each move, and every move is published to the observers.
- **Courier pick-up:** asks the `RouteProvider` adapter (OSRM, with a straight-line fallback) for a route.
- **Customer actions:** reorder and cancel run as Commands. Cancel is executed by `OrderService.cancel`, so it goes through the State, refunds through the payment Adapter, and notifies the Observers.
- **Reports:** the admin's reports run the Template Method pipeline.

The sequence diagram [`diagrams/checkout-sequence.png`](diagrams/checkout-sequence.png) shows the checkout flow step by step.

---

## 1. Strategy — delivery options

**Problem.** Standard, express and pickup delivery compute the fee and the delivery time differently:

- **Standard:** a base fee plus a per-km fee; the ETA is prep time + courier wait + ride.
- **Express:** a higher fee; the kitchen prioritises the order, so prep time is ×0.75.
- **Pickup:** no fee and no address; the ETA is just prep time.

The customer picks the method at checkout, so the algorithm is chosen at runtime.

**Participants.**
- `DeliveryStrategy` (abstract): `quote(context) -> DeliveryQuote` and `requires_address`.
- `CourierDelivery`: shared fee formula for courier methods.
- `StandardDelivery`, `ExpressDelivery`, `PickupDelivery`: the concrete strategies.
- `DeliveryStrategyResolver`: the context; picks the strategy by `delivery_method`.

**Wiring.** The container builds `DeliveryStrategyResolver([StandardDelivery(), ExpressDelivery(), PickupDelivery()])` and injects it into `OrderQuoteService`.

```python
# services/quote_service.py — OrderQuoteService.quote
strategy = self._delivery_strategies.resolve(draft.delivery.method)
delivery = strategy.quote(
    DeliveryContext(
        restaurant=draft.restaurant.location,
        prep_minutes=draft.restaurant.prep_minutes,
        destination=draft.delivery.destination if strategy.requires_address else None,
    )
)
```

**Collaboration.**
- The strategy's fee is the input to the price decorators (2).
- Its `requires_address` tells `DeliveryZoneCheck` (4) whether to check the zone.
- Its ETA becomes `estimated_delivery_minutes` on the order, which the tracking page and the courier report (12) use.

**Why it helps (OCP).** A new method, e.g. "scheduled", is one new class and one line in the container. The checkout, validation and pricing code don't change.

## 2. Decorator — stacking discounts

**Problem.** Three discounts can apply in any combination:

- the regular-customer percentage;
- free delivery with a premium card;
- paying part of the order with bonus points.

A class per combination would explode (2³ variants). Each discount also has to show up as a line in the checkout breakdown.

**Participants.**
- `PriceComponent` (component): `subtotal()`, `delivery_fee()`, `total()`, `lines()`, `bonus_points_used()`.
- `BaseOrderPrice`: the concrete component (dishes + delivery).
- `PriceDecorator`: wraps an `inner` component and adds its `adjustment()` and `line()`.
- `RegularCustomerDiscount`, `PremiumFreeDelivery`, `BonusPointsRedemption`: the concrete decorators.

**Wiring.** `domain/pricing/policy.py` decides which decorators to apply and in what order. Points come last, so their cap is checked against the price after the other discounts.

```python
# domain/pricing/policy.py
price: PriceComponent = BaseOrderPrice(subtotal, delivery_fee)
if status.is_regular and rules.regular_customer_discount_percent > 0:
    price = RegularCustomerDiscount(price, rules.regular_customer_discount_percent)
if status.has_premium and delivery_fee > 0:
    price = PremiumFreeDelivery(price)
points = min(requested_points, status.points_balance)
if points > 0:
    price = BonusPointsRedemption(
        price, points, rules.point_value, rules.max_points_redemption_percent
    )
```

**Collaboration.**
- The delivery fee comes from the Strategy (1).
- The rules come from `LoyaltySettings`, which the admin edits.
- The resulting `PriceBreakdown` is stored on the order by the Facade (10) and charged through the payment gateway (8, 9).
- `POST /orders/quote` and `POST /orders` use the same function, so the quoted price and the charged price can't differ.

## 3. Builder — assembling an order

**Problem.** An order has many optional parts: dishes added one by one (the same dish twice increases the quantity), delivery details, a payment method and points to redeem. Each part has rules, such as "dishes from one restaurant only" or "quantity ≥ 1". A constructor with ten parameters would be unreadable and could create half-valid objects.

**Participants.**
- `OrderBuilder`: the builder, with step methods that return `self`.
- `OrderDraft`, `DraftItem`, `RestaurantSnapshot`, `DishSnapshot`: the immutable product. It is plain domain data, not ORM rows.

```python
# services/quote_service.py — OrderQuoteService._build_draft
builder = OrderBuilder(customer_id).for_restaurant(_restaurant_snapshot(restaurant))
for item in request.items:
    builder.add_item(_dish_snapshot(dishes[item.dish_id]), item.quantity)
builder.with_delivery(
    request.delivery_method, request.destination, request.delivery_address, request.delivery_note
).redeem_points(request.bonus_points)
if request.payment_method is not None:
    builder.with_payment(request.payment_method)
return builder.build()
```

**Collaboration.**
- The draft is what the validation chain (4) checks and the strategy (1) prices.
- `OrderRepository.create_from_draft` turns the draft into `Order`/`OrderItem` rows. It snapshots each item's name and price, so a later menu change doesn't rewrite history.
- GRASP Creator: the builder creates `DraftItem`s because it aggregates them.

## 4. Chain of Responsibility — order validation

**Problem.** An order is checked against several independent rules:

- the restaurant is open;
- the dishes are available;
- the minimum order amount is reached;
- the delivery point is inside the delivery zone;
- the customer has enough bonus points.

Each rule has its own error code and form field, and the cheapest, most basic checks should run first. One function with a long `if` cascade would be hard to extend or reorder.

**Participants.**
- `OrderValidator` (handler): `set_next()`, `validate()` (runs its `check`, then passes to the next link), abstract `check()`.
- Concrete handlers: `RestaurantActiveCheck`, `ItemsAvailableCheck`, `MinOrderAmountCheck`, `DeliveryZoneCheck`, `BonusPointsCheck`.

```python
# domain/orders/validation.py
def build_order_validation_chain() -> OrderValidator:
    head = RestaurantActiveCheck()
    (
        head.set_next(ItemsAvailableCheck())
        .set_next(MinOrderAmountCheck())
        .set_next(DeliveryZoneCheck())
        .set_next(BonusPointsCheck())
    )
    return head
```

**How the chain stops.** A handler stops it by raising `OrderValidationError` (a `BusinessRuleError` with a `code` and `field`). The error handler turns it into 422 with `details: [{field, message}]`, and the checkout page shows it next to the right field.

**Collaboration.**
- The quote endpoint runs the chain and returns the error in the quote, so the UI can warn early. `CheckoutFacade` (10) raises it and refuses the order.
- `DeliveryZoneCheck` relies on the Strategy's `requires_address` (1).
- `BonusPointsCheck` uses the same redemption cap from `LoyaltySettings` (`max_redeemable_points`) as `BonusPointsRedemption` (2).

## 5. State — order lifecycle

**Problem.** What can happen to an order depends on its status:

- only an accepted order can start preparing;
- a pickup order skips "delivering";
- cancelling is allowed only before the kitchen starts.

Scattered `if status == ...` checks in every service would drift apart. An invalid move must be impossible and must return a clear error (HTTP 409).

**Participants.**
- `OrderState` (abstract): one method per action, `pay`, `start_preparing`, `mark_ready`, `pick_up`, `deliver`, `cancel`. By default each one refuses with `InvalidTransitionError`.
- Concrete states: `PendingPayment`, `Accepted`, `Preparing`, `ReadyForPickup`, `Delivering`, `Delivered`, `Cancelled`. Each overrides only the actions it allows.
- Helpers: `OrderFacts(is_pickup)` carries per-order facts that change the rules; `state_for(status)` rebuilds the state from the stored string; `initial_state(pays_online)` gives the first state.

```python
# domain/orders/states.py
class ReadyForPickup(OrderState):
    status = "ready_for_pickup"
    label = "Ready for pickup"

    def pick_up(self, facts: OrderFacts) -> OrderState:
        if facts.is_pickup:
            raise InvalidTransitionError(
                "Pickup orders are collected by the customer, not a courier."
            )
        return DELIVERING

    def deliver(self, facts: OrderFacts) -> OrderState:
        # Pickup orders skip Delivering: handing the bag over completes them.
        if not facts.is_pickup:
            raise InvalidTransitionError("A courier must pick the order up before delivering it.")
        return DELIVERED
```

**Wiring.**
- `OrderService.change_status`: `state_for(order.status).apply(action, facts)`, then `transition()` publishes the change.
- `PaymentService._accept_order`: `state_for(...).pay(...)`.
- `CheckoutFacade`: `initial_state(gateway.is_online)`.
- `OrderService.available_transitions`: combines `available_actions()` with the permission policy (`domain/orders/permissions.py`). This list drives the admin's status buttons, so the UI can only offer valid moves.

Diagram: [`diagrams/order-state.png`](diagrams/order-state.png).

## 6. Observer — reacting to status changes

**Problem.** A status change has several side effects:

- a status history row;
- an in-app notification for the customer;
- on `delivered`, bonus points and a completed-order count.

The code that changes statuses (checkout, payment confirmation, staff, couriers, cancel) shouldn't know about any of them. Otherwise every new reaction would mean editing five services.

**Participants.**
- `OrderEventPublisher`: the subject (see 7).
- `OrderObserver` (abstract): `on_status_changed(event)`.
- Concrete observers: `StatusHistoryObserver`, `NotificationObserver`, `LoyaltyObserver`.
- `OrderStatusChanged`: the event, plain immutable data.
- Observers write through small protocols (`StatusHistorySink`, `NotificationSink`, `LoyaltyLedger`), which the repositories implement. The domain stays free of SQLAlchemy.

```python
# domain/events/observers.py
class LoyaltyObserver(OrderObserver):
    def on_status_changed(self, event: OrderStatusChanged) -> None:
        if event.new_status != "delivered":
            return
        points = points_earned(self._ledger.rules(), event.total)
        balance = self._ledger.record_completed_order(event.customer_id, event.order_id, points)
        ...
```

**Wiring.**
- `register_order_observers()` in `container.py` subscribes the three observers once, from `create_app()`.
- Every status change goes through `services/order_events.py` (`transition` / `publish_status`).
- Observers run synchronously in the caller's transaction, so the status and its side effects commit or roll back together.

## 7. Singleton — one event publisher

**Problem.** Checkout, payments, staff status changes, the courier workspace and the cancel command all publish events. If any of them had its own publisher instance, observers registered at startup would silently miss its events.

**Participant.** `OrderEventPublisher`. `__new__` always returns the one class-level instance; `instance()` is the explicit accessor.

```python
# domain/events/publisher.py
def __new__(cls) -> "OrderEventPublisher":
    if cls._instance is None:
        instance = super().__new__(cls)
        instance._observers = []
        cls._instance = instance
    return cls._instance
```

**Wiring.** The container takes `OrderEventPublisher.instance()` and passes it into the services' constructors. Services receive the publisher as a dependency rather than calling the global, so they stay testable (DIP).

**Tradeoffs.**
- It is global, process-wide state. `reset()` exists so the app factory (and tests) can start from an empty observer list, which also prevents duplicate subscriptions when the app is created twice.
- Two Flask apps in one process would share observers. This project never does that.
- With several worker processes each has its own instance. That is correct here, because observers act synchronously within the request that changed the order.

## 8. Factory Method — payment gateways

**Problem.** The customer chooses "card online" or "cash", but the class that handles a card payment depends on the configuration:

- with `STRIPE_SECRET_KEY` set, Stripe;
- without it, a mock that behaves like a successful payment, so the project runs with no keys.

Later operations (verify, refund) must reach the gateway that handled the payment. Callers must not contain this decision.

**Participants.**
- `PaymentGatewayFactory`: `for_method(method)` and `for_provider(provider)`. They create the product from a registry of creators; the Stripe creator is a lazy callable built only when a key exists.
- `PaymentGateway`: the product interface.
- `CashGateway`, `MockGateway`, `StripeGateway`: the concrete products.

```python
# domain/payments/factory.py
self._creators = {
    CashGateway.provider: CashGateway,
    MockGateway.provider: MockGateway,
    "stripe": stripe_gateway or MockGateway,
}
```

**Collaboration.**
- `CheckoutFacade` (10) asks for the gateway before pricing, so the order records the provider that really takes the money.
- The gateway's `is_online` picks the initial State (5): online orders start as `PendingPayment`, cash orders as `Accepted`.
- `OrderService.cancel` uses `for_provider` to refund through the right gateway.

## 9. Adapter — Stripe and OSRM

**Problem.** Two third-party APIs have their own shapes:

- **Stripe SDK:** Checkout Sessions, PaymentIntents, `StripeError`.
- **OSRM HTTP API:** `lng,lat` paths, GeoJSON, `code: "Ok"`.

Domain code must not depend on either one: not in tests, not when the key is missing, and not when the service is down.

**Participants.**
- **Payments:**
  - Target: `PaymentGateway` (`start`, `verify`, `refund`).
  - Adapter: `StripeGateway`.
  - Adaptee: `stripe.StripeClient`.
  - Stripe errors become `PaymentProviderError` (HTTP 502).
- **Routing:**
  - Target: `RouteProvider.route(origin, destination) -> Route`.
  - Adapter: `OsrmRouteProvider`, which turns OSRM's JSON into `Route(points, distance_km)`.
  - Alternatives: `StraightLineRouteProvider` for offline use, and `FallbackRouteProvider`, which composes a primary provider with a fallback.

```python
# domain/delivery/routing.py — OsrmRouteProvider.route (excerpt)
coordinates = f"{origin.lng},{origin.lat};{destination.lng},{destination.lat}"
payload = self._http_get(url, {"overview": "full", "geometries": "geojson"}, self._timeout)
...
points = [GeoPoint(lat=lat, lng=lng) for lng, lat in best["geometry"]["coordinates"]]
return Route(points=points, distance_km=best["distance"] / 1000, provider="osrm")
```

**Wiring.**
- `FallbackRouteProvider(OsrmRouteProvider(OSRM_BASE_URL), StraightLineRouteProvider())` is injected into `OrderService`. On "picked up", it stores the polyline and `picked_up_at`. The courier's position is interpolated along it on every tracking request (`domain/delivery/tracking.py`), with no background jobs.
- `StripeGateway` is created by the Factory Method (8).
- GRASP: Indirection and Protected Variations.

## 10. Facade — placing an order

**Problem.** Placing an order involves the builder, the validation chain, a delivery strategy, the price decorators, the gateway factory, the initial state, three repositories, the payment session and the event publisher, all in one transaction. The HTTP layer shouldn't orchestrate any of that.

**Participant.** `CheckoutFacade.place_order(request, customer_id) -> CheckoutResult`. It is the only thing `POST /orders` calls.

```python
# services/checkout_facade.py (excerpt)
gateway = self._payments.gateway_for(request.payment_method)
quote = self._quotes.quote(replace(request.quote, payment_method=gateway.provider), customer_id)
if quote.validation_error is not None:
    raise quote.validation_error
state = initial_state(pays_online=gateway.is_online)
try:
    order = self._orders.create_from_draft(quote.draft, quote.price, status=state.status, ...)
    publish_status(self._events, order, old_status=None, changed_by_id=customer_id)
    self._spend_points(customer_id, order)
    redirect_url = self._payments.start(order, gateway)
    self._orders.commit()
except Exception:
    self._orders.rollback()
    raise
```

**Collaboration.**
- The facade touches Factory Method (8), Adapter (9), Builder (3), Strategy (1), Chain (4), Decorator (2), State (5), and Observer/Singleton (6, 7).
- If the payment provider fails, the whole order rolls back, so no unpaid order is left behind.
- GRASP Controller: the blueprint delegates the "place order" system operation to it.

## 11. Command — reorder and cancel

**Problem.** "Order again" and "Cancel" are user actions that:

- may run from the account, the order page and the admin page;
- should be self-contained, with their parameters packed into an object;
- should be logged uniformly: who, what, result, duration, error code.

Reorder also has to handle dishes that were removed, are sold out, or changed price.

**Participants.**
- `Command[ResultT]`: `execute()` and `describe()`.
- `ReorderCommand`: rebuilds a cart from a past order through the `PastOrders` / `CurrentMenu` ports and reports skipped items and price changes.
- `CancelOrderCommand`: its receiver is `OrderService.cancel`, which runs the State, refunds and events.
- `CommandInvoker`: runs a command and records a `CommandLogEntry` whether it succeeds or fails.
- `CommandLog` / `LoggerCommandLog`: write to the `forkful.commands` logger.
- `OrderActions`: the client; it builds the command and hands it to the invoker.

```python
# services/order_actions.py
def cancel(self, order_id: int, actor: Actor) -> Order:
    command = CancelOrderCommand(order_id, actor.user_id, actor.role, self._orders)
    return self._invoker.run(command, actor_id=actor.user_id)
```

**Collaboration.**
- Cancel goes through the State (5): `cancel` is allowed only from `pending_payment` and `accepted`.
- It refunds an online payment through the gateway Adapter (9) and returns redeemed points.
- It publishes `cancelled` to the Observers (6).
- Reorder only rebuilds a cart. The customer still checks out through the Facade (10), so the current prices and rules apply.

## 12. Template Method — reports

**Problem.** The admin has three reports: sales by restaurant, popular dishes and courier performance. They share one pipeline: take a period, fetch records, group them, turn groups into table rows, add a totals row, output JSON or CSV. Only the data steps differ. Copying the pipeline three times would let the period rules and the output format drift apart.

**Participants.**
- `ReportGenerator`: the abstract class. Its template method `generate(period)` calls `collect` → `aggregate` → `format_rows` → `totals`. The first three are abstract; `totals` is a hook that returns `None` by default.
- `SalesByRestaurantReport`, `PopularDishesReport`, `CourierPerformanceReport`: the concrete classes.
- Shared pieces: `ReportPeriod` (validated, inclusive dates) and `to_csv()`.
- `ReportDataSource`: a protocol implemented by `repositories/report_repository.py`. The SQL stays out of the domain.

```python
# domain/reports/base.py
def generate(self, period: ReportPeriod) -> Report:
    records = self.collect(period)
    groups = self.aggregate(records)
    rows = self.format_rows(groups)
    return Report(key=self.key, title=self.title, period=period,
                  columns=self.columns, rows=rows, totals=self.totals(rows))
```

**Wiring.**
- `ReportService` receives the list of generators from the container and finds one by `key`.
- `GET /admin/reports/{key}?date_from=&date_to=[&format=csv]` returns the report.
- The admin page builds its table from `columns` and their `kind` (money, minutes, percent), so a new report needs one subclass and one line in the container.

**Collaboration.** The courier report's "on time" metric compares the delivery time with the ETA the Strategy (1) promised at checkout. The delivery time comes from the status history the Observer (6) wrote.

---

## Patterns considered and not used

- **Abstract Factory.** There is only one family of products (payment gateways), so a plain Factory Method is enough.
- **Mediator.** The publisher already decouples the services from the reactions to status changes. A mediator between services would add a layer without removing any dependency.
- **Proxy for caching the catalog.** The catalog queries are fast at this scale, and a cache would add invalidation rules for admin edits.
