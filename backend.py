"""NewSto backend: database setup, accounts, orders, pool joins, saved shop state.
Pure Python + SQLite (standard library). No Streamlit imports, so it is easy to test."""
import hashlib, hmac, json, os, re, secrets, sqlite3
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).parent
DB_PATH = Path(os.environ.get("NEWSTO_DB", ROOT / "newsto.db"))
DEMO = os.environ.get("NEWSTO_DEMO", "1") == "1"        # demo mode: closed pools are re-opened automatically
DEMO_USER = ("Saksham Gupta", "Gupta General Store", "Kirana", "demo@newsto.in", "demo1234")


def connect() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def _run_script(con, text):
    for stmt in text.split(";"):
        stmt = "\n".join(l for l in stmt.splitlines() if not l.strip().startswith("--")).strip()
        if not stmt:
            continue
        try:
            con.execute(stmt)
        except sqlite3.OperationalError as e:
            if "duplicate column" not in str(e).lower():
                raise


def migrate():
    with closing(connect()) as con, con:
        _run_script(con, (ROOT / "04_backend.sql").read_text(encoding="utf-8"))
        if not con.execute("SELECT 1 FROM users WHERE email=?", (DEMO_USER[3],)).fetchone():
            con.execute("INSERT INTO users (name, shop_name, shop_type, email, password_hash) VALUES (?,?,?,?,?)",
                        (*DEMO_USER[:4], _hash(DEMO_USER[4])))


def build_db(reset=True):
    if reset and DB_PATH.exists():
        DB_PATH.unlink()
    with closing(connect()) as con:
        for f in ("01_schema.sql", "02_seed.sql"):
            con.executescript((ROOT / f).read_text(encoding="utf-8"))
        con.commit()
    migrate()


def ensure_db():
    """Builds the database if it is missing (also on Streamlit Cloud), otherwise just migrates it."""
    ok = DB_PATH.exists()
    if ok:
        with closing(connect()) as con:
            ok = con.execute("SELECT COUNT(*) FROM sqlite_master WHERE name='products'").fetchone()[0] == 1
    build_db() if not ok else migrate()


def refresh_demo_pools():
    """Demo mode: re-open pools whose timer ran out so the demo never shows an empty page."""
    if not DEMO:
        return
    with closing(connect()) as con, con:
        con.execute("UPDATE pools SET closes_at = datetime('now', '+' || (90 + (id * 53) % 240) || ' minutes') "
                    "WHERE closes_at <= datetime('now', '+5 minutes')")


# ---------------- accounts ----------------
def _hash(pw, salt=None):
    salt = salt or secrets.token_hex(8)
    return salt + "$" + hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), 120_000).hex()


def _verify(pw, stored):
    salt = stored.split("$")[0]
    return hmac.compare_digest(_hash(pw, salt), stored)


def _user(row):
    return {"id": row["id"], "name": row["name"].split()[0], "shop": row["shop_name"],
            "shop_type": row["shop_type"], "email": row["email"]}


def register(p, s):
    name, shop = str(p.get("name", "")).strip(), str(p.get("shop", "")).strip()
    email, pw = str(p.get("email", "")).strip().lower(), str(p.get("password", ""))
    if not name or not shop:
        return {"ok": False, "error": "Add your name and shop name"}
    if not re.match(r"^\S+@\S+\.\S+$", email):
        return {"ok": False, "error": "Enter a valid email"}
    if len(pw) < 6:
        return {"ok": False, "error": "Password needs 6+ characters"}
    try:
        with closing(connect()) as con, con:
            uid = con.execute("INSERT INTO users (name, shop_name, shop_type, email, password_hash) VALUES (?,?,?,?,?)",
                              (name, shop, str(p.get("shop_type") or "Kirana"), email, _hash(pw))).lastrowid
            row = con.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    except sqlite3.IntegrityError:
        return {"ok": False, "error": "That email is already registered. Try logging in."}
    s["uid"] = uid
    return {"user": _user(row)}


def login(p, s):
    with closing(connect()) as con:
        row = con.execute("SELECT * FROM users WHERE email=?", (str(p.get("email", "")).strip().lower(),)).fetchone()
        if not row or not _verify(str(p.get("password", "")), row["password_hash"]):
            return {"ok": False, "error": "Wrong email or password"}
        st = con.execute("SELECT godown_json, ledger_json FROM user_state WHERE user_id=?", (row["id"],)).fetchone()
    s["uid"] = row["id"]
    u = _user(row)
    if st:
        u["state"] = {"gd": json.loads(st["godown_json"] or "{}"), "lg": json.loads(st["ledger_json"] or "{}")}
    return {"user": u}


def logout(p, s):
    s.pop("uid", None)
    return {}


