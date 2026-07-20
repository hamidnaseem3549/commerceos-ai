"use client";

import { useState, useEffect } from "react";
import Image from "next/image";
import { getProducts, getCategories, Product } from "@/lib/api";
import { useCart } from "@/lib/cart";

const UNSPLASH_QUERIES: Record<string, string> = {
  "Apparel": "clothing-fashion",
  "Electronics": "electronics-gadgets",
  "Accessories": "accessories-fashion",
  "Home & Living": "home-decor",
  "Footwear": "shoes-footwear",
  "Sports & Fitness": "fitness-sports",
};

function getProductImage(product: Product, index: number): string {
  const query = UNSPLASH_QUERIES[product.category] || "product";
  const seed = product.product_id.replace("P", "");
  return `https://images.unsplash.com/photo-${1500000000 + parseInt(seed) * 100}?w=600&h=600&fit=crop&q=80`;
}

export default function ProductGrid() {
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [activeCat, setActiveCat] = useState("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const { addItem } = useCart();

  useEffect(() => {
    getCategories().then(({ categories }) => setCategories(categories)).catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    getProducts({ category: activeCat || undefined, search: search || undefined })
      .then((prods: any) => setProducts(Array.isArray(prods) ? prods : prods.products || []))
      .catch(() => setProducts([]))
      .finally(() => setLoading(false));
  }, [activeCat, search]);

  // Fallback product image colors
  const getColor = (i: number) => {
    const colors = ["from-brand-100 to-brand-200", "from-blue-100 to-blue-200",
                    "from-purple-100 to-purple-200", "from-green-100 to-green-200",
                    "from-yellow-100 to-yellow-200", "from-pink-100 to-pink-200"];
    return colors[i % colors.length];
  };

  return (
    <div className="space-y-6">
      {/* Search + Filter bar */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="flex gap-2 flex-wrap">
          <button
            onClick={() => setActiveCat("")}
            className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
              !activeCat ? "bg-dark-100 text-white shadow-lg" : "bg-white text-gray-600 hover:bg-gray-100"
            }`}
          >
            All
          </button>
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setActiveCat(activeCat === cat ? "" : cat)}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                activeCat === cat
                  ? "bg-dark-100 text-white shadow-lg"
                  : "bg-white text-gray-600 hover:bg-gray-100"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
        <div className="relative w-full sm:w-72">
          <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            placeholder="Search products..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="input-field !pl-10"
          />
        </div>
      </div>

      {/* Product Grid */}
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="glass-card overflow-hidden animate-pulse">
              <div className="aspect-square bg-gray-200" />
              <div className="p-4 space-y-2">
                <div className="h-4 bg-gray-200 rounded w-3/4" />
                <div className="h-3 bg-gray-200 rounded w-1/2" />
                <div className="h-6 bg-gray-200 rounded w-1/3" />
              </div>
            </div>
          ))}
        </div>
      ) : products.length === 0 ? (
        <div className="text-center py-20">
          <div className="text-6xl mb-4">🔍</div>
          <p className="text-xl text-gray-400">No products found</p>
          <button onClick={() => { setSearch(""); setActiveCat(""); }} className="btn-secondary mt-4">
            Clear filters
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {products.map((product, i) => (
            <div key={product.product_id} className="glass-card overflow-hidden group">
              {/* Image */}
              <div className="aspect-square relative overflow-hidden bg-gradient-to-br">
                <div className={`w-full h-full bg-gradient-to-br ${getColor(i)} flex items-center justify-center
                                group-hover:scale-105 transition-transform duration-500`}>
                  <span className="text-4xl font-black text-white/80 select-none">
                    {product.product_name.split(" ").map(w => w[0]).join("").slice(0, 2).toUpperCase()}
                  </span>
                </div>
                {/* Sale badge */}
                {product.is_on_sale && (
                  <span className="absolute top-3 left-3 bg-orange-500 text-white px-3 py-1 rounded-full text-xs font-bold shadow-lg animate-pulse-slow">
                    SALE
                  </span>
                )}
                {/* Out of stock overlay */}
                {product.stock_quantity === 0 && (
                  <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
                    <span className="text-white font-bold text-lg">Out of Stock</span>
                  </div>
                )}
              </div>

              {/* Info */}
              <div className="p-4 space-y-2">
                <span className="text-xs text-gray-400 font-medium uppercase tracking-wider">{product.category}</span>
                <h3 className="font-semibold text-dark-100 leading-tight group-hover:text-brand-500 transition-colors">
                  {product.product_name}
                </h3>
                <div className="flex items-center gap-2">
                  {product.is_on_sale && product.sale_price ? (
                    <>
                      <span className="text-lg font-bold text-brand-500">${product.sale_price.toFixed(2)}</span>
                      <span className="text-sm text-gray-400 line-through">${product.price.toFixed(2)}</span>
                    </>
                  ) : (
                    <span className="text-lg font-bold text-dark-100">${product.price.toFixed(2)}</span>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  {product.stock_quantity <= product.reorder_threshold && product.stock_quantity > 0 ? (
                    <span className="badge-warning text-xs">Only {product.stock_quantity} left</span>
                  ) : product.stock_quantity > 0 ? (
                    <span className="badge-success text-xs">In stock</span>
                  ) : null}
                </div>
                <button
                  onClick={() => addItem(product)}
                  disabled={product.stock_quantity === 0}
                  className="btn-primary w-full !py-2.5 !text-sm mt-2"
                >
                  Add to Cart
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
