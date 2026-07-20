"use client";

import { useState } from "react";
import { getOrders, getOrder } from "@/lib/api";
import type { Order } from "@/lib/api";

export default function OrdersPage() {
  const [email, setEmail] = useState("");
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  const searchOrders = async () => {
    if (!email.trim()) return;
    setLoading(true);
    setSearched(true);
    try {
      const { orders } = await getOrders(email);
      setOrders(orders);
    } catch {
      setOrders([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-dark-100">📦 Order History</h1>
        <p className="text-gray-500 mt-1">Look up your orders by email</p>
      </div>

      <div className="flex gap-3">
        <input
          type="email"
          placeholder="Enter your email..."
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="input-field flex-1"
          onKeyDown={(e) => e.key === "Enter" && searchOrders()}
        />
        <button onClick={searchOrders} disabled={loading} className="btn-primary">
          {loading ? "Searching..." : "Search"}
        </button>
      </div>

      {searched && !loading && (
        <div className="space-y-3">
          {orders.length === 0 ? (
            <div className="text-center py-12 text-gray-400">
              <div className="text-4xl mb-3">🔍</div>
              <p>No orders found for this email</p>
            </div>
          ) : (
            orders.map((order) => (
              <div key={order.order_id} className="glass-card !p-5">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-bold text-dark-100">{order.order_id}</h3>
                  <span className={`badge ${
                    order.status === "delivered" ? "badge-success" :
                    order.status === "cancelled" ? "badge-error" :
                    order.status === "shipped" ? "badge-info" : "badge-warning"
                  }`}>{order.status}</span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-sm text-gray-600">
                  <p>Amount: <span className="font-medium">${order.order_amount.toFixed(2)}</span></p>
                  <p>Shipping: {order.shipping_country}</p>
                  {order.tracking_number && <p>Tracking: <code className="bg-gray-100 px-2 py-0.5 rounded text-xs">{order.tracking_number}</code></p>}
                  <p>Date: {new Date(order.order_timestamp).toLocaleDateString()}</p>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
