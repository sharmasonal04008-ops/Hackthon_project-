-- =====================================================================
-- NewSto · 01_schema.sql
-- Creates all TABLES (the empty "spreadsheets" of the database).
-- Database used: SQLite (a single file, no install, works with Python/Streamlit).
-- Run order: 01_schema.sql -> 02_seed.sql -> 03_queries.sql (read only)
-- =====================================================================

-- Start clean so the script can be re-run safely during the hackathon.
DROP TABLE IF EXISTS pool_joins;
DROP TABLE IF EXISTS pools;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS stock;
DROP TABLE IF EXISTS godown_rooms;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS distributors;
DROP TABLE IF EXISTS shop_types;
DROP TABLE IF EXISTS geo_trends;
DROP TABLE IF EXISTS locations;

PRAGMA foreign_keys = ON;   -- make SQLite enforce links between tables

-- ---------------------------------------------------------------------
-- FEATURE 1 · SMART PLANNING
-- ---------------------------------------------------------------------

-- Cities / pin-codes shown in the "Shop pin-code" dropdown.
-- Replaces: data.get_pincodes()
CREATE TABLE locations (
    pincode  TEXT PRIMARY KEY,          -- e.g. '202001'
    city     TEXT NOT NULL              -- e.g. 'Aligarh'
);

-- Demand score (0-100) of each item in each pin-code.
-- Replaces: data.get_geo_trends(pin)
CREATE TABLE geo_trends (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    pincode       TEXT    NOT NULL REFERENCES locations(pincode),
    item          TEXT    NOT NULL,     -- e.g. 'Besan'
    demand_score  INTEGER NOT NULL CHECK (demand_score BETWEEN 0 AND 100),
    UNIQUE (pincode, item)              -- one score per item per pincode
);

-- Cost per sq ft for each shop type + how the budget is split.
-- Replaces: data.SHOP_RATE and data.capital_sync()
CREATE TABLE shop_types (
    shop_type      TEXT PRIMARY KEY,    -- 'Kirana', 'Bakery', ...
    rate_per_sqft  INTEGER NOT NULL,    -- Rs per sq ft
    stock_pct      REAL NOT NULL DEFAULT 0.60,    -- 60% of capital -> stock
    fixtures_pct   REAL NOT NULL DEFAULT 0.25,    -- 25% -> shelves, fridge etc.
    buffer_pct     REAL NOT NULL DEFAULT 0.15     -- 15% -> emergency money
);

-- ---------------------------------------------------------------------
-- FEATURE 2 · D2D SOURCING (distributors, products, orders)
-- ---------------------------------------------------------------------

CREATE TABLE distributors (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    name      TEXT NOT NULL UNIQUE,     -- 'Aggarwal Traders'
    verified  INTEGER NOT NULL DEFAULT 1   -- 1 = shows the "verified" tick
);

-- Replaces: data.get_catalog() and data.get_products()
CREATE TABLE products (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,      -- 'Atta 10kg'
    distributor_id  INTEGER NOT NULL REFERENCES distributors(id),
    category        TEXT NOT NULL,      -- Staples / Oils / Beverages ...
    price           REAL NOT NULL,      -- NewSto (direct) price
    mrp             REAL NOT NULL,      -- Middleman price (what shop pays today)
    emoji           TEXT,               -- icon shown in the UI
    CHECK (price <= mrp)                -- direct price must never exceed middleman
);

-- One row per order placed with the "One-click bulk order" button.
-- Replaces: data.place_order()
CREATE TABLE orders (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    order_code  TEXT UNIQUE,            -- 'ORD-2026-0001' (filled by the app/trigger)
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    status      TEXT NOT NULL DEFAULT 'PLACED'   -- PLACED / SHIPPED / DELIVERED
);

-- The items inside each order (a cart can hold many products).
CREATE TABLE order_items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id    INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id  INTEGER NOT NULL REFERENCES products(id),
    qty         INTEGER NOT NULL CHECK (qty > 0),
    unit_price  REAL    NOT NULL        -- price at the time of order (copy it!)
);

-- Auto-create order_code like ORD-2026-0001 right after an order is inserted.
CREATE TRIGGER trg_order_code
AFTER INSERT ON orders
WHEN NEW.order_code IS NULL
BEGIN
    UPDATE orders
       SET order_code = 'ORD-' || strftime('%Y','now') || '-' || printf('%04d', NEW.id)
     WHERE id = NEW.id;
END;

-- ---------------------------------------------------------------------
-- FEATURE 3 · GODOWN & ALERTS
-- ---------------------------------------------------------------------

CREATE TABLE godown_rooms (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    name  TEXT NOT NULL UNIQUE          -- 'Room A · Front'
);

-- Replaces: data.get_godown()
-- We store the EXPIRY DATE (not "days left") because days left changes daily;
-- the query calculates it automatically.
CREATE TABLE stock (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id      INTEGER NOT NULL REFERENCES godown_rooms(id),
    item         TEXT    NOT NULL,
    qty          INTEGER NOT NULL CHECK (qty >= 0),
    expiry_date  TEXT    NOT NULL       -- format YYYY-MM-DD
);

-- ---------------------------------------------------------------------
-- FEATURE 7 · SYNDICATE POOL (group buying)
-- ---------------------------------------------------------------------

-- Replaces: data.get_pools()
CREATE TABLE pools (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    emoji         TEXT,
    name          TEXT NOT NULL,        -- 'Basmati Rice 500kg Bulk Pool'
    area          TEXT NOT NULL,        -- 'Sector 4'
    km            REAL NOT NULL,        -- distance from the shop
    unit          TEXT NOT NULL,        -- 'kg' or 'L'
    target_qty    REAL NOT NULL,        -- goal quantity to unlock the discount
    current_qty   REAL NOT NULL DEFAULT 0,  -- already pooled quantity
    base_price    REAL NOT NULL,        -- normal price per unit
    discount_pct  REAL NOT NULL,        -- discount if target is reached
    stores        INTEGER NOT NULL DEFAULT 0,   -- how many shops joined
    closes_at     TEXT NOT NULL         -- when the pool closes (YYYY-MM-DD HH:MM:SS)
);

-- Who joined which pool and how much they added.
CREATE TABLE pool_joins (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    pool_id     INTEGER NOT NULL REFERENCES pools(id) ON DELETE CASCADE,
    shop_name   TEXT NOT NULL,
    qty         REAL NOT NULL CHECK (qty > 0),
    joined_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Indexes = make common searches fast.
CREATE INDEX idx_geo_pincode   ON geo_trends(pincode);
CREATE INDEX idx_products_cat  ON products(category);
CREATE INDEX idx_stock_room    ON stock(room_id);
CREATE INDEX idx_stock_expiry  ON stock(expiry_date);
