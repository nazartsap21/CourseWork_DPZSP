import type { Cuisine, Dish } from "./catalog";
import type { DeliveryMethod, OrderStatus, PaymentMethod, PaymentStatus } from "./orders";

/** Money fields are integer kopiyky. */
export interface AdminRestaurant {
  id: number;
  name: string;
  description: string;
  address: string;
  lat: number;
  lng: number;
  avg_prep_minutes: number;
  min_order_amount: number;
  image_url: string | null;
  is_active: boolean;
  cuisines: Cuisine[];
}

export interface AdminRestaurantRow extends AdminRestaurant {
  dish_count: number;
}

export interface AdminCuisine extends Cuisine {
  restaurant_count: number;
}

export type RestaurantPayload = Omit<AdminRestaurant, "id" | "cuisines"> & { cuisine_ids: number[] };

export type DishPayload = Pick<Dish, "name" | "description" | "price" | "category" | "is_available" | "image_url">;

export interface AdminCourier {
  id: number;
  name: string;
  email: string;
  phone: string | null;
  active_order_ids: number[];
  delivered_today: number;
}

export interface AdminOrderRow {
  id: number;
  status: OrderStatus;
  delivery_method: DeliveryMethod;
  payment_method: PaymentMethod;
  payment_status: PaymentStatus;
  /** Kopiyky. */
  total: number;
  created_at: string;
  restaurant_name: string;
  customer_name: string;
  courier_name: string | null;
}

/** Money values in kopiyky, percentages as whole numbers. */
export interface LoyaltySettings {
  points_per_100_uah: number;
  point_value: number;
  max_points_redemption_percent: number;
  regular_customer_threshold: number;
  regular_customer_discount_percent: number;
  premium_card_price: number;
  premium_card_days: number;
}
