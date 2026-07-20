"use client";

import { useState, useEffect } from "react";
import { getProducts, getCategories, Product } from "@/lib/api";
import { useCart } from "@/lib/cart";

const PRODUCT_IMAGES: Record<string, string> = {
  P1001: "photo-1603252109303-2751441dd157",  // Classic Cotton T-Shirt - Black
  P1002: "photo-1521572163474-6864f9cf17ab",  // Classic Cotton T-Shirt - White
  P1003: "photo-1505740420928-5e560c06d30e",  // Wireless Bluetooth Headphones
  P1004: "photo-1491637639811-60e2756cc1c7",  // Leather Weekend Duffle Bag
  P1005: "photo-1602143407151-7111542de6e8",  // Stainless Steel Water Bottle
  P1006: "photo-1556679343-c7306c1976bc",  // Organic Green Tea Set
  P1007: "photo-1520903920243-00d872a2d2c2",  // Wool Blend Scarf - Charcoal
  P1008: "photo-1542291026-7eec264c27ff",  // Running Shoes - Men's
  P1009: "photo-1608231387042-66d1773070a5",  // Smart Watch
  P1010: "photo-1622560480605-d83c853bc5c3",  // Canvas Backpack - Olive
  P1011: "photo-1607301405390-d831c242f59d",  // Scented Soy Candle Set
  P1012: "photo-1571019613454-1cb2f99b2d8b",  // Yoga Mat Premium
  P1013: "photo-1551028719-00167b16eac5",  // Denim Jacket - Classic Fit
  P1014: "photo-1583394293214-28ded15ee548",  // Wireless Charging Pad
  P1015: "photo-1524592094714-0f0654e20314",  // Sunglasses - Aviator
  P1016: "photo-1523275335684-37898b6baf30",  // Cashmere Beanie
  P1017: "photo-1608043152269-423dbba4e7e1",  // Portable Bluetooth Speaker
  P1018: "photo-1620799140408-edc6dcb6d1ef",  // Laptop Sleeve 13 inch
  P1019: "photo-1593030761757-71fae45fa0e7",  // Essentials Hoodie - Grey
  P1020: "photo-1553062407-98eeb64c6a62",  // Leather Belt - Brown
};

const PRODUCT_COLORS: Record<string, string> = {
  P1001: "from-gray-800 to-gray-900", P1002: "from-gray-100 to-gray-200",
  P1003: "from-indigo-500 to-indigo-700", P1004: "from-amber-700 to-amber-900",
  P1005: "from-cyan-400 to-cyan-600", P1006: "from-emerald-400 to-emerald-600",
  P1007: "from-gray-500 to-gray-700", P1008: "from-red-500 to-red-700",
  P1009: "from-purple-500 to-purple-700", P1010: "from-green-700 to-green-900",
  P1011: "from-yellow-400 to-yellow-600", P1012: "from-teal-400 to-teal-600",
  P1013: "from-blue-600 to-blue-800", P1014: "from-gray-700 to-gray-900",
  P1015: "from-orange-400 to-orange-600", P1016: "from-violet-500 to-violet-700",
  P1017: "from-pink-500 to-pink-700", P1018: "from-sky-500 to-sky-700",
  P1019: "from-stone-400 to-stone-600", P1020: "from-amber-600 to-amber-800",
};

const FALLBACK_COLORS = [
  "from-brand-100 to-brand-200", "from-blue-100 to-blue-200",
  "from-purple-100 to-purple-200", "from-green-100 to-green-200",
  "from-yellow-100 to-yellow-200", "from-pink-100 to-pink-200",
];

function getProductImage(product: Product): string {
  const photoId = PRODUCT_IMAGES[product.product_id];
  if (photoId) return `https://images.unsplash.com/${photoId}?w=600&h=600&fit=crop&q=80`;
  return `https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600&h=600&fit=crop&q=80`;
}

function getColor(product: Product, index: number): string {
  return PRODUCT_COLORS[product.product_id] || FALLBACK_COLORS[index % FALLBACK_COLORS.length];
}

function ProductCard({ product, index, onAdd }: { product: Product; index: number; onAdd: (p: Product) => void }) {
  const [imgError, setImgError] = useState(false);
  const color = getColor(product, index);
  const initials = product.product_name.split(" ").map((w) => w[0]).join("").slice(0, 2).toUpperCase();

  return (
    <div className="glass-card overflow-hidden group">
      {/* Image */}
      <div className="aspect-square relative overflow-hidden bg-gray-100">
        {!imgError ? (
          <img
            src={getProductImage(product)}
            alt={product.product_name}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
            loading="lazy"
            onError={() => setImgError(true)}
          />
        ) : (
          <div className={`w-full h-full bg-gradient-to-br ${color} flex items-center justify-center`}>
            <span className="text-4xl font-black text-white/80 select-none">{initials}</span>
          </div>
        )}
        {product.is_on_sale && (
          <span className="absolute top-3 left-3 bg-orange-500 text-white px-3 py-1 rounded-full text-xs font-bold shadow-lg animate-pulse-slow">
            SALE
          </span>
        )}
        {product.stock_quantity === 0 && (
          <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
            <span className="text-white font-bold text-lg">Out of Stock</span>
          </div>
        )}
      </div>

      {/* Info */}
      <div className="p-4 space-y-2">
        <span className="text-xs text-gray-400 font-medium uppercase tracking-wider">{product.category}</span>
        <h3 className="font-semibold text-dark-100 leading-tight group-hover:text-brand-500 transition-colors">{product.product_name}</h3>
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
        <button onClick={() => onAdd(product)} disabled={product.stock_quantity === 0}
          className="btn-primary w-full !py-2.5 !text-sm mt-2">Add to Cart</button>
      </div>
    </div>
  );
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
    const params: Record<string, string> = {};
    if (activeCat) params.category = activeCat;
    if (search) params.search = search;
    getProducts(params)
      .then((prods) => setProducts(Array.isArray(prods) ? prods : []))
      .catch(() => setProducts([]))
      .finally(() => setLoading(false));
  }, [activeCat, search]);

  return (
    <div className="space-y-6">
      {/* Search + Filter bar */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="flex gap-2 flex-wrap">
          <button onClick={() => setActiveCat("")}
            className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${!activeCat ? "bg-dark-100 text-white shadow-lg" : "bg-white text-gray-600 hover:bg-gray-100"}`}>
            All
          </button>
          {categories.map((cat) => (
            <button key={cat} onClick={() => setActiveCat(activeCat === cat ? "" : cat)}
              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${activeCat === cat ? "bg-dark-100 text-white shadow-lg" : "bg-white text-gray-600 hover:bg-gray-100"}`}>
              {cat}
            </button>
          ))}
        </div>
        <div className="relative w-full sm:w-72">
          <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input type="text" placeholder="Search products..." value={search}
            onChange={(e) => setSearch(e.target.value)} className="input-field !pl-10" />
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
          <button onClick={() => { setSearch(""); setActiveCat(""); }} className="btn-secondary mt-4">Clear filters</button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {products.map((product, i) => (
            <ProductCard key={product.product_id} product={product} index={i} onAdd={addItem} />
          ))}
        </div>
      )}
    </div>
  );
}
