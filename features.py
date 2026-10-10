"""UI for the three new features: Voice Ledger, Ambient Demand Engine, Micro-Syndicate Sourcing."""
import time
import streamlit as st
import streamlit.components.v1 as components
import data
import logic

inr = lambda n: f"₹{round(n):,}"
AV = ["#d2461e", "#2f7d4f", "#2b5d9e", "#b7791f"]

CSS = """
<style>
.bdg{display:inline-block;padding:3px 12px;border-radius:20px;font-size:.78rem;background:#18202b;border:1px solid #f0b42966;color:#f0d28a}
.avs{display:flex;align-items:center;gap:10px;margin:.4rem 0}
.avs .st{display:flex}.avs .st span{width:30px;height:30px;border-radius:50%;border:2px solid #0b0f0c;margin-left:-8px;display:grid;place-items:center;font-size:.68rem;font-weight:700;color:#fff}
.avs .st span:first-child{margin-left:0}
.ok{color:#3ddc84;font-weight:800}
[data-testid="stVerticalBlockBorderWrapper"]{background:rgba(255,255,255,.04);backdrop-filter:blur(10px);border-radius:16px}
</style>
"""


def init_state():
    ss = st.session_state
    ss.setdefault("ledger", [])          # TODO backend: persist to DB
    ss.setdefault("stock", {})           # {item: qty}; shared with Godown page if you wire it
    ss.setdefault("pools", data.get_pools())
    ss.setdefault("restock", [])
    ss.setdefault("flash", None)


def _head(tag, title, sub=""):
    st.markdown(CSS + f'<div class="tag">{tag}</div><div class="hero" style="font-size:2.2rem">{title}</div>'
                      f'<p style="color:#7a9a84">{sub}</p>', unsafe_allow_html=True)


def _flash():
    f = st.session_state.pop("flash", None)
    if f:
        (st.success if f[0] else st.warning)(f[1])


# =====================================================================
# 1. VOICE LEDGER
# =====================================================================
MIC_HTML = """
<div style="font-family:monospace;text-align:center;color:#d7f5df">
<button id="m" style="width:84px;height:84px;border-radius:50%;font-size:32px;border:0;background:#3ddc84;cursor:pointer">🎙️</button>
<div id="s" style="margin:8px 0;font-size:13px;color:#7a9a84">Tap the mic and speak</div>
<select id="l" style="background:#101812;color:#d7f5df;border:1px solid #1f3a28;border-radius:6px;padding:4px">
<option value="en-IN">English / Hinglish</option><option value="hi-IN">Hindi</option></select></div>
<script>
const SR=window.SpeechRecognition||window.webkitSpeechRecognition,m=document.getElementById('m'),s=document.getElementById('s');
function send(t){
  try{const P=window.parent,i=P.document.querySelector('input[aria-label="voice_transcript"]');
    if(!i){s.textContent='Type it in the box below';return}
    Object.getOwnPropertyDescriptor(P.HTMLInputElement.prototype,'value').set.call(i,t);
    i.dispatchEvent(new Event('input',{bubbles:true}));
    i.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',code:'Enter',keyCode:13,which:13,bubbles:true}));
  }catch(e){s.textContent='Copy the text into the box below'}}
if(!SR){s.textContent='Voice needs Chrome. Use the text box below.';m.disabled=true}
else{const r=new SR();r.interimResults=true;let on=false;
  m.onclick=()=>{if(on){r.stop();return}r.lang=document.getElementById('l').value;try{r.start()}catch(e){}};
  r.onstart=()=>{on=true;m.style.background='#ff6b6b';s.textContent='Listening...'};
  r.onresult=e=>{const t=[...e.results].map(x=>x[0].transcript).join(' ');s.textContent='"'+t+'"';
    if(e.results[e.results.length-1].isFinal)send(t)};
  r.onerror=e=>{s.textContent='Mic error ('+e.error+'). Use the text box below.'};
  r.onend=()=>{on=false;m.style.background='#3ddc84'}}
</script>"""

EXAMPLES = ["sold 5 kg atta at 40 rupees", "paanch kilo atta bech diya 40 rupaye",
            "bought 20 packet biscuit at 10 each", "do litre mustard oil becha 150 rupaye litre"]


