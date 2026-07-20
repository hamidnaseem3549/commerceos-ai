"use client";

import { useState, useEffect } from "react";
import { getProducts, getCategories, Product } from "@/lib/api";
import { useCart } from "@/lib/cart";

const CATEGORY_IMAGES: Record<string, string[]> = {
  Apparel: [
    "photo-1556909114-f6e7ad7d3136",
    "photo-1556905055-8f358a7a47b2",
    "photo-1490114538077-0a7f8cb49891",
  ],
  Electronics: [
    "photo-1468495244123-6c6c332eeece",
    "photo-1523275335684-37898b6baf30",
    "photo-1505740420928-5e560c06d30e",
  ],
  Accessories: [
    "photo-1491637639811-60e2756cc1c7",
    "photo-1547996160-81dfa63595aa",
    "photo-1524592094714-0f0654e20314",
  ],
  "Home & Living": [
    "photo-1544457070-4cd773b4d71e",
    "photo-1567225591450-0e5ec7ba0d4f",
    "photo-1555041469-a586c61ea9bc",
  ],
  Footwear: [
    "photo-1542291026-7eec264c27ff",
    "photo-1608231387042-66d1773070a5",
    "photo-1491553895911-0055eca6402d",
  ],
  "Sports & Fitness": [
    "photo-1571019613454-1cb2f99b2d8b",
    "photo-1534258938425-1efa0faf2d60",
    "photo-1518611012118-696072aa579a",
  ],
};

const FALLBACK_COLORS = [
  "from-brand-100 to-brand-200", "from-blue-100 to-blue-200",
  "from-purple-100 to-purple-200", "from-green-100 to-green-200",
  "from-yellow-100 to-yellow-200", "from-pink-100 to-pink-200",
];

function getProductImage(product: Product): string {
  const images = CATEGORY_IMAGES[product.category] || CATEGORY_IMAGES.Apparel;
  const index = parseInt(product.product_id.replace("P", "")) % images.length;
  return `https://images.unsplash.com/${images[index]}?w=600&h=600&fit=crop&q=80`;
}

function ProductCard({ product, index, onAdd }: { product: Product; index: number; onAdd: (p: Product) => void }) {
  const [imgError, setImgError] = useState(false);
  const color = FALLBACK_COLORS[index % FALLBACK_COLORS.length];
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
