"use client";

import { CartProvider } from "@/lib/cart";
import ProductGrid from "@/components/ProductGrid";

export default function HomePage() {
  return (
    <CartProvider>
      <div className="space-y-8">
        {/* Hero */}
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-dark-100 via-dark-200 to-brand-700 p-8 sm:p-12">
          <div className="relative z-10 max-w-2xl">
            <span className="badge-info !bg-white/20 !text-white text-xs mb-4 inline-block">Powered by CommerceOS AI</span>
            <h1 className="text-4xl sm:text-5xl font-bold text-white leading-tight mb-4">
              Style Meets{" "}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand-300 to-yellow-300">
                Intelligence
              </span>
            </h1>
            <p className="text-gray-300 text-lg mb-6 max-w-lg">
              Five AI agents working together to give you the best shopping experience —
              from support to fraud protection to dynamic pricing.
            </p>
            <div className="flex gap-3 flex-wrap">
              <a href="#products" className="btn-primary !bg-white !text-dark-100 hover:!bg-gray-100">
                Shop Now
              </a>
              <a href="/chat" className="px-6 py-3 rounded-xl bg-white/10 text-white font-medium
                                          hover:bg-white/20 transition-all backdrop-blur-sm">
                🤖 Ask AI Assistant
              </a>
            </div>
          </div>
          {/* Decorative elements */}
          <div className="absolute -top-20 -right-20 w-64 h-64 bg-brand-500/20 rounded-full blur-3xl" />
          <div className="absolute -bottom-10 -left-10 w-48 h-48 bg-yellow-400/10 rounded-full blur-3xl" />
        </div>

        {/* Product Grid */}
        <div id="products">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-dark-100">Shop Our Collection</h2>
            <span className="text-sm text-gray-400">AI-powered recommendations</span>
          </div>
          <ProductGrid />
        </div>
      </div>
    </CartProvider>
  );
}