def _log(text):
    ss = st.session_state
    ok, msg = logic.apply_command(text, ss.ledger, ss.stock)
    ss.flash = (ok, msg)


def page_ledger():
    ss = st.session_state
    _head("FEATURE 04 · VOICE LEDGER", "Speak your sales. We do the books.",
          "Say “sold 5 kg atta at 40 rupees” or “paanch kilo atta bech diya 40 rupaye”. English and Hinglish both work.")
    left, right = st.columns(2)
    with left:
        components.html(MIC_HTML, height=170)
        with st.form("voice_form", clear_on_submit=True):
            txt = st.text_input("voice_transcript", label_visibility="collapsed", placeholder="Or type: sold 5 kg atta at 40 rupees")
            go = st.form_submit_button("Log it", use_container_width=True)
        if go and txt.strip():
            _log(txt)
            st.rerun()
        st.caption("Quick demo commands (work even without a microphone):")
        for i, ex in enumerate(EXAMPLES):
            st.button(ex, key=f"ex{i}", on_click=_log, args=(ex,), use_container_width=True)
    with right:
        _flash()
        p = logic.pnl(ss.ledger)
        st.markdown("**Today's P&L**")
        c1, c2, c3 = st.columns(3)
        c1.metric("Sales", inr(p["sales"]))
        c2.metric("Purchases", inr(p["purchases"]))
        c3.metric("Net today", inr(p["net"]), delta=f"{p['net']:+,.0f}" if p["net"] else None)
        st.markdown("**Stock now**")
        if ss.stock:
            st.dataframe([{"Item": k, "Qty": f"{v:g}"} for k, v in ss.stock.items()], hide_index=True, use_container_width=True)
        else:
            st.caption("Stock updates here as you log entries.")
    st.markdown("**Today's entries**")
    if ss.ledger:
        st.dataframe([{"Time": e["time"], "Type": "🟢 Sale" if e["type"] == "sale" else "🔵 Purchase", "Item": e["item"],
                       "Qty": f"{e['qty']:g} {e['unit']}", "Rate": inr(e["price"]), "Total": inr(e["total"]),
                       "Stock after": f"{e['stock_after']:g}"} for e in ss.ledger], hide_index=True, use_container_width=True)
        if st.button("↩ Undo last entry"):
            e = ss.ledger.pop(0)
            ss.stock[e["item"]] = max(0, ss.stock.get(e["item"], 0) + (e["qty"] if e["type"] == "sale" else -e["qty"]))
            st.rerun()
    else:
        st.caption("No entries yet. Tap the mic or an example above.")


# =====================================================================
# 2. AMBIENT DEMAND ENGINE
# =====================================================================
def _restock(name):
    p = next((r for _, r in data.get_catalog().iterrows() if name.lower() in r["Product"].lower()), None)
    if p is not None and p["Product"] not in st.session_state.restock:
        st.session_state.restock.append(p["Product"])
    st.toast(f"🛒 {p['Product'] if p is not None else name} added to restock list")


def page_ambient():
    ss = st.session_state
    _head("FEATURE 05 · AMBIENT DEMAND ENGINE", "Know what the weather will do to your shelves.",
          "Forecast-driven spoilage alerts and restock surges. Demo uses sample forecasts; swap logic.forecast() for a live weather API.")
    scn = st.radio("Forecast scenario", list(logic.SCENARIOS), horizontal=True)
    days = logic.forecast(scn)
    for col, d in zip(st.columns(5), days):
        icon = "🌧️" if d["rain"] >= 60 else "☀️" if d["temp"] >= 36 else "☁️" if d["hum"] >= 70 else "🌤️"
        with col:
            with st.container(border=True):
                st.markdown(f"**{d['day']}** {icon}  \n{d['temp']}°C  \n💧{d['hum']}% · ☔{d['rain']}%")
    res = logic.analyze_weather(days)
    st.progress(res["risk"] / 100, text=f"Spoilage risk (next 3 days): {res['risk']}/100")
    for i, (lvl, title, body, prods) in enumerate(res["alerts"]):
        getattr(st, lvl)(f"**{title}**\n\n{body}")
        if prods:
            for col, name in zip(st.columns(len(prods)), prods):
                col.button(f"+ {name}", key=f"rs{i}{name}", on_click=_restock, args=(name,), use_container_width=True)
    st.markdown("**Your stock at risk**")
    hit = [f"{k} ({v:g})" for k, v in ss.stock.items() if any(w in k.lower() for w in logic.HUMID_ITEMS)] if res["at_risk"] else []
    st.caption(", ".join(hit) if hit else ("None of your logged items are affected." if ss.stock else
               "Log stock in Voice Ledger and the engine will flag the items it affects."))
    if ss.restock:
        st.markdown("**Restock list:** " + " · ".join(ss.restock))


