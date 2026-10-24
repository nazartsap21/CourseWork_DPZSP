// Money fields are integer kopiyky, as returned by the API.

export type DeliveryMethod = "standard" | "express" | "pickup";
export type PaymentMethod = "stripe" | "cash" | "mock";
export type PaymentStatus = "pending" | "paid" | "failed" | "refunded";
export type OrderStatus =
  | "pending_payment"
  | "accepted"
  | "preparing"
  | "ready_for_pickup"
  | "delivering"
  | "delivered"
  | "cancelled";

export interface OrderItemPayload {
  dish_id: number;
  quantity: number;
}

export interface QuotePayload {
  restaurant_id: number;
  items: OrderItemPayload[];
  delivery_method: DeliveryMethod;
  delivery_lat?: number;
  delivery_lng?: number;
  bonus_points?: number;
}

export interface CheckoutPayload extends QuotePayload {
  payment_method: PaymentMethod;
  delivery_address?: string;
  delivery_note?: string;
}

export interface QuotedItem {
  dish_id: number;
  name: string;
  price: number;
  quantity: number;
  line_total: number;
  is_available: boolean;
}

export interface PriceLine {
  code: string;
  label: string;
  amount: number;
}

export interface DeliveryQuote {
  method: DeliveryMethod;
  fee: number;
  eta_minutes_min: number;
  eta_minutes_max: number;
  distance_km: number | null;
  needs_courier: boolean;
  is_priority: boolean;
}

export interface ValidationIssue {
  code: string;
  message: string;
  field: string | null;
}

export interface Quote {
  restaurant_id: number;
  items: QuotedItem[];
  delivery: DeliveryQuote;
  lines: PriceLine[];
  subtotal: number;
  delivery_fee: number;
  discount: number;
  bonus_points_used: number;
  total: number;
  loyalty: {
    is_regular: boolean;
    has_premium: boolean;
    points_balance: number;
    max_redeemable_points: number;
  };
  delivery_radius_km: number;
  validation_error: ValidationIssue | null;
}

export interface OrderItem {
  dish_id: number | null;
  name: string;
  price: number;
  quantity: number;
}

export interface Order {
  id: number;
  status: OrderStatus;
  restaurant: { id: number; name: string; address: string; lat: number; lng: number };
  items: OrderItem[];
  delivery_method: DeliveryMethod;
  delivery_address: string | null;
  delivery_note: string | null;
  delivery_lat: number | null;
  delivery_lng: number | null;
  subtotal: number;
  delivery_fee: number;
  discount: number;
  bonus_points_used: number;
  total: number;
  payment_method: PaymentMethod;
  payment_status: PaymentStatus;
  estimated_delivery_minutes: number | null;
  created_at: string;
  status_history: { status: OrderStatus; changed_at: string }[];
}
