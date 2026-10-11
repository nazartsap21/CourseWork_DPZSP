// Client-side cart: persisted in localStorage, one restaurant per cart.
// Prices here are display snapshots only; the backend recalculates every
// amount at quote and checkout time, so a tampered cart can't change a price.

export interface CartRestaurant {
  id: number;
  name: string;
  min_order_amount: number;
}

export interface CartItem {
  dish_id: number;
  name: string;
  price: number;
  quantity: number;
}

export interface Cart {
  restaurant: CartRestaurant | null;
  items: CartItem[];
}

export interface CartDish {
  id: number;
  name: string;
  price: number;
}

export const MAX_ITEM_QUANTITY = 20;
export const EMPTY_CART: Cart = { restaurant: null, items: [] };

const STORAGE_KEY = "forkful.cart";
const CHANGE_EVENT = "forkful:cart-change";

// ---- pure updates (no storage access, easy to reason about) ----

export function addDish(cart: Cart, restaurant: CartRestaurant, dish: CartDish): Cart {
  const base = cart.restaurant?.id === restaurant.id ? cart : { restaurant, items: [] };
  const existing = base.items.find((item) => item.dish_id === dish.id);
  const items = existing
    ? base.items.map((item) =>
        item.dish_id === dish.id ? { ...item, quantity: Math.min(item.quantity + 1, MAX_ITEM_QUANTITY) } : item,
      )
    : [...base.items, { dish_id: dish.id, name: dish.name, price: dish.price, quantity: 1 }];
  return { restaurant, items };
}

export function setItemQuantity(cart: Cart, dishId: number, quantity: number): Cart {
  const clamped = Math.min(Math.max(Math.trunc(quantity), 0), MAX_ITEM_QUANTITY);
  const items =
    clamped === 0
      ? cart.items.filter((item) => item.dish_id !== dishId)
      : cart.items.map((item) => (item.dish_id === dishId ? { ...item, quantity: clamped } : item));
  return items.length === 0 ? EMPTY_CART : { ...cart, items };
}

/** Applies current menu prices/names to the snapshots; returns the same object if nothing changed. */
export function syncWithMenu(cart: Cart, dishes: Map<number, CartDish>): Cart {
  let changed = false;
  const items = cart.items.map((item) => {
    const dish = dishes.get(item.dish_id);
    if (!dish || (dish.price === item.price && dish.name === item.name)) return item;
    changed = true;
    return { ...item, price: dish.price, name: dish.name };
  });
  return changed ? { ...cart, items } : cart;
}

export function cartItemCount(cart: Cart): number {
  return cart.items.reduce((sum, item) => sum + item.quantity, 0);
}

export function cartSubtotal(cart: Cart): number {
  return cart.items.reduce((sum, item) => sum + item.price * item.quantity, 0);
}

// ---- persistence ----

function isCart(value: unknown): value is Cart {
  if (typeof value !== "object" || value === null) return false;
  const { restaurant, items } = value as Partial<Cart>;
  const restaurantOk =
    restaurant === null ||
    (typeof restaurant === "object" && typeof restaurant?.id === "number" && typeof restaurant.name === "string");
  return (
    restaurantOk &&
    Array.isArray(items) &&
    items.every(
      (item) =>
        typeof item?.dish_id === "number" &&
        typeof item.name === "string" &&
        typeof item.price === "number" &&
        Number.isInteger(item.quantity) &&
        item.quantity > 0,
    )
  );
}

// useSyncExternalStore needs a stable snapshot: re-parse only when the raw string changes.
let cachedRaw: string | null = null;
let cachedCart: Cart = EMPTY_CART;

export function readCart(): Cart {
  let raw: string | null = null;
  try {
    raw = window.localStorage.getItem(STORAGE_KEY);
  } catch {
    return EMPTY_CART;
  }
  if (raw === cachedRaw) return cachedCart;
  cachedRaw = raw;
  try {
    const parsed: unknown = raw ? JSON.parse(raw) : null;
    cachedCart = isCart(parsed) ? parsed : EMPTY_CART;
  } catch {
    cachedCart = EMPTY_CART;
  }
  return cachedCart;
}

export function writeCart(cart: Cart): void {
  try {
    if (cart.items.length === 0) {
      window.localStorage.removeItem(STORAGE_KEY);
    } else {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(cart));
    }
  } finally {
    window.dispatchEvent(new Event(CHANGE_EVENT));
  }
}

/** Fires on changes in this tab and in other tabs (the `storage` event). */
export function subscribeCart(onChange: () => void): () => void {
  window.addEventListener(CHANGE_EVENT, onChange);
  window.addEventListener("storage", onChange);
  return () => {
    window.removeEventListener(CHANGE_EVENT, onChange);
    window.removeEventListener("storage", onChange);
  };
}

export const getServerCart = (): Cart => EMPTY_CART;
