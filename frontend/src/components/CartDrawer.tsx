"use client";

import { useState } from "react";
import { useCart } from "@/lib/cart";
import { placeOrder } from "@/lib/api";
import { clsx } from "clsx";

export default function CartDrawer() {
  const { items, isOpen, closeCart, total, itemCount, updateQuantity, removeItem, clearCart } = useCart();
  const [checkoutOpen, setCheckoutOpen] = useState(false);
  const [form, setForm] = useState({ name: "", email: "", country: "" });
  const [placing, setPlacing] = useState(false);
  const [orderResult, setOrderResult] = useState<{ order_id: string; product_name: string; total: number } | null>(null);

  const handlePlaceOrder = async () => {
    if (!form.name || !form.email || !form.country || !items.length) return;
    setPlacing(true);
    try {
      const first = items[0];
      const result = await placeOrder({
        customer_name: form.name,
        customer_email: form.email,
        shipping_country: form.country,
        product_id: first.product.product_id,
        quantity: first.quantity,
      });
      setOrderResult(result);
      clearCart();
    } catch (e: any) {
      alert(e.message);
    } finally {
      setPlacing(false);
    }
  };

  return (
    <>
      {/* Overlay */}
      {isOpen && (
        <div className="fixed inset-0 bg-black/40 z-40" onClick={closeCart} />
      )}

      {/* Drawer */}
      <div
        className={clsx(
          "fixed top-0 right-0 h-full w-full max-w-md bg-white z-50 shadow-2xl transition-transform duration-300",
          isOpen ? "translate-x-0" : "translate-x-full"
        )}
      >
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b">
            <h2 className="text-lg font-bold text-dark-100">🛒 Cart ({itemCount})</h2>
            <button onClick={closeCart} className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Items */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {orderResult ? (
              <div className="text-center py-12 animate-fade-in">
                <div className="text-4xl mb-4">🎉</div>
                <h3 className="text-xl font-bold text-dark-100 mb-2">Order Placed!</h3>
                <p className="text-gray-600 mb-1">Order {orderResult.order_id}</p>
                <p className="text-gray-500 text-sm">Thank you, {form.name}!</p>
                <button
                  onClick={() => { setOrderResult(null); setCheckoutOpen(false); }}
                  className="btn-primary mt-6"
                >
                  Continue Shopping
                </button>
              </div>
            ) : items.length === 0 ? (
              <div className="text-center py-12 text-gray-400">
                <div className="text-5xl mb-4">🛍️</div>
                <p>Your cart is empty</p>
                <button onClick={closeCart} className="btn-secondary mt-4">
                  Browse Products
                </button>
              </div>
            ) : (
              items.map(({ product, quantity }) => (
                <div key={product.product_id} className="flex gap-4 glass-card !p-4">
                  <div className="w-16 h-16 rounded-xl bg-gradient-to-br from-brand-100 to-brand-200 flex items-center justify-center text-lg font-bold text-brand-600 shrink-0">
                    {product.product_name.split(" ").map(w => w[0]).join("").slice(0, 2).toUpperCase()}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-dark-100 truncate">{product.product_name}</p>
                    <p className="text-sm text-gray-500">${product.price.toFixed(2)}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <button onClick={() => updateQuantity(product.product_id, quantity - 1)}
                              className="w-7 h-7 rounded-full bg-gray-100 flex items-center justify-center text-sm hover:bg-gray-200">−</button>
                      <span className="text-sm font-medium w-6 text-center">{quantity}</span>
                      <button onClick={() => updateQuantity(product.product_id, quantity + 1)}
                              className="w-7 h-7 rounded-full bg-gray-100 flex items-center justify-center text-sm hover:bg-gray-200">+</button>
                      <button onClick={() => removeItem(product.product_id)}
                              className="ml-auto text-red-400 hover:text-red-600 text-sm">Remove</button>
                    </div>
                  </div>
                </div>
              ))
            )}

            {/* Checkout form */}
            {items.length > 0 && !orderResult && (
              <div className="border-t pt-4 mt-4">
                {!checkoutOpen ? (
                  <button onClick={() => setCheckoutOpen(true)} className="btn-primary w-full">
                    Checkout — ${total.toFixed(2)}
                  </button>
                ) : (
                  <div className="space-y-3 animate-fade-in">
                    <p className="font-semibold text-dark-100">Shipping Details</p>
                    <input className="input-field" placeholder="Full Name" value={form.name}
                           onChange={(e) => setForm({ ...form, name: e.target.value })} />
                    <input className="input-field" type="email" placeholder="Email" value={form.email}
                           onChange={(e) => setForm({ ...form, email: e.target.value })} />
                    <input className="input-field" placeholder="Country" value={form.country}
                           onChange={(e) => setForm({ ...form, country: e.target.value })} />
                    <div className="flex gap-2">
                      <button onClick={() => setCheckoutOpen(false)} className="btn-secondary flex-1">Back</button>
                      <button onClick={handlePlaceOrder} disabled={placing} className="btn-primary flex-1">
                        {placing ? "Placing..." : `Pay $${total.toFixed(2)}`}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
