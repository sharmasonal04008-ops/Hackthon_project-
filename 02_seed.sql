-- =====================================================================
-- NewSto · 02_seed.sql
-- Fills the tables with the SAME demo data that is in data.py,
-- so the UI looks identical when you switch from mock data to the database.
-- =====================================================================

-- Locations (pincode dropdown) ----------------------------------------
INSERT INTO locations (pincode, city) VALUES
 ('202001','Aligarh'), ('110001','New Delhi'), ('226001','Lucknow');

-- Geo-trend demand scores ---------------------------------------------
INSERT INTO geo_trends (pincode, item, demand_score) VALUES
 ('202001','Besan',92), ('202001','Atta',88), ('202001','Mustard Oil',81),
 ('202001','Tea',79),   ('202001','Biscuits',72), ('202001','Rice',64),
 ('110001','Rice',90),  ('110001','Biscuits',86), ('110001','Snacks',84),
 ('110001','Tea',77),   ('110001','Atta',70), ('110001','Besan',55),
 ('226001','Atta',89),  ('226001','Tea',85), ('226001','Rice',80),
 ('226001','Mustard Oil',74), ('226001','Besan',70), ('226001','Snacks',66);

-- Shop types (rate per sq ft; split uses the 60/25/15 defaults) --------
INSERT INTO shop_types (shop_type, rate_per_sqft) VALUES
 ('Kirana',1800), ('Bakery',2200), ('Pharmacy',3500), ('Stationery',1500);

-- Distributors ----------------------------------------------------------
INSERT INTO distributors (name) VALUES
 ('Aggarwal Traders'), ('Sharma Agencies'), ('Gupta Wholesale'), ('Dairy Fresh Co');

-- Products (name, distributor, category, NewSto price, middleman price, emoji)
INSERT INTO products (name, distributor_id, category, price, mrp, emoji) VALUES
 ('Atta 10kg',        (SELECT id FROM distributors WHERE name='Aggarwal Traders'),'Staples',   395,430,'🌾'),
 ('Besan 1kg',        (SELECT id FROM distributors WHERE name='Aggarwal Traders'),'Staples',    78, 90,'🫘'),
 ('Basmati Rice 5kg', (SELECT id FROM distributors WHERE name='Sharma Agencies'), 'Staples',   410,455,'🍚'),
 ('Toor Dal 5kg',     (SELECT id FROM distributors WHERE name='Sharma Agencies'), 'Staples',   640,700,'🫘'),
 ('Mustard Oil 1L',   (SELECT id FROM distributors WHERE name='Sharma Agencies'), 'Oils',      128,142,'🫒'),
 ('Refined Oil 5L',   (SELECT id FROM distributors WHERE name='Gupta Wholesale'), 'Oils',      690,760,'🛢️'),
 ('Tea 500g',         (SELECT id FROM distributors WHERE name='Gupta Wholesale'), 'Beverages', 190,215,'🍵'),
 ('Cold Drink Crate', (SELECT id FROM distributors WHERE name='Gupta Wholesale'), 'Beverages', 310,340,'🥤'),
 ('Biscuit Carton',   (SELECT id FROM distributors WHERE name='Gupta Wholesale'), 'Snacks',    520,580,'🍪'),
 ('Namkeen 10 pack',  (SELECT id FROM distributors WHERE name='Sharma Agencies'), 'Snacks',    360,400,'🥨'),
 ('Milk Packs (12)',  (SELECT id FROM distributors WHERE name='Dairy Fresh Co'),  'Dairy',     650,700,'🥛'),
 ('Detergent 5kg',    (SELECT id FROM distributors WHERE name='Aggarwal Traders'),'Household', 420,480,'🧴');

-- Godown rooms ----------------------------------------------------------
INSERT INTO godown_rooms (name) VALUES
 ('Room A · Front'), ('Room B · Back'), ('Room C · Cold');

-- Stock: expiry = today + N days, so the demo alerts always look fresh.
INSERT INTO stock (room_id, item, qty, expiry_date) VALUES
 ((SELECT id FROM godown_rooms WHERE name='Room A · Front'),'Atta 10kg',     40, date('now','+120 day')),
 ((SELECT id FROM godown_rooms WHERE name='Room A · Front'),'Biscuit Carton',12, date('now','+6 day')),
 ((SELECT id FROM godown_rooms WHERE name='Room B · Back'), 'Besan 1kg',     55, date('now','+25 day')),
 ((SELECT id FROM godown_rooms WHERE name='Room B · Back'), 'Mustard Oil 1L',30, date('now','+90 day')),
 ((SELECT id FROM godown_rooms WHERE name='Room C · Cold'), 'Milk Packs',    60, date('now','+3 day')),
 ((SELECT id FROM godown_rooms WHERE name='Room C · Cold'), 'Paneer 200g',   18, date('now','+12 day'));

-- Syndicate pools (closes_at = now + N hours) --------------------------
INSERT INTO pools (emoji,name,area,km,unit,target_qty,current_qty,base_price,discount_pct,stores,closes_at) VALUES
 ('🍚','Basmati Rice 500kg Bulk Pool','Sector 4',    1.8,'kg', 500,380, 91,18,4, datetime('now','+255 minutes')),
 ('🫒','Cooking Oil 200L Pool',       'Civil Lines', 2.6,'L',  200,120,142,12,3, datetime('now','+102 minutes')),
 ('🌾','Atta 1000kg Bulk Pool',       'Marris Road', 3.4,'kg',1000,640,39.5,10,6, datetime('now','+450 minutes')),
 ('🍵','Tea 100kg Pool',              'Sector 4',    0.9,'kg', 100, 85,380,15,5, datetime('now','+144 minutes'));
