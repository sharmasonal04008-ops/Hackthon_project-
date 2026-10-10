"""Parcha-Scan: reads a photo of a handwritten parchi / wholesaler invoice / distributor challan
and returns structured line items (name, qty, unit, unit cost, batch, expiry).
Uses Gemini (REST, standard library only) with a JSON response schema.
Set GEMINI_API_KEY to enable real scanning. Without a key it returns a clearly-labelled DEMO result,
so the website never breaks. Optional: GEMINI_MODEL (default gemini-1.5-flash; falls back to newer Flash models)."""
import base64, json, os, re, urllib.error, urllib.request

MODELS = [m for m in (os.environ.get("GEMINI_MODEL"), "gemini-1.5-flash", "gemini-2.0-flash", "gemini-2.5-flash") if m]
MAX_B64 = 6_000_000            # ~4.5 MB image

PROMPT = """You read photos of Indian kirana wholesale documents: handwritten vendor parchis (slips), printed wholesaler
invoices and beat-distributor challans. Text may be Hindi (Devanagari or romanised), English or mixed, in cursive.
Extract every purchased line item. Rules:
- name: product name in simple English (transliterate Hindi, e.g. "आटा" -> "Atta"), include pack size if written (e.g. "Atta 10kg").
- qty: number of billed units (number). unit: the unit exactly as billed, lower-case, e.g. bori, peti, katta, carton, kg, packet, pcs, litre, dozen.
- unit_cost: wholesale price in rupees per ONE billed unit (number). If only a line total is written, divide by qty.
- batch: batch number string or "". expiry: YYYY-MM-DD if printed (convert MM/YY to last day of month), else "".
- confidence: 0 to 1 for how sure you are of that row. Never invent items that are not on the document.
- vendor: shop / distributor name if visible, else ""."""

SCHEMA = {"type": "OBJECT", "properties": {
    "vendor": {"type": "STRING"},
    "items": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {
        "name": {"type": "STRING"}, "qty": {"type": "NUMBER"}, "unit": {"type": "STRING"},
        "unit_cost": {"type": "NUMBER"}, "batch": {"type": "STRING"}, "expiry": {"type": "STRING"},
        "confidence": {"type": "NUMBER"}}, "required": ["name", "qty", "unit", "unit_cost"]}}},
    "required": ["items"]}

DEMO_ITEMS = [
    {"name": "Atta 10kg", "qty": 10, "unit": "bori", "unit_cost": 395, "batch": "AT2410", "expiry": "", "confidence": 0.93},
    {"name": "Besan 1kg", "qty": 24, "unit": "packet", "unit_cost": 78, "batch": "BS118", "expiry": "", "confidence": 0.88},
    {"name": "Biscuit Carton", "qty": 3, "unit": "peti", "unit_cost": 520, "batch": "BC77", "expiry": "", "confidence": 0.81},
]


def _clean(items):
    out = []
    for it in items or []:
        try:
            name = re.sub(r"\s+", " ", str(it.get("name", "")).strip())[:80]
            qty, cost = float(it.get("qty", 0)), float(it.get("unit_cost", 0))
        except (TypeError, ValueError, AttributeError):
            continue
        if not name or qty <= 0 or cost < 0:
            continue
        exp = str(it.get("expiry") or "")
        out.append({"name": name, "qty": min(qty, 100_000), "unit": str(it.get("unit") or "pcs").strip().lower()[:20],
                    "unit_cost": round(cost, 2), "batch": str(it.get("batch") or "")[:30],
                    "expiry": exp if re.match(r"^\d{4}-\d{2}-\d{2}$", exp) else "",
                    "confidence": max(0.0, min(1.0, float(it.get("confidence") or 0.8)))})
    return out[:60]


def _gemini(b64, mime, key):
    body = json.dumps({"contents": [{"parts": [{"text": PROMPT}, {"inline_data": {"mime_type": mime, "data": b64}}]}],
                       "generationConfig": {"temperature": 0, "response_mime_type": "application/json",
                                            "response_schema": SCHEMA}}).encode()
    last = "no model tried"
    for model in dict.fromkeys(MODELS):
        req = urllib.request.Request(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            data=body, headers={"Content-Type": "application/json", "x-goog-api-key": key})
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                data = json.load(r)
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(text), model
        except urllib.error.HTTPError as e:
            last = f"{model}: HTTP {e.code}"
            if e.code in (400, 401, 403, 429):      # bad key / quota: other models will not help
                break
        except Exception as e:                       # network, parse error, empty answer
            last = f"{model}: {e}"
    raise RuntimeError(last)


def scan_bill(p, s):
    """Event handler: payload {image: dataURL or base64, demo: bool}. Returns {items, vendor, demo, model?}."""
    img = str(p.get("image") or "")
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if p.get("demo") or not img or not key:
        why = "Sample bill" if p.get("demo") or not img else "Demo mode: set GEMINI_API_KEY for real scanning"
        return {"items": DEMO_ITEMS, "vendor": "Aggarwal Traders", "demo": True, "note": why}
    mime = "image/jpeg"
    m = re.match(r"^data:(image/[\w.+-]+);base64,", img)
    if m:
        mime, img = m.group(1), img[m.end():]
    if len(img) > MAX_B64:
        return {"ok": False, "error": "Photo is too large. Try again with a smaller photo."}
    try:
        base64.b64decode(img[:64] + "=" * (-len(img[:64]) % 4))
        data, model = _gemini(img, mime, key)
    except Exception as e:
        return {"ok": False, "error": f"Could not read the bill ({e}). Try a clearer, well-lit photo."}
    items = _clean(data.get("items"))
    if not items:
        return {"ok": False, "error": "No items found. Hold the bill flat, in good light, and scan again."}
    return {"items": items, "vendor": str(data.get("vendor") or "")[:60], "demo": False, "model": model}
