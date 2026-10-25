export type CardType = "standard" | "premium";
export type BonusReason = "order_accrual" | "order_redemption" | "redemption_refund" | "admin_adjustment";

export interface BonusTransaction {
  delta: number;
  reason: BonusReason;
  order_id: number | null;
  created_at: string;
}

export interface Loyalty {
  points_balance: number;
  card_type: CardType;
  premium_until: string | null;
  has_premium: boolean;
  completed_orders: number;
  is_regular: boolean;
  /** Orders still needed for the regular-customer discount (0 once reached). */
  orders_to_regular: number;
  /** Money values in kopiyky. */
  rules: {
    points_per_100_uah: number;
    point_value: number;
    max_points_redemption_percent: number;
    regular_customer_threshold: number;
    regular_customer_discount_percent: number;
    premium_card_price: number;
    premium_card_days: number;
  };
  transactions: BonusTransaction[];
}
