import type { DeliveryMethod, OrderStatus, PaymentMethod } from "@/types/orders";

export const DELIVERY_METHOD_LABELS: Record<DeliveryMethod, { title: string; description: string }> = {
  standard: { title: "Standard", description: "Courier delivery" },
  express: { title: "Express", description: "Cooked first, courier comes straight to you" },
  pickup: { title: "Pickup", description: "Collect it yourself, no fee" },
};

/** Short status names for lists (the tracking page has its own, longer headlines). */
export const ORDER_STATUS_LABELS: Record<OrderStatus, string> = {
  pending_payment: "Waiting for payment",
  accepted: "Accepted",
  preparing: "Preparing",
  ready_for_pickup: "Ready",
  delivering: "On the way",
  delivered: "Delivered",
  cancelled: "Cancelled",
};

export const PAYMENT_METHOD_LABELS: Record<PaymentMethod, string> = {
  stripe: "Card online",
  mock: "Card online",
  cash: "Cash",
};
