"""Generate clean, professional SVG product images with category-based icons."""
import os, sys

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "public", "images")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Each product: (name, color, icon-emoji)
PRODUCTS = [
    ("P1001", "Classic Cotton T-Shirt - Black", "#2d2d2d", "👕"),
    ("P1002", "Classic Cotton T-Shirt - White", "#e8e8e8", "👕"),
    ("P1003", "Wireless Bluetooth Headphones", "#1a237e", "🎧"),
    ("P1004", "Leather Weekend Duffle Bag", "#8d6e63", "👜"),
    ("P1005", "Stainless Steel Water Bottle", "#00acc1", "🧴"),
    ("P1006", "Organic Green Tea Set", "#2e7d32", "🍵"),
    ("P1007", "Wool Blend Scarf - Charcoal", "#546e7a", "🧣"),
    ("P1008", "Running Shoes - Men's", "#c62828", "👟"),
    ("P1009", "Smart Watch Series 3", "#283593", "⌚"),
    ("P1010", "Canvas Backpack - Olive", "#558b2f", "🎒"),
    ("P1011", "Scented Soy Candle Set", "#f57f17", "🕯️"),
    ("P1012", "Yoga Mat Premium", "#00695c", "🧘"),
    ("P1013", "Denim Jacket - Classic Fit", "#1565c0", "🧥"),
    ("P1014", "Wireless Charging Pad", "#37474f", "📱"),
    ("P1015", "Leather Belt - Brown", "#795548", "🔗"),
    ("P1016", "Sunglasses - Aviator", "#263238", "🕶️"),
    ("P1017", "Cashmere Beanie", "#6a1b9a", "🧢"),
    ("P1018", "Portable Bluetooth Speaker", "#e65100", "🔊"),
    ("P1019", "Laptop Sleeve - 13 inch", "#455a64", "💻"),
    ("P1020", "Essentials Hoodie - Grey", "#78909c", "👚"),
]


def make_svg(pid, name, color, icon):
    """Generate a clean product card SVG with icon."""
    # Determine text color based on background brightness
    r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
    text_color = "#ffffff" if (r * 0.299 + g * 0.587 + b * 0.114) < 140 else "#333333"
    initials = "".join(w[0] for w in name.split()[:2]).upper()

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="600" height="600" viewBox="0 0 600 600">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:{color};stop-opacity:1" />
      <stop offset="100%" style="stop-color:{color}dd;stop-opacity:1" />
    </linearGradient>
    <linearGradient id="shine" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#ffffff;stop-opacity:0.1" />
      <stop offset="100%" style="stop-color:#ffffff;stop-opacity:0" />
    </linearGradient>
  </defs>
  <rect width="600" height="600" rx="0" fill="url(#bg)"/>
  <rect width="600" height="600" rx="0" fill="url(#shine)"/>
  <text x="300" y="260" text-anchor="middle" font-size="120" fill="{text_color}" opacity="0.95">{icon}</text>
  <text x="300" y="380" text-anchor="middle" font-size="48" font-weight="700" font-family="Inter, Arial, sans-serif" fill="{text_color}" opacity="0.85">{initials}</text>
  <text x="300" y="420" text-anchor="middle" font-size="18" font-weight="400" font-family="Inter, Arial, sans-serif" fill="{text_color}" opacity="0.6">{name}</text>
  <rect x="0" y="0" width="600" height="600" rx="0" fill="none" stroke="#ffffff" stroke-opacity="0.05" stroke-width="2"/>
</svg>'''


for pid, name, color, icon in PRODUCTS:
    svg = make_svg(pid, name, color, icon)
    filepath = os.path.join(OUTPUT_DIR, f"{pid.lower()}.svg")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"  OK {pid} - {name}".encode("utf-8", errors="replace").decode("utf-8"))
    sys.stdout.flush()

print(f"\nDONE: Generated {len(PRODUCTS)} product images in {OUTPUT_DIR}")
