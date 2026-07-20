const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface FetcherOptions {
  method?: string;
  body?: unknown;
  params?: Record<string, string>;
}

async function fetcher<T>(endpoint: string, opts: FetcherOptions = {}): Promise<T> {
  const url = new URL(`${API_BASE}${endpoint}`);
  if (opts.params) Object.entries(opts.params).forEach(([k, v]) => url.searchParams.set(k, v));

  const res = await fetch(url.toString(), {
    method: opts.method || "GET",
    headers: { "Content-Type": "application/json" },
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `API error: ${res.status}`);
  }

  return res.json();
}

// ── Products ──
export interface Product {
  product_id: string;
  product_name: string;
  category: string;
  price: number;
  stock_quantity: number;
  reorder_threshold: number;
  image_url: string;
  is_on_sale: boolean;
  sale_price: number | null;
}

export const getProducts = (params?: { category?: string; search?: string }) =>
  fetcher<{ products: Product[]; count: number }>("/api/products", { params: params as Record<string, string> })
    .then(r => r.products);

export const getProduct = (id: string) =>
  fetcher<Product>(`/api/products/${id}`);

export const getCategories = () =>
  fetcher<{ categories: string[] }>("/api/products/categories");

export const getLowStockProducts = () =>
  fetcher<{ products: Product[] }>("/api/products/low-stock");

// ── Orders ──
export interface Order {
  order_id: string;
  customer_name: string;
  customer_email: string;
  order_amount: number;
  status: string;
  tracking_number?: string;
  shipping_country: string;
  order_timestamp: string;
}

export const placeOrder = (data: {
  customer_name: string;
  customer_email: string;
  shipping_country: string;
  product_id: string;
  quantity: number;
}) => fetcher<{ order_id: string; product_name: string; total: number }>("/api/orders", { method: "POST", body: data });

export const getOrders = (email: string) =>
  fetcher<{ orders: Order[] }>(`/api/orders?email=${encodeURIComponent(email)}`);

export const getOrder = (id: string) =>
  fetcher<Order>(`/api/orders/${id}`);

// ── Chat ──
export interface ChatResult {
  answer: string;
  agent: string;
  ops_alert?: string;
}

export const chat = (query: string, threadId = "default") =>
  fetcher<ChatResult>("/api/chat", {
    method: "POST",
    body: { query, thread_id: threadId },
  });

// ── Admin ──
export interface AdminStats {
  total_orders: number;
  pending_orders: number;
  low_stock_items: number;
  fraud_alerts: number;
  total_customers: number;
  total_products: number;
}

export const getAdminStats = () => fetcher<AdminStats>("/api/admin/stats");
export const getAdminAlerts = (limit = 20) =>
  fetcher<{ alerts: any[] }>(`/api/admin/alerts?limit=${limit}`);
export const getAdminLogs = (limit = 50) =>
  fetcher<{ logs: any[] }>(`/api/admin/logs?limit=${limit}`);
export const getAgents = () =>
  fetcher<{ agents: string[] }>("/api/admin/agents");
export const runFraudSweep = () =>
  fetcher<{ flagged: number }>("/api/admin/actions/fraud-sweep", { method: "POST" });
export const runPricingAnalysis = () =>
  fetcher<{ sales_applied: number }>("/api/admin/actions/pricing-analysis", { method: "POST" });
