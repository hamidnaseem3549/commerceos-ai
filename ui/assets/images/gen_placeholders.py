"""Generate simple SVG placeholder images for products."""
import os

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

PRODUCT_PALETTE = {
    "P1001": ("Classic Cotton T-Shirt - Black", "#1a1a2e"),
    "P1002": ("Classic Cotton T-Shirt - White", "#f0f0f0"),
    "P1003": ("Wireless Bluetooth Headphones", "#0f3460"),
    "P1004": ("Leather Weekend Duffle Bag", "#c38d9e"),
    "P1005": ("Stainless Steel Water Bottle", "#41b3a3"),
    "P1006": ("Organic Green Tea Set", "#85cdca"),
    "P1007": ("Wool Blend Scarf - Charcoal", "#636e72"),
    "P1008": ("Running Shoes - Men's", "#e94560"),
    "P1009": ("Smart Watch Series 3", "#16213e"),
    "P1010": ("Canvas Backpack - Olive", "#8e44ad"),
    "P1011": ("Scented Soy Candle Set", "#e8a87c"),
    "P1012": ("Yoga Mat Premium", "#2ecc71"),
    "P1013": ("Denim Jacket - Classic Fit", "#3498db"),
    "P1014": ("Wireless Charging Pad", "#1a1a2e"),
    "P1015": ("Leather Belt - Brown", "#e27d60"),
    "P1016": ("Sunglasses - Aviator", "#2c3e50"),
    "P1017": ("Cashmere Beanie", "#9b59b6"),
    "P1018": ("Portable Bluetooth Speaker", "#e67e22"),
    "P1019": ("Laptop Sleeve - 13 inch", "#34495e"),
    "P1020": ("Essentials Hoodie - Grey", "#95a5a6"),
}


def generate_placeholder(product_id: str) -> str:
    name, color = PRODUCT_PALETTE.get(product_id, ("Item", "#636e72"))
    initials = "".join(w[0] for w in name.split()[:2]).upper()
    r_val = int(color[1:3], 16)
    g_val = int(color[3:5], 16)
    b_val = int(color[5:7], 16)
    text_color = "#ffffff" if (r_val + g_val + b_val) / 3 < 128 else "#1a1a2e"

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300" viewBox="0 0 400 300">
  <rect width="400" height="300" fill="{color}" rx="12"/>
  <text x="200" y="140" text-anchor="middle" fill="{text_color}" font-size="64" font-weight="700" font-family="Arial">{initials}</text>
  <text x="200" y="180" text-anchor="middle" fill="{text_color}" font-size="16" opacity="0.8" font-family="Arial">{name}</text>
</svg>"""


def generate_all():
    for pid in PRODUCT_PALETTE:
        svg = generate_placeholder(pid)
        filepath = os.path.join(OUTPUT_DIR, f"product_{pid.lower()}.svg")
        with open(filepath, "w") as f:
            f.write(svg)
        print(f"Generated: {filepath}")


if __name__ == "__main__":
    generate_all()
