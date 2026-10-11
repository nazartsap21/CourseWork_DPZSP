// Money fields are integer kopiyky, as returned by the API.

export interface Cuisine {
  id: number;
  name: string;
}

export interface CuisineWithCount extends Cuisine {
  restaurant_count: number;
}

export type PriceLevel = 1 | 2 | 3;

export interface RestaurantSummary {
  id: number;
  name: string;
  description: string;
  address: string;
  lat: number;
  lng: number;
  image_url: string | null;
  cuisines: Cuisine[];
  rating: number | null;
  review_count: number;
  price_level: PriceLevel | null;
  delivery_minutes_min: number;
  delivery_minutes_max: number;
  avg_prep_minutes: number;
  min_order_amount: number;
}

export interface RestaurantDetails extends RestaurantSummary {
  /** Review count per star value; keys are "1".."5". */
  rating_breakdown: Record<string, number>;
}

export interface Dish {
  id: number;
  restaurant_id: number;
  name: string;
  description: string;
  price: number;
  category: string;
  is_available: boolean;
  image_url: string | null;
}

export interface MenuSection {
  category: string;
  dishes: Dish[];
}

export interface Menu {
  restaurant_id: number;
  sections: MenuSection[];
}

export type RestaurantSort = "rating" | "delivery_time" | "price";
