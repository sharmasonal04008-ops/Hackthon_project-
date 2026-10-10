"""Pure-Python logic (no Streamlit imports) so your backend friend can reuse/test it."""
import re, datetime

# ---------------- Voice Ledger: English + Hinglish command parser ----------------
HN = {"ek": 1, "do": 2, "teen": 3, "char": 4, "chaar": 4, "paanch": 5, "panch": 5, "chhe": 6, "saat": 7, "aath": 8, "nau": 9,
      "das": 10, "barah": 12, "pandrah": 15, "bees": 20, "pachees": 25, "tees": 30, "chalis": 40, "pachas": 50, "saath": 60, "sau": 100,
      "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
      "twenty": 20, "fifty": 50, "hundred": 100, "aadha": .5, "half": .5, "dedh": 1.5}
UNITS = "kg|kgs|kilo|kilos|kilogram|packet|packets|pkt|pcs|piece|pieces|litre|liter|litres|ltr|dozen|bag|bags|carton|cartons"
SALE = "sold|sell|sale|becha|bech|beche|bika|bik"
BUY = "bought|buy|purchase|kharida|kharid|kharide|liya|aaya|restock|received"
STOP = (f"\\b({SALE}|{BUY}|{UNITS}|diya|di|kiya|kar|ka|ke|ki|ko|ne|maine|mene|of|at|per|each|rate|aaj|today|"
        "and|aur|the|a|an|to|for|ek|rs|rupees?|rupaye|me|mein|from|se|customer)\\b")
PRICE_RE = re.compile(r"(?:\b(?:rs|rupees?|rupaye|rupiye|inr)\s*(\d+(?:\.\d+)?))|(?:(\d+(?:\.\d+)?)\s*(?:rs|rupees?|rupaye|rupiye|inr)\b)"
                      r"|(?:\b(?:at|@|rate|each|per)\s+(?:[a-z]+\s+)?(\d+(?:\.\d+)?))")


def parse_command(text: str) -> dict:
    """'paanch kilo atta bech diya 40 rupaye' -> {act:'sale', qty:5, unit:'kilo', price:40, item:'atta'}"""
    s = " " + re.sub(r"[₹,]", " ", text.lower()) + " "
    s = re.sub(r"\b[a-z]+\b", lambda m: str(HN.get(m.group(0), m.group(0))), s)
    act = "sale" if re.search(rf"\b({SALE})\b", s) else "purchase" if re.search(rf"\b({BUY})\b", s) else None
    price = qty = None
    unit = ""
    m = PRICE_RE.search(s)
    if m:
        price = float(next(g for g in m.groups() if g))
        s = s[:m.start()] + " " + s[m.end():]
    m = re.search(rf"(\d+(?:\.\d+)?)\s*({UNITS})?\b", s)
    if m:
        qty, unit = float(m.group(1)), m.group(2) or ""
        s = s[:m.start()] + " " + s[m.end():]
    item = re.sub(STOP, " ", s)
    item = " ".join(re.sub(r"[^a-z\s]", " ", item).split())
    return {"act": act, "qty": qty, "unit": unit, "price": price, "item": item}


def apply_command(text: str, ledger: list, stock: dict):
    """Parses a command, updates the ledger list and stock dict IN PLACE. Returns (ok, message)."""
    r = parse_command(text)
    if not r["act"]:
        return False, "Say 'sold' or 'bought', e.g. sold 5 kg atta at 40 rupees"
    if not r["item"]:
        return False, "I couldn't catch the item name"
    qty = r["qty"] if r["qty"] is not None else 1.0
    price = r["price"]
    if price is None:
        last = next((e for e in ledger if e["key"] == r["item"]), None)
        if not last:
            return False, "Add a price, e.g. 'at 40 rupees'"
        price = last["price"]
    name = r["item"].title()
    match = next((k for k in stock if k.lower() == r["item"] or r["item"] in k.lower() or k.lower() in r["item"]), name)
    before = stock.get(match, 0.0)
    after = max(0.0, before + (-qty if r["act"] == "sale" else qty))
    warn = f" Only {before:g} in stock, set to 0." if r["act"] == "sale" and qty > before else ""
    stock[match] = after
    ledger.insert(0, {"time": datetime.datetime.now().strftime("%H:%M"), "type": r["act"], "item": match, "key": r["item"],
                      "qty": qty, "unit": r["unit"], "price": price, "total": qty * price, "stock_after": after})
    return True, f"{'Sale' if r['act'] == 'sale' else 'Purchase'} logged: {qty:g} {r['unit']} {match} = Rs {qty * price:,.0f}.{warn}"


