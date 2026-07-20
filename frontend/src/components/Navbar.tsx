"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useCart } from "@/lib/cart";
import { getCategories } from "@/lib/api";

export default function Navbar() {
  const { itemCount, openCart } = useCart();
  const [categories, setCategories] = useState<string[]>([]);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    getCategories().then((r) => setCategories(r.categories)).catch(() => {});
    const onScroll = () => setScrolled(window.scrollY > 10);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <nav
      className={`sticky top-0 z-50 transition-all duration-300 ${
        scrolled ? "glass shadow-sm" : "bg-transparent"
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 group">
            <span className="text-2xl">🛍️</span>
            <div>
              <span className="font-bold text-xl text-dark-100 group-hover:text-brand-500 transition-colors">
                Urban Thread
              </span>
              <span className="text-[10px] block text-gray-400 -mt-1 font-medium">Co.</span>
            </div>
          </Link>

          {/* Categories */}
          <div className="hidden md:flex items-center gap-1">
            <Link
              href="/"
              className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-dark-100 rounded-lg hover:bg-gray-100 transition-all"
            >
              All
            </Link>
            {categories.slice(0, 5).map((cat) => (
              <Link
                key={cat}
                href={`/?category=${encodeURIComponent(cat)}`}
                className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-dark-100 rounded-lg hover:bg-gray-100 transition-all"
              >
                {cat}
              </Link>
            ))}
          </div>

          {/* Right actions */}
          <div className="flex items-center gap-3">
            <Link href="/chat" className="btn-secondary text-sm !px-4 !py-2">
              🤖 AI Assistant
            </Link>
            <Link href="/admin" className="btn-secondary text-sm !px-4 !py-2">
              ⚙️ Admin
            </Link>
            <button
              onClick={openCart}
              className="relative p-2.5 rounded-xl hover:bg-gray-100 transition-all group"
            >
              <svg className="w-6 h-6 text-gray-600 group-hover:text-brand-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 100 4 2 2 0 000-4z" />
              </svg>
              {itemCount > 0 && (
                <span className="absolute -top-1 -right-1 bg-brand-500 text-white text-xs font-bold
                               w-5 h-5 rounded-full flex items-center justify-center animate-scale-in">
                  {itemCount}
                </span>
              )}
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}
