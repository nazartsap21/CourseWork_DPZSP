import type { Cuisine, Dish } from "./catalog";

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