# =====================================================================
# 3. MICRO-SYNDICATE SOURCING
# =====================================================================
@st.fragment(run_every=1)
def _countdown(closes_at):
    s = max(0, int(closes_at - time.time()))
    st.markdown(f'<span class="bdg">⏱ Closes in {s // 3600:02d}h : {s % 3600 // 60:02d}m</span>', unsafe_allow_html=True)


@st.dialog("Join pool")
def _join_dialog(pid):
    p = next(x for x in st.session_state.pools if x["id"] == pid)
    rem = int(p["target"] - p["current"])
    st.markdown(f"**{p['name']}**")
    qty = st.number_input(f"Your store's contribution ({p['unit']})", min_value=1, max_value=rem, value=min(50, rem), step=1)
    std, syn, saved = logic.pool_price(p, qty)
    c1, c2 = st.columns(2)
    c1.metric("Standard individual price", inr(std))
    c2.metric("Syndicate bulk price", inr(syn))
    st.markdown(f"Total saved: <span class='ok' style='font-size:1.7rem'>{inr(saved)}</span>", unsafe_allow_html=True)
    st.caption(f"Up to {rem}{p['unit']} remaining. Discount applies when the pool fills.")
    if st.button("Confirm and join", type="primary", use_container_width=True):
        filled = logic.join_pool(p, qty)
        try:                                   # also save the join in newsto.db
            import backend
            backend.join_pool({"pool_id": pid, "qty": qty}, {})
        except Exception:
            pass
        st.session_state.flash = (True, "🎉 Wholesale Tier 1 Unlocked - Order Dispatched to Distributor" if filled
                                  else f"✔ You joined with {qty}{p['unit']}")
        st.session_state.balloons = filled
        st.rerun()


def page_syndicate():
    ss = st.session_state
    _head("FEATURE 06 · MICRO-SYNDICATE SOURCING", "Nearby Pooling Deals",
          "Shops within 5 km pool their orders to unlock tier-1 distributor pricing.")
    _flash()
    if ss.pop("balloons", False):
        st.balloons()
    for row in range(0, len(ss.pools), 2):
        for col, p in zip(st.columns(2), ss.pools[row:row + 2]):
            pct, rem = logic.pool_pct(p), p["target"] - p["current"]
            with col:
                with st.container(border=True):
                    st.markdown(f"#### {p['emoji']} {p['name']}")
                    st.caption(f"📍 {p['area']} · {p['km']} km away")
                    _countdown(p["closes_at"])
                    st.progress(pct / 100)
                    if pct >= 100:
                        st.success("✔ Wholesale Tier 1 Unlocked - Order Dispatched to Distributor")
                    else:
                        st.markdown(f"Current Pool: **{p['current']:g}{p['unit']} / {p['target']}{p['unit']}** ({pct}% filled) — "
                                    f"{rem:g}{p['unit']} needed to unlock **{p['disc']}%** bulk wholesale discount.")
                    avs = "".join(f'<span style="background:{AV[i]}">{"ABCD"[i]}{i + 1}</span>' for i in range(min(p["stores"], 4)))
                    avs += '<span style="background:#222">You</span>' if p.get("yours") else ""
                    st.markdown(f'<div class="avs"><div class="st">{avs}</div><span style="color:#7a9a84;font-size:.8rem">'
                                f'{p["stores"]} neighboring verified stores joined</span></div>', unsafe_allow_html=True)
                    st.caption(f"{inr(p['base'])}/{p['unit']} alone → {inr(p['base'] * (1 - p['disc'] / 100))}/{p['unit']} in syndicate")
                    if st.button("Pool filled" if pct >= 100 else "Join Pool", key=f"join{p['id']}", disabled=pct >= 100,
                                 type="primary", use_container_width=True):
                        _join_dialog(p["id"])