def save_state(p, s):
    uid = s.get("uid")
    if not uid:
        return {"ok": False, "error": "Not logged in"}
    gd, lg = json.dumps(p.get("gd") or {}), json.dumps(p.get("lg") or {})
    if len(gd) + len(lg) > 1_000_000:
        return {"ok": False, "error": "State too large"}
    with closing(connect()) as con, con:
        con.execute("INSERT INTO user_state (user_id, godown_json, ledger_json) VALUES (?,?,?) "
                    "ON CONFLICT(user_id) DO UPDATE SET godown_json=excluded.godown_json, "
                    "ledger_json=excluded.ledger_json, updated_at=datetime('now')", (uid, gd, lg))
    return {}


# ---------------- orders ----------------
def place_order(p, s):
    items = {}
    for it in p.get("items") or []:
        try:
            pid, q = int(it["id"]), int(it["qty"])
        except (KeyError, TypeError, ValueError):
            continue
        if q > 0:
            items[pid] = items.get(pid, 0) + min(q, 10_000)
    if not items:
        return {"ok": False, "error": "Cart is empty"}
    with closing(connect()) as con, con:
        rows = con.execute(f"SELECT id, price, mrp FROM products WHERE id IN ({','.join('?' * len(items))})", list(items)).fetchall()
        if len(rows) != len(items):
            return {"ok": False, "error": "Some products no longer exist"}
        oid = con.execute("INSERT INTO orders (user_id) VALUES (?)", (s.get("uid"),)).lastrowid
        total = saved = 0
        for r in rows:
            q = items[r["id"]]
            con.execute("INSERT INTO order_items (order_id, product_id, qty, unit_price) VALUES (?,?,?,?)", (oid, r["id"], q, r["price"]))
            total += q * r["price"]
            saved += q * (r["mrp"] - r["price"])
        code = con.execute("SELECT order_code FROM orders WHERE id=?", (oid,)).fetchone()[0]
    return {"code": code, "total": total, "saved": saved}


# ---------------- syndicate pools ----------------
def _pool(con, pid):
    r = con.execute("SELECT id, current_qty, target_qty, stores FROM pools WHERE id=?", (pid,)).fetchone()
    return None if not r else {"id": r["id"], "current": r["current_qty"], "target": r["target_qty"], "stores": r["stores"],
                               "filled": r["current_qty"] >= r["target_qty"]}


def join_pool(p, s):
    try:
        pid, qty = int(p["pool_id"]), float(p["qty"])
    except (KeyError, TypeError, ValueError):
        return {"ok": False, "error": "Invalid request"}
    if qty <= 0:
        return {"ok": False, "error": "Enter a quantity above 0"}
    with closing(connect()) as con, con:
        if not _pool(con, pid):
            return {"ok": False, "error": "Pool not found"}
        # one atomic UPDATE: succeeds only if the pool is open and the quantity still fits
        cur = con.execute("UPDATE pools SET current_qty = current_qty + ?, stores = stores + 1 "
                          "WHERE id = ? AND current_qty + ? <= target_qty AND (closes_at > datetime('now') OR ?)",
                          (qty, pid, qty, 1 if DEMO else 0))
        pool = _pool(con, pid)
        if cur.rowcount == 0:
            left = pool["target"] - pool["current"]
            return {"ok": False, "pool": pool, "error": "This pool is already full" if left <= 0 else
                    f"Only {left:g} left in this pool" if qty > left else "This pool has closed"}
        shop = "Guest shop"
        if s.get("uid"):
            shop = con.execute("SELECT shop_name FROM users WHERE id=?", (s["uid"],)).fetchone()["shop_name"]
        con.execute("INSERT INTO pool_joins (pool_id, shop_name, qty, user_id) VALUES (?,?,?,?)", (pid, shop, qty, s.get("uid")))
    return {"pool": pool}


try:                                            # Parcha-Scan is optional: the rest of the site works without it
    from scan import scan_bill
except Exception:
    scan_bill = lambda p, s: {"ok": False, "error": "Scan module unavailable"}

HANDLERS = {"scan_bill": scan_bill, "register": register, "login": login, "logout": logout, "save_state": save_state,
            "place_order": place_order, "join_pool": join_pool, "ping": lambda p, s: {}}


def handle_event(ev: dict, session) -> dict:
    """Entry point used by app.py. Always returns a JSON-safe dict containing the event id."""
    eid, fn = ev.get("id"), HANDLERS.get(ev.get("type"))
    try:
        res = fn(ev.get("payload") or {}, session) if fn else {"ok": False, "error": f"Unknown action {ev.get('type')}"}
        res.setdefault("ok", True)
    except Exception as e:                       # never crash the demo
        res = {"ok": False, "error": f"Server error: {e}"}
    res["id"] = eid
    return res
