"""MOCK DATA LAYER - backend friend: replace each function body with real DB / API calls.
Keep the function names + return shapes and the frontend keeps working."""
import pandas as pd

def get_pincodes():                      # TODO: SELECT pincode, label FROM locations
    return ["202001 · Aligarh", "110001 · New Delhi", "226001 · Lucknow"]

def get_geo_trends(pin: str) -> pd.DataFrame:   # TODO: demographic/trend query by pincode
    d = {"202001 · Aligarh": {"Besan": 92, "Atta": 88, "Mustard Oil": 81, "Tea": 79, "Biscuits": 72, "Rice": 64},
         "110001 · New Delhi": {"Rice": 90, "Biscuits": 86, "Snacks": 84, "Tea": 77, "Atta": 70, "Besan": 55},
         "226001 · Lucknow": {"Atta": 89, "Tea": 85, "Rice": 80, "Mustard Oil": 74, "Besan": 70, "Snacks": 66}}[pin]
    return pd.DataFrame({"Item": d.keys(), "Demand score": d.values()}).set_index("Item")

SHOP_RATE = {"Kirana": 1800, "Bakery": 2200, "Pharmacy": 3500, "Stationery": 1500}
def capital_sync(sqft: int, shop_type: str) -> dict:   # TODO: real budget model
    total = sqft * SHOP_RATE[shop_type]
    return {"total": total, "stock": int(total * .6), "fixtures": int(total * .25), "buffer": int(total * .15)}

def get_catalog() -> pd.DataFrame:       # TODO: SELECT * FROM distributor_catalog
    rows = [("Aggarwal Traders", "Atta 10kg", "Staples", 395, 430), ("Aggarwal Traders", "Besan 1kg", "Staples", 78, 90),
            ("Sharma Agencies", "Mustard Oil 1L", "Oils", 128, 142), ("Sharma Agencies", "Basmati Rice 5kg", "Staples", 410, 455),
            ("Gupta Wholesale", "Tea 500g", "Beverages", 190, 215), ("Gupta Wholesale", "Biscuit Carton", "Snacks", 520, 580),
            ("Gupta Wholesale", "Cold Drink Crate", "Beverages", 310, 340), ("Dairy Fresh Co", "Milk Packs (12)", "Dairy", 650, 700)]
    return pd.DataFrame(rows, columns=["Distributor", "Product", "Category", "NewSto price", "Middleman price"])

def place_order(items: dict) -> str:     # TODO: INSERT INTO orders
    return "ORD-2026-0001"

def get_godown() -> pd.DataFrame:        # TODO: SELECT * FROM stock JOIN godown_rooms
    rows = [("Room A · Front", "Atta 10kg", 40, 120), ("Room A · Front", "Biscuit Carton", 12, 6),
            ("Room B · Back", "Besan 1kg", 55, 25), ("Room B · Back", "Mustard Oil 1L", 30, 90),
            ("Room C · Cold", "Milk Packs", 60, 3), ("Room C · Cold", "Paneer 200g", 18, 12)]
    df = pd.DataFrame(rows, columns=["Room", "Item", "Qty", "Days to expiry"])
    df["Status"] = df["Days to expiry"].apply(lambda d: "🔴 CRITICAL" if d <= 7 else "🟡 WARN" if d <= 30 else "🟢 OK")
    return df

def margin_price(cost: float, margin_pct: float) -> float:   # TODO: smarter pricing model
    return round(cost / (1 - margin_pct / 100), 2)


def get_pools() -> list:                 # TODO: SELECT * FROM pools WHERE distance_km <= 5
    import time
    h = 3600
    return [
        {"id": 1, "emoji": "🍚", "name": "Basmati Rice 500kg Bulk Pool", "area": "Sector 4", "km": 1.8, "unit": "kg", "target": 500, "current": 380, "base": 91, "disc": 18, "stores": 4, "closes_at": time.time() + 4.25 * h},
        {"id": 2, "emoji": "🫒", "name": "Cooking Oil 200L Pool", "area": "Civil Lines", "km": 2.6, "unit": "L", "target": 200, "current": 120, "base": 142, "disc": 12, "stores": 3, "closes_at": time.time() + 1.7 * h},
        {"id": 3, "emoji": "🌾", "name": "Atta 1000kg Bulk Pool", "area": "Marris Road", "km": 3.4, "unit": "kg", "target": 1000, "current": 640, "base": 39.5, "disc": 10, "stores": 6, "closes_at": time.time() + 7.5 * h},
        {"id": 4, "emoji": "🍵", "name": "Tea 100kg Pool", "area": "Sector 4", "km": 0.9, "unit": "kg", "target": 100, "current": 85, "base": 380, "disc": 15, "stores": 5, "closes_at": time.time() + 2.4 * h},
    ]


def get_products() -> list:              # TODO: SELECT * FROM distributor_products JOIN distributors
    rows = [("Atta 10kg", "Aggarwal Traders", "Staples", 395, 430, "🌾"), ("Besan 1kg", "Aggarwal Traders", "Staples", 78, 90, "🫘"),
            ("Basmati Rice 5kg", "Sharma Agencies", "Staples", 410, 455, "🍚"), ("Toor Dal 5kg", "Sharma Agencies", "Staples", 640, 700, "🫘"),
            ("Mustard Oil 1L", "Sharma Agencies", "Oils", 128, 142, "🫒"), ("Refined Oil 5L", "Gupta Wholesale", "Oils", 690, 760, "🛢️"),
            ("Tea 500g", "Gupta Wholesale", "Beverages", 190, 215, "🍵"), ("Cold Drink Crate", "Gupta Wholesale", "Beverages", 310, 340, "🥤"),
            ("Biscuit Carton", "Gupta Wholesale", "Snacks", 520, 580, "🍪"), ("Namkeen 10 pack", "Sharma Agencies", "Snacks", 360, 400, "🥨"),
            ("Milk Packs (12)", "Dairy Fresh Co", "Dairy", 650, 700, "🥛"), ("Detergent 5kg", "Aggarwal Traders", "Household", 420, 480, "🧴")]
    return [{"id": i + 1, "name": n, "dist": ds, "cat": c, "price": pr, "mrp": m, "em": e} for i, (n, ds, c, pr, m, e) in enumerate(rows)]
