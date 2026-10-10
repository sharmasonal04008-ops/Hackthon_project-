"""Quick self-test (uses a temporary database):   python test_backend.py"""
import os, tempfile
os.environ["NEWSTO_DB"] = os.path.join(tempfile.mkdtemp(), "test.db")
import backend, data

S = {}
ev = lambda t, p, s=S: backend.handle_event({"id": "t", "type": t, "payload": p}, s)

assert len(data.get_products()) == 12 and len(data.get_pools()) == 4
assert ev("register", {"name": "Asha V", "shop": "Verma Store", "email": "a@x.in", "password": "secret1"})["ok"]
assert not ev("register", {"name": "Asha V", "shop": "Verma Store", "email": "a@x.in", "password": "secret1"})["ok"]   # duplicate email
assert not ev("login", {"email": "a@x.in", "password": "wrong"}, {})["ok"]
s2 = {}
assert ev("login", {"email": "a@x.in", "password": "secret1"}, s2)["ok"] and s2["uid"]
assert ev("save_state", {"gd": {"rooms": ["Back"]}, "lg": {}}, s2)["ok"]
assert ev("login", {"email": "a@x.in", "password": "secret1"}, {})["user"]["state"]["gd"]["rooms"] == ["Back"]
o = ev("place_order", {"items": [{"id": 1, "qty": 4}, {"id": 2, "qty": 2}]}, s2)
assert o["ok"] and o["code"].startswith("ORD-") and o["saved"] == 164
pid = data.get_pools()[0]["id"]
assert ev("join_pool", {"pool_id": pid, "qty": 50}, s2)["pool"]["current"] == 430
assert not ev("join_pool", {"pool_id": pid, "qty": 500}, s2)["ok"]            # more than remaining
assert ev("join_pool", {"pool_id": pid, "qty": 70}, s2)["pool"]["filled"]     # fills the pool
assert not ev("join_pool", {"pool_id": pid, "qty": 1}, s2)["ok"]              # already full
print("All backend tests passed")
