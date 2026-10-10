import time
import streamlit as st
import pandas as pd
import data
import features

st.set_page_config(page_title="NewSto · Retail Co-Pilot", page_icon="🛒", layout="wide", initial_sidebar_state="collapsed")

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700;800&display=swap');
html,body,[class*="css"],.stApp{font-family:'JetBrains Mono',monospace!important}
.stApp{background:radial-gradient(circle at 20% 0%,#142a1b 0%,#0b0f0c 55%)}
#MainMenu,footer,header,[data-testid="stSidebar"],[data-testid="collapsedControl"]{display:none!important}
.block-container{padding-top:1.2rem;max-width:1150px}
/* page transition: terminal wipe + staggered fade-up */
.wipe{position:fixed;inset:0;z-index:99999;background:#0b0f0c;display:flex;align-items:center;justify-content:center;
 color:#3ddc84;font-size:1.4rem;font-weight:700;pointer-events:none;animation:wipe .9s cubic-bezier(.77,0,.18,1) forwards}
@keyframes wipe{0%{clip-path:inset(0 0 0 0)}55%{clip-path:inset(0 0 0 0)}100%{clip-path:inset(0 0 0 100%)}}
.wipe span{border-right:3px solid #3ddc84;white-space:nowrap;overflow:hidden;animation:type .45s steps(24) both}
@keyframes type{from{width:0}to{width:100%}}
.stApp [data-testid="stVerticalBlock"]>div{animation:up .6s ease both}
.stApp [data-testid="stVerticalBlock"]>div:nth-child(2){animation-delay:.1s}
.stApp [data-testid="stVerticalBlock"]>div:nth-child(3){animation-delay:.2s}
.stApp [data-testid="stVerticalBlock"]>div:nth-child(4){animation-delay:.3s}
.stApp [data-testid="stVerticalBlock"]>div:nth-child(5){animation-delay:.4s}
@keyframes up{from{opacity:0;transform:translateY(22px)}to{opacity:1;transform:none}}
/* hero + cards */
.tag{color:#7a9a84;font-size:.8rem;letter-spacing:.15em}
.hero{font-size:clamp(2rem,5vw,3.6rem);font-weight:800;line-height:1.1;margin:.3rem 0}
.hero b{color:#3ddc84}
.type{display:inline-block;border-right:3px solid #3ddc84;overflow:hidden;white-space:nowrap;max-width:100%;
 animation:type 2.2s steps(40) both,blink .8s step-end infinite}
@keyframes blink{50%{border-color:transparent}}
.steps{display:flex;gap:.6rem;flex-wrap:wrap;margin:1rem 0 1.4rem}
.step{border:1px solid #1f3a28;padding:.35rem .8rem;border-radius:6px;color:#7a9a84;animation:glow 5s infinite}
.step:nth-child(2){animation-delay:1s}.step:nth-child(3){animation-delay:2s}.step:nth-child(4){animation-delay:3s}.step:nth-child(5){animation-delay:4s}
@keyframes glow{0%,20%{border-color:#3ddc84;color:#3ddc84;box-shadow:0 0 14px #3ddc8444}30%,100%{border-color:#1f3a28;color:#7a9a84;box-shadow:none}}
.card{border:1px solid #1f3a28;background:#101812;border-radius:12px;padding:1.1rem;min-height:150px;transition:.25s}
.card:hover{transform:translateY(-6px);border-color:#3ddc84;box-shadow:0 10px 30px #3ddc8422}
.card h4{margin:.2rem 0 .4rem;color:#d7f5df}.card p{color:#8aa994;font-size:.82rem;margin:0}
.live{color:#3ddc84;font-size:.7rem}.soon{color:#e5b84b;font-size:.7rem}
.stButton>button{width:100%;border-radius:8px;border:1px solid #1f3a28;background:#101812;color:#d7f5df;transition:.2s}
.stButton>button:hover{border-color:#3ddc84;color:#3ddc84;transform:translateX(3px)}
.pill{padding:.8rem 1rem;border-left:3px solid #3ddc84;background:#101812;border-radius:6px;margin:.4rem 0}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

PAGES = {"home": "Home", "plan": "Smart Planning", "source": "D2D Sourcing", "operate": "Godown & Alerts", "price": "Margin Matrix",
         "ledger": "Voice Ledger", "ambient": "Demand Engine", "syndicate": "Syndicate Pool"}
ss = st.session_state
ss.setdefault("page", "home"); ss.setdefault("shown", None); ss.setdefault("cart", {}); features.init_state()

def go(p):
    ss.page = p

# --- transition overlay (only when page actually changed) ---
if ss.shown != ss.page:
    st.markdown(f'<div class="wipe"><span>$ ./load {ss.page} --now</span></div>', unsafe_allow_html=True)
    ss.shown = ss.page

# --- top nav ---
cols = st.columns([1] + [1] * 7)
cols[0].markdown("### 🛒 **> NEWSTO**")
for c, (k, v) in zip(cols[1:], list(PAGES.items())[1:]):
    c.button(v, key=f"nav_{k}", on_click=go, args=(k,), type="primary" if ss.page == k else "secondary")
if ss.page != "home":
    st.button("← back to home", on_click=go, args=("home",))

def head(tag, title):
    st.markdown(f'<div class="tag">{tag}</div><div class="hero" style="font-size:2.2rem">{title}</div>', unsafe_allow_html=True)

# ================= HOME =================
if ss.page == "home":
    st.markdown('<div class="tag">FUTURE FORGE HACKATHON 2026 · V1.0 PROTOTYPE</div>'
                '<div class="hero">Your <b>Retail Co-Pilot</b><br><span class="type">From first idea to profitable shop.</span></div>'
                '<div class="steps"><span class="step">[ ] IDEA</span><span class="step">[ ] PLAN</span><span class="step">[ ] SOURCE</span>'
                '<span class="step">[ ] OPERATE</span><span class="step">[x] PROFIT</span></div>', unsafe_allow_html=True)
    cards = [("plan", "🗺️ Smart Planning", "Geo-Trend Mapper + Capital Sync. Stop guessing demand.", True),
             ("source", "🚚 D2D Sourcing", "Direct distributors. No middlemen. One-click restock.", True),
             ("operate", "📦 Godown & Alerts", "Multi-room stock + expiry and seasonal risk alerts.", True),
             ("price", "💰 Margin Matrix", "Optimal price + promo simulator before you launch.", True),
             ("ledger", "🎙️ Voice Ledger", "Say your sales. Books and stock update instantly.", True),
             ("ambient", "⛈️ Demand Engine", "Weather-aware spoilage alerts and restock surges.", True),
             ("syndicate", "🤝 Syndicate Pool", "Pool orders with nearby shops for bulk prices.", True),
             ("plans", "💳 Plans & Billing", "Freemium + paid SaaS tiers.", False),
             ("api", "🔌 Logistics API", "Partner integrations for delivery & fulfilment.", False)]
    for row in (cards[:3], cards[3:6], cards[6:9], cards[9:]):
        for col, (k, t, d, live) in zip(st.columns(3), row):
            with col:
                badge = '<span class="live">● LIVE DEMO</span>' if live else '<span class="soon">◌ COMING SOON</span>'
                st.markdown(f'<div class="card">{badge}<h4>{t}</h4><p>{d}</p></div>', unsafe_allow_html=True)
                if live:
                    st.button("Open →", key=f"open_{k}", on_click=go, args=(k,))
                else:
                    if st.button("Preview", key=f"open_{k}"):
                        st.toast(f"🚧 {t} is on the roadmap — not in this prototype.", icon="🚧")

# ================= PLAN =================
elif ss.page == "plan":
    head("FEATURE 01 · SMART PLANNING", "The day a new owner stops guessing.")
    a, b, c = st.columns(3)
    pin = a.selectbox("Shop pin-code", data.get_pincodes())
    typ = b.selectbox("Shop type", list(data.SHOP_RATE))
    sqft = c.slider("Shop size (sq ft)", 100, 1500, 350, 50)
    t = data.get_geo_trends(pin); cap = data.capital_sync(sqft, typ)
    l, r = st.columns([1.3, 1])
    with l:
        st.markdown("**Geo-Trend Mapper** · local demand score")
        st.bar_chart(t, color="#3ddc84")
    with r:
        st.markdown("**Capital Sync** · recommended budget")
        st.metric("Total starting capital", f"₹{cap['total']:,}")
        m1, m2, m3 = st.columns(3)
        m1.metric("Stock", f"₹{cap['stock']:,}"); m2.metric("Fixtures", f"₹{cap['fixtures']:,}"); m3.metric("Buffer", f"₹{cap['buffer']:,}")
    top, low = t.index[0], t.index[-1]
    st.markdown(f'<div class="pill">> Stock <b>{top}</b> over {low} — local demand favours it.<br>✓ Prevents dead stock from day one.</div>', unsafe_allow_html=True)

# ================= SOURCE =================
elif ss.page == "source":
    head("FEATURE 02 · D2D SOURCING HUB", "Distributor-to-Door. No middlemen.")
    cat = data.get_catalog()
    f = st.multiselect("Category", cat["Category"].unique(), default=list(cat["Category"].unique()))
    view = cat[cat["Category"].isin(f)].reset_index(drop=True)
    qty = {}
    for i, rw in view.iterrows():
        c1, c2, c3, c4 = st.columns([2.2, 1.6, 1.4, 1])
        c1.markdown(f"**{rw.Product}**  \n<span class='tag'>{rw.Distributor} ✔ verified</span>", unsafe_allow_html=True)
        c2.markdown(f"₹{rw['NewSto price']}  \n<span class='tag'><s>₹{rw['Middleman price']}</s> middleman</span>", unsafe_allow_html=True)
        c3.markdown(f"<span class='live'>save ₹{rw['Middleman price'] - rw['NewSto price']}/unit</span>", unsafe_allow_html=True)
        qty[rw.Product] = c4.number_input("qty", 0, 500, 0, key=f"q{i}", label_visibility="collapsed")
    saved = sum(q * (view.loc[view.Product == p, "Middleman price"].iat[0] - view.loc[view.Product == p, "NewSto price"].iat[0]) for p, q in qty.items())
    total = sum(q * view.loc[view.Product == p, "NewSto price"].iat[0] for p, q in qty.items())
    st.markdown(f'<div class="pill">Cart total <b>₹{total:,}</b> · you save <b>₹{saved:,}</b> vs middlemen</div>', unsafe_allow_html=True)
    if st.button("⚡ One-click bulk order", disabled=total == 0):
        with st.spinner("Contacting distributors..."):
            time.sleep(1)
        st.success(f"Order {data.place_order(qty)} placed!"); st.balloons()

# ================= OPERATE =================
elif ss.page == "operate":
    head("FEATURE 03 · OPERATIONS", "Track every shelf.")
    g = data.get_godown()
    crit = g[g["Status"].str.contains("CRITICAL")]
    k1, k2, k3 = st.columns(3)
    k1.metric("Godown rooms", g["Room"].nunique()); k2.metric("Units in stock", int(g["Qty"].sum())); k3.metric("Critical alerts", len(crit))
    tabs = st.tabs(["All"] + sorted(g["Room"].unique()))
    for tab, room in zip(tabs, ["All"] + sorted(g["Room"].unique())):
        with tab:
            st.dataframe(g if room == "All" else g[g["Room"] == room], use_container_width=True, hide_index=True)
    st.markdown("**Smart Risk Alerts**")
    for _, rw in crit.iterrows():
        st.error(f"EXPIRY: {rw.Item} ({rw.Qty} units) expires in {rw['Days to expiry']} days — discount or move now.")
    st.warning("WARN · Monsoon: elevate bulk pulses, secure food packaging.")

# ================= PRICE =================
elif ss.page == "price":
    head("FEATURE 03 · PRICING", "Price every item right.")
    a, b = st.columns(2)
    cost = a.number_input("Wholesale cost (₹)", 1.0, 5000.0, 78.0)
    mg = b.slider("Target margin %", 5, 60, 20)
    price = data.margin_price(cost, mg)
    st.metric("Optimal selling price", f"₹{price}", f"₹{round(price - cost, 2)} profit / unit")
    st.markdown("**Promo Simulator**")
    offer = st.radio("Offer", ["None", "Buy 1 Get 1", "10% off", "20% off"], horizontal=True)
    eff = {"None": price, "Buy 1 Get 1": price / 2, "10% off": price * .9, "20% off": price * .8}[offer]
    new_m = (eff - cost) / eff * 100
    c1, c2 = st.columns(2)
    c1.metric("Effective price / unit", f"₹{eff:.2f}"); c2.metric("Margin after offer", f"{new_m:.1f}%", f"{new_m - mg:.1f}% vs target")
    (st.error if new_m < 0 else st.warning if new_m < 8 else st.success)(
        "Loss-making offer — do NOT launch." if new_m < 0 else "Thin margin — risky." if new_m < 8 else "Offer is safe to run.")
elif ss.page == "ledger":
    features.page_ledger()
elif ss.page == "ambient":
    features.page_ambient()
elif ss.page == "syndicate":
    features.page_syndicate()
