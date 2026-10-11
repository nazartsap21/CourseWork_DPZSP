"use client";

import { createContext, useCallback, useContext, useMemo, useState, useSyncExternalStore } from "react";

import { SwitchRestaurantDialog } from "@/components/cart/switch-restaurant-dialog";

import { useAuth } from "./auth";
import {
  addDish,
  type Cart,
  type CartDish,
  cartItemCount,
  cartSubtotal,
  type CartRestaurant,
  EMPTY_CART,
  getServerCart,
  readCart,
  setItemQuantity,
  subscribeCart,
  syncWithMenu,
  writeCart,
} from "./cart-store";

interface PendingAdd {
  restaurant: CartRestaurant;
  dish: CartDish;
}

interface CartContextValue {
  cart: Cart;
  itemCount: number;
  subtotal: number;
  /** Guests and customers can order; couriers and admins don't see cart controls. */
  canOrder: boolean;
  /** Adds one portion; asks first if the cart holds another restaurant's dishes. */
  add: (restaurant: CartRestaurant, dish: CartDish) => void;
  setQuantity: (dishId: number, quantity: number) => void;
  syncPrices: (dishes: Map<number, CartDish>) => void;
  clear: () => void;
  quantityOf: (dishId: number) => number;
}

const CartContext = createContext<CartContextValue | null>(null);

export function CartProvider({ children }: { children: React.ReactNode }) {
  const cart = useSyncExternalStore(subscribeCart, readCart, getServerCart);
  const { user } = useAuth();
  const [pending, setPending] = useState<PendingAdd | null>(null);

  const add = useCallback((restaurant: CartRestaurant, dish: CartDish) => {
    // Read the latest stored cart, not the render-time one, so fast double clicks both count.
    const current = readCart();
    if (current.restaurant && current.restaurant.id !== restaurant.id && current.items.length > 0) {
      setPending({ restaurant, dish });
      return;
    }
    writeCart(addDish(current, restaurant, dish));
  }, []);

  const setQuantity = useCallback((dishId: number, quantity: number) => {
    writeCart(setItemQuantity(readCart(), dishId, quantity));
  }, []);

  const syncPrices = useCallback((dishes: Map<number, CartDish>) => {
    const current = readCart();
    const synced = syncWithMenu(current, dishes);
    if (synced !== current) writeCart(synced);
  }, []);

  const clear = useCallback(() => writeCart(EMPTY_CART), []);

  const value = useMemo<CartContextValue>(() => {
    const quantities = new Map(cart.items.map((item) => [item.dish_id, item.quantity]));
    return {
      cart,
      itemCount: cartItemCount(cart),
      subtotal: cartSubtotal(cart),
      canOrder: !user || user.role === "customer",
      add,
      setQuantity,
      syncPrices,
      clear,
      quantityOf: (dishId) => quantities.get(dishId) ?? 0,
    };
  }, [cart, user, add, setQuantity, syncPrices, clear]);

  return (
    <CartContext.Provider value={value}>
      {children}
      <SwitchRestaurantDialog
        currentRestaurant={cart.restaurant?.name ?? ""}
        nextRestaurant={pending?.restaurant.name ?? ""}
        open={pending !== null}
        onCancel={() => setPending(null)}
        onConfirm={() => {
          if (pending) writeCart(addDish(EMPTY_CART, pending.restaurant, pending.dish));
          setPending(null);
        }}
      />
    </CartContext.Provider>
  );
}

export function useCart(): CartContextValue {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error("useCart must be used inside <CartProvider>");
  }
  return context;
}
