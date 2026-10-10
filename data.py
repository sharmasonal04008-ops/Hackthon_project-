"""Data layer: reads newsto.db. Same function names and return shapes as data_mock.py."""
import json
from contextlib import closing
import pandas as pd
import backend

backend.ensure_db()                       # builds the database automatically if it is missing


def _df(sql, params=()):
    with closing(backend.connect()) as con:      # closing() releases the file (needed on Windows)
        return pd.read_sql_query(sql, con, params=params)


def _records(df):
    """DataFrame -> list of plain Python dicts (numpy numbers break json.dumps otherwise)."""
    return json.loads(df.to_json(orient="records", force_ascii=False))


def get_pincodes():
    return _df("SELECT pincode || ' · ' || city AS label FROM locations ORDER BY city")["label"].tolist()


def get_geo_trends(pin: str) -> pd.DataFrame:
    pincode = pin.split(" ")[0]
    return _df('SELECT item AS Item, demand_score AS "Demand score" FROM geo_trends '
               'WHERE pincode=? ORDER BY demand_score DESC', (pincode,)).set_index("Item")


SHOP_RATE = {k: int(v) for k, v in _df("SELECT shop_type, rate_per_sqft FROM shop_types").values}


def capital_sync(sqft: int, shop_type: str) -> dict:
    r = _df("SELECT rate_per_sqft*? AS total, stock_pct, fixtures_pct, buffer_pct FROM shop_types WHERE shop_type=?",
            (sqft, shop_type)).iloc[0]
    t = int(r.total)
    return {"total": t, "stock": int(t * r.stock_pct), "fixtures": int(t * r.fixtures_pct), "buffer": int(t * r.buffer_pct)}


def get_catalog() -> pd.DataFrame:
    return _df('SELECT d.name AS Distributor, p.name AS Product, p.category AS Category, '
               'p.price AS "NewSto price", p.mrp AS "Middleman price" '
               'FROM products p JOIN distributors d ON d.id=p.distributor_id')


def place_order(items: dict) -> str:      # items = {"Atta 10kg": 3, "Besan 1kg": 0}
    with closing(backend.connect()) as con, con:
        oid = con.execute("INSERT INTO orders DEFAULT VALUES").lastrowid
        for name, qty in items.items():
            if qty and qty > 0:
                con.execute("INSERT INTO order_items (order_id, product_id, qty, unit_price) "
                            "SELECT ?, id, ?, price FROM products WHERE name=?", (oid, int(qty), name))
        return con.execute("SELECT order_code FROM orders WHERE id=?", (oid,)).fetchone()[0]


def get_godown() -> pd.DataFrame:
    return _df("""SELECT r.name AS Room, s.item AS Item, s.qty AS Qty,
        CAST(julianday(s.expiry_date) - julianday(date('now')) AS INTEGER) AS "Days to expiry",
        CASE WHEN julianday(s.expiry_date)-julianday(date('now')) <= 7  THEN '🔴 CRITICAL'
             WHEN julianday(s.expiry_date)-julianday(date('now')) <= 30 THEN '🟡 WARN'
             ELSE '🟢 OK' END AS Status
        FROM stock s JOIN godown_rooms r ON r.id=s.room_id ORDER BY r.name, s.expiry_date""")


def margin_price(cost: float, margin_pct: float) -> float:
    return round(cost / (1 - margin_pct / 100), 2)


def get_pools() -> list:
    backend.refresh_demo_pools()
    return _records(_df("""SELECT id, emoji, name, area, km, unit, target_qty AS target, current_qty AS current,
                  base_price AS base, discount_pct AS disc, stores,
                  CAST(strftime('%s', closes_at) AS INTEGER) AS closes_at
                  FROM pools WHERE km <= 5 AND closes_at > datetime('now') ORDER BY id"""))


def get_products() -> list:
    return _records(_df("SELECT p.id, p.name, d.name AS dist, p.category AS cat, p.price, p.mrp, p.emoji AS em "
                        "FROM products p JOIN distributors d ON d.id=p.distributor_id ORDER BY p.id"))
