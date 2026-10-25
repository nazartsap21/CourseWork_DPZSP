import type { DeliveryMethod, PaymentMethod } from "@/types/orders";

export const DELIVERY_METHOD_LABELS: Record<DeliveryMethod, { title: string; description: string }> = {
  standard: { title: "Standard", description: "Courier delivery" },
  express: { title: "Express", description: "Cooked first, courier comes straight to you" },
  pickup: { title: "Pickup", description: "Collect it yourself, no fee" },
};

export const PAYMENT_METHOD_LABELS: Record<PaymentMethod, string> = {
  stripe: "Card online",
  mock: "Card online",
  cash: "Cash",
};
