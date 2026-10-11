"use client";

import { useEffect, useRef } from "react";

/** Native <dialog>: gives focus trapping, Escape to close and a backdrop for free. */
export function SwitchRestaurantDialog({
  open,
  currentRestaurant,
  nextRestaurant,
  onCancel,
  onConfirm,
}: {
  open: boolean;
  currentRestaurant: string;
  nextRestaurant: string;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);

  return (
    <dialog
      ref={ref}
      onCancel={(event) => {
        event.preventDefault();
        onCancel();
      }}
      onClick={(event) => {
        // A click on the backdrop lands on the <dialog> element itself.
        if (event.target === event.currentTarget) onCancel();
      }}
      aria-labelledby="switch-restaurant-title"
      className="m-auto w-[min(26rem,calc(100%-2rem))] rounded-2xl border border-line bg-card p-0 text-ink backdrop:bg-ink/40"
    >
      <div className="p-6">
        <h2 id="switch-restaurant-title" className="font-serif text-2xl">
          Start a new order?
        </h2>
        <p className="mt-3 text-sm leading-relaxed text-muted-ink">
          Your cart has dishes from <span className="font-medium text-ink">{currentRestaurant}</span>. An order comes
          from one restaurant, so adding a dish from <span className="font-medium text-ink">{nextRestaurant}</span>{" "}
          will empty the cart.
        </p>
        <div className="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <button
            type="button"
            onClick={onCancel}
            className="rounded-full border border-line px-4 py-2 text-sm font-medium text-ink hover:bg-surface"
          >
            Keep current cart
          </button>
          <button
            type="button"
            onClick={onConfirm}
            className="rounded-full bg-accent px-4 py-2 text-sm font-semibold text-white hover:bg-accent-strong"
          >
            Start new order
          </button>
        </div>
      </div>
    </dialog>
  );
}
