"""Adapter: Stripe Checkout behind our `PaymentGateway` interface.

The Stripe SDK speaks in sessions, `payment_status` strings and its own error
classes; this class translates them into `PaymentSession`,
`PaymentVerification` and `PaymentProviderError`. Nothing outside this file
imports `stripe`.
"""

import stripe

from .gateways import (
    PaymentGateway,
    PaymentProviderError,
    PaymentRequest,
    PaymentSession,
    PaymentVerification,
)


class StripeGateway(PaymentGateway):
    provider = "stripe"

    def __init__(self, client: stripe.StripeClient) -> None:
        self._client = client

    def start(self, request: PaymentRequest) -> PaymentSession:
        try:
            session = self._client.checkout.sessions.create(
                params={
                    "mode": "payment",
                    # One line with the final total: discounts and points are already applied.
                    "line_items": [
                        {
                            "quantity": 1,
                            "price_data": {
                                "currency": request.currency,
                                "unit_amount": request.amount,
                                "product_data": {"name": request.description},
                            },
                        }
                    ],
                    "customer_email": request.customer_email,
                    # Stripe substitutes {CHECKOUT_SESSION_ID} itself.
                    "success_url": request.success_url,
                    "cancel_url": request.cancel_url,
                    "metadata": {"order_id": str(request.order_id)},
                }
            )
        except stripe.StripeError as error:
            raise PaymentProviderError(
                f"The payment service is unavailable: {error.user_message or 'try again later'}."
            ) from error
        if not session.url:
            raise PaymentProviderError("The payment service didn't return a payment page.")
        return PaymentSession(external_id=session.id, redirect_url=session.url)

    def verify(self, external_id: str) -> PaymentVerification:
        try:
            session = self._client.checkout.sessions.retrieve(external_id)
        except stripe.StripeError as error:
            raise PaymentProviderError("Couldn't check the payment with Stripe.") from error
        return PaymentVerification(
            is_paid=session.payment_status == "paid", amount=session.amount_total
        )
