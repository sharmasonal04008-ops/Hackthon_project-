-- =====================================================================
-- NewSto · 03_queries.sql
-- Ready-made SQL for every function in data.py.
-- Lines starting with ":" (like :pin) are PARAMETERS the backend fills in.
-- NEVER paste user text directly into SQL - always pass it as a parameter.
-- =====================================================================

-- 1) data.get_pincodes() ----------------------------------------------
SELECT pincode || ' · ' || city AS label FROM locations ORDER BY city;

-- 2) data.get_geo_trends(pin)   (:pincode = '202001') -------------------
SELECT item AS "Item", demand_score AS "Demand score"
FROM geo_trends WHERE pincode = :pincode
ORDER BY demand_score DESC;              -- highest demand first

-- 3) data.SHOP_RATE ------------------------------------------------------
SELECT shop_type, rate_per_sqft FROM shop_types;

-- 3b) data.capital_sync(sqft, shop_type)  (:sqft, :shop_type) ------------
SELECT CAST(:sqft * rate_per_sqft AS INTEGER)               AS total,
       CAST(:sqft * rate_per_sqft * stock_pct    AS INTEGER) AS stock,
       CAST(:sqft * rate_per_sqft * fixtures_pct AS INTEGER) AS fixtures,
       CAST(:sqft * rate_per_sqft * buffer_pct   AS INTEGER) AS buffer
FROM shop_types WHERE shop_type = :shop_type;

-- 4) data.get_catalog()  (D2D Sourcing table) ----------------------------
SELECT d.name AS "Distributor", p.name AS "Product", p.category AS "Category",
       p.price AS "NewSto price", p.mrp AS "Middleman price"
FROM products p JOIN distributors d ON d.id = p.distributor_id;

-- 4b) data.get_products()  (JSON for the HTML UI) -------------------------
SELECT p.id, p.name, d.name AS dist, p.category AS cat,
       p.price, p.mrp, p.emoji AS em
FROM products p JOIN distributors d ON d.id = p.distributor_id
ORDER BY p.id;

-- 5) data.place_order(items)  - run these 3 steps inside ONE transaction --
--   Step A: create the order
--     INSERT INTO orders DEFAULT VALUES;
--   Step B: get its id            ->  SELECT last_insert_rowid();   (call it :oid)
--   Step C: add each cart line (repeat per product with qty > 0)
--     INSERT INTO order_items (order_id, product_id, qty, unit_price)
--     SELECT :oid, id, :qty, price FROM products WHERE name = :product_name;
--   Step D: return the code to show in the UI
--     SELECT order_code FROM orders WHERE id = :oid;      -- 'ORD-2026-0001'

-- 5b) Total saved by an order (middleman vs NewSto) ------------------------
SELECT SUM(oi.qty * oi.unit_price)          AS total_paid,
       SUM(oi.qty * (p.mrp - oi.unit_price)) AS total_saved
FROM order_items oi JOIN products p ON p.id = oi.product_id
WHERE oi.order_id = :oid;

-- 6) data.get_godown()  (Godown table + status colours) -------------------
SELECT r.name AS "Room", s.item AS "Item", s.qty AS "Qty",
       CAST(julianday(s.expiry_date) - julianday(date('now')) AS INTEGER) AS "Days to expiry",
       CASE
         WHEN julianday(s.expiry_date) - julianday(date('now')) <= 7  THEN '🔴 CRITICAL'
         WHEN julianday(s.expiry_date) - julianday(date('now')) <= 30 THEN '🟡 WARN'
         ELSE '🟢 OK'
       END AS "Status"
FROM stock s JOIN godown_rooms r ON r.id = s.room_id
ORDER BY r.name, s.expiry_date;

-- 6b) Dashboard numbers (rooms, units, critical alerts) ---------------------
SELECT COUNT(DISTINCT room_id) AS rooms,
       SUM(qty)                AS units_in_stock,
       SUM(CASE WHEN julianday(expiry_date) - julianday(date('now')) <= 7 THEN 1 ELSE 0 END) AS critical_alerts
FROM stock;

-- 7) data.margin_price(cost, margin)  -> no table needed.
--    Formula:  price = cost / (1 - margin/100)   (do it in Python or SQL)
SELECT ROUND(:cost / (1 - :margin / 100.0), 2) AS optimal_price;

-- 8) data.get_pools()  (Syndicate Pool cards) -------------------------------
SELECT id, emoji, name, area, km, unit,
       target_qty AS target, current_qty AS "current",
       base_price AS base, discount_pct AS disc, stores,
       CAST(strftime('%s', closes_at) AS INTEGER) AS closes_at_epoch,  -- unix seconds
       ROUND(100.0 * current_qty / target_qty, 1) AS pct_filled
FROM pools
WHERE km <= 5 AND closes_at > datetime('now')     -- only nearby, still-open pools
ORDER BY km;

-- 8b) Join a pool (run both statements in ONE transaction) ---------------------
--   INSERT INTO pool_joins (pool_id, shop_name, qty) VALUES (:pool_id, :shop, :qty);
--   UPDATE pools SET current_qty = current_qty + :qty, stores = stores + 1
--   WHERE id = :pool_id;
