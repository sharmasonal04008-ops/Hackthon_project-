# NewSto · Retail Co-Pilot

## Run
```
pip install -r requirements.txt
streamlit run app.py
```
`newsto.db` is built automatically on first run. To reset all demo data: `python create_db.py` (stop Streamlit first).
Self-test: `python test_backend.py`.  Demo login: **demo@newsto.in / demo1234** (button "Try demo founder").

## How it fits together
| File | Job |
|---|---|
| `ui/index.html` | The whole website (design, animations, all 7 features) |
| `app.py` | Streamlit page that shows the website and passes data/actions between it and Python |
| `data.py` | Reads products, pools, planning data from `newsto.db` |
| `backend.py` | Accounts (hashed passwords), orders, pool joins, saved godown/ledger |
| `logic.py`, `features.py` | Voice parser, weather rules + the older all-Streamlit pages (`app_native.py`) |
| `01_schema.sql` `02_seed.sql` `04_backend.sql` | Tables and demo data (`03_queries.sql` = reference queries) |

## What is saved in the database
- Register / login (`users`), Place bulk order (`orders`, `order_items`, with the user), Join pool (`pools`, `pool_joins`),
  Godown rooms/items and Voice Ledger entries per user (`user_state`, JSON), restored on login.

## Good to know
- If the database fails, the website quietly uses built-in demo data. A sidebar warning shows the reason.
- Demo mode (default) re-opens pools whose timer ran out. Set env `NEWSTO_DEMO=0` for real closing times.
- Weather scenarios are sample data (`logic.SCENARIOS`); replace `forecast()` with a real weather API later.
- Login lasts for the open browser tab (Streamlit session). Refreshing the page logs out.
- Streamlit Cloud: the file system resets on restart, so data resets too. Use PostgreSQL for real persistence.

## Parcha-Scan (handwritten bill / invoice / challan OCR)
Open **Parcha-Scan** in the top menu, take or choose a photo, press **Scan Challan**, edit if needed, then **Add to Godown**.
- Backend: `scan.py` (Gemini REST + JSON schema, no new packages). Set `GEMINI_API_KEY` (optional `GEMINI_MODEL`, default `gemini-1.5-flash`, falls back to newer Flash models).
- Without a key it returns a labelled sample result, so the demo never breaks. "Try a sample bill" works even offline.
- Items go into the Godown with cost, suggested selling price (printed MRP or 12% margin), batch and expiry.
