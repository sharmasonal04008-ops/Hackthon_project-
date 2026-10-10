-- NewSto · 04_backend.sql : tables the live website needs (accounts + saved shop state).
-- Safe to run more than once (backend.py ignores "duplicate column" errors).
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    shop_name     TEXT NOT NULL,
    shop_type     TEXT NOT NULL DEFAULT 'Kirana',
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,            -- 'salt$pbkdf2-sha256' (never the plain password)
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
-- Godown rooms/items and the voice-ledger of each user, saved as JSON (simple for a hackathon).
CREATE TABLE IF NOT EXISTS user_state (
    user_id     INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    godown_json TEXT NOT NULL DEFAULT '{}',
    ledger_json TEXT NOT NULL DEFAULT '{}',
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
ALTER TABLE orders     ADD COLUMN user_id INTEGER REFERENCES users(id);
ALTER TABLE pool_joins ADD COLUMN user_id INTEGER REFERENCES users(id);
CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);
