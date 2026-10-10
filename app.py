"""NewSto: Streamlit app. Shows the full website (ui/index.html) as a two-way component:
  Python -> website : products, pools, forecasts (from newsto.db via data.py)
  website -> Python : register, login, orders, pool joins, saved godown/ledger (handled by backend.py)
If anything fails, the website falls back to its built-in demo data, so the demo never breaks."""
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="NewSto · Retail Co-Pilot", page_icon="🛒", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""<style>
#MainMenu,header,footer,[data-testid="stToolbar"],[data-testid="stSidebar"],[data-testid="collapsedControl"],[data-testid="stDecoration"]{display:none!important}
.stApp{background:#fff3dc}.block-container{padding:0!important;max-width:100%!important}
[data-testid="stMain"],section.main{overflow:hidden!important}
iframe{height:100vh!important;width:100%!important;border:0;display:block}
</style>""", unsafe_allow_html=True)

UI_DIR = Path(__file__).parent / "ui"
if not (UI_DIR / "index.html").exists():
    st.error(f"Website file missing. Expected: {UI_DIR / 'index.html'}")
    st.stop()

ui = components.declare_component("newsto_ui", path=str(UI_DIR))


def build_payload() -> dict:
    payload = {}
    try:
        import data
        payload["products"] = data.get_products()
        payload["pools"] = [{**{k: v for k, v in p.items() if k not in ("current", "closes_at")},
                             "cur": p["current"], "end": int(p["closes_at"] * 1000)} for p in data.get_pools()]
    except Exception as e:                       # the website then uses its built-in demo data
        st.sidebar.warning(f"Database unavailable, using demo data: {e}")
    try:
        import logic
        payload["scenarios"] = {k: [list(day) for day in v] for k, v in logic.SCENARIOS.items()}
    except Exception:
        pass
    return payload


ss = st.session_state
event = ui(data=build_payload(), result=ss.get("result"), key="newsto_ui", default=None)

# A new action arrived from the website: save it in the database, then rerun to send back the answer.
if isinstance(event, dict) and event.get("id") and event["id"] != ss.get("last_event"):
    ss["last_event"] = event["id"]
    try:
        import backend
        ss["result"] = backend.handle_event(event, ss)
    except Exception as e:
        ss["result"] = {"id": event["id"], "ok": False, "error": f"Server error: {e}"}
    st.rerun()