def pnl(ledger: list) -> dict:
    sales = sum(e["total"] for e in ledger if e["type"] == "sale")
    buys = sum(e["total"] for e in ledger if e["type"] == "purchase")
    return {"sales": sales, "purchases": buys, "net": sales - buys}


# ---------------- Ambient Demand Engine ----------------
# (temp C, humidity %, rain probability %). Replace with a real weather API call later.
SCENARIOS = {
    "Monsoon incoming": [(28, 78, 20), (27, 86, 70), (26, 90, 85), (28, 82, 45), (30, 72, 10)],
    "Heatwave": [(38, 30, 0), (40, 28, 0), (41, 25, 0), (39, 30, 5), (37, 35, 10)],
    "Clear and mild": [(27, 48, 0), (28, 50, 5), (27, 52, 0), (26, 55, 10), (27, 50, 0)],
}
HUMID_ITEMS = ["atta", "besan", "rice", "sugar", "salt", "biscuit", "namkeen", "milk"]


def forecast(scenario: str) -> list:
    today = datetime.date.today()
    out = []
    for i, (t, h, r) in enumerate(SCENARIOS[scenario]):
        d = today + datetime.timedelta(days=i)
        out.append({"day": "Today" if i == 0 else d.strftime("%a"), "temp": t, "hum": h, "rain": r})
    return out


def analyze_weather(days: list) -> dict:
    """Returns {risk:0-100, alerts:[(level,title,body,[product names to restock])]}"""
    hum3 = max(d["hum"] for d in days[:3])
    rain3 = max(d["rain"] for d in days[:3])
    rain = max(d["rain"] for d in days)
    temp = max(d["temp"] for d in days)
    risk = int(max(0, min(98, max(hum3 - 45, 0) * 1.2 + rain3 * .25 + (25 if temp >= 38 else 0))))
    alerts = []
    if hum3 >= 75 or rain >= 60:
        alerts.append(("error", "Humidity and rain spoilage risk",
                       f"Humidity reaches {hum3}%. Atta, besan, rice, sugar, salt and biscuits absorb moisture. "
                       "Raise them off the floor, use airtight bins and sell older stock first.", []))
    rain_day = next((d for d in days if d["rain"] >= 60), None)
    if rain_day:
        alerts.append(("warning", f"Restock surge before {rain_day['day']}",
                       "Rain is likely. Tea, biscuits, besan and cooking oil sell faster on rainy days. "
                       "Order now so stock arrives before the weather shifts.", ["Tea", "Biscuit", "Besan", "Mustard"]))
    if temp >= 36:
        alerts.append(("warning", "Heat surge and dairy risk",
                       f"Temperatures reach {temp} C. Cold drinks and water will sell fast and milk spoils sooner. "
                       "Keep dairy in cold storage and restock drinks early.", ["Cold Drink", "Milk"]))
    if not alerts:
        alerts.append(("success", "No weather risks in the next 5 days", "Conditions are stable. Keep your normal restocking rhythm.", []))
    return {"risk": risk, "alerts": alerts, "at_risk": hum3 >= 75 or rain >= 60 or temp >= 36}


# ---------------- Micro-Syndicate pools ----------------
def pool_pct(p: dict) -> int:
    return min(100, round(p["current"] / p["target"] * 100))


def pool_price(p: dict, qty: float) -> tuple:
    std = qty * p["base"]
    syn = std * (1 - p["disc"] / 100)
    return std, syn, std - syn


def join_pool(p: dict, qty: float) -> bool:
    """Adds qty to the pool IN PLACE. Returns True if this join filled the pool."""
    p["current"] = min(p["target"], p["current"] + qty)
    p["stores"] += 1
    p["yours"] = p.get("yours", 0) + qty
    return p["current"] >= p["target"]
