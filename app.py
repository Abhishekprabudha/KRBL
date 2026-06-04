import os
import time
from pathlib import Path
from datetime import datetime, timedelta
import re
import hashlib

import numpy as np
import plotly.graph_objects as go
import streamlit as st

# ------------------------------------------------------------
# KRBL × AIonOS Streamlit Demo
# Inventory Replenishment Engine adapted to KRBL deck / 2-pager
# ------------------------------------------------------------

st.set_page_config(
    page_title="KRBL Inventory Replenishment Engine | AIonOS",
    page_icon="🌾",
    layout="wide",
)

st.markdown(
    """
    <style>
      .block-container {padding-top: 1.0rem; padding-bottom: 1.2rem;}
      .stMetric {padding: 6px 8px;}
      div[data-testid="stVerticalBlockBorderWrapper"] {padding: 10px;}
      .hero {
        padding: 18px 22px; border-radius: 18px;
        background: linear-gradient(110deg, #132743 0%, #0b5f69 58%, #0d8a8a 100%);
        color: white; margin-bottom: 12px;
      }
      .hero h1 {margin: 0; font-size: 2.0rem; letter-spacing: -0.02em;}
      .hero p {margin: 6px 0 0 0; opacity: 0.88; font-size: 1.0rem;}
      .tight-card {padding: 14px 16px; border-radius: 16px; border: 1px solid rgba(49,51,63,0.16); background: rgba(250,252,253,0.72);}
      .dark-card {padding: 14px 16px; border-radius: 16px; background: #132743; color: white;}
      .muted {opacity: 0.72;}
      .pill {display:inline-block; padding:5px 11px; border-radius:999px; border:1px solid rgba(49,51,63,0.18); margin: 2px 4px 2px 0;}
      .green-pill {display:inline-block; padding:5px 11px; border-radius:999px; background:#e7f8f6; color:#087f7a; font-weight:700; margin: 2px 4px 2px 0;}
      .small {font-size: 0.82rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <h1>🌾 AIonOS × KRBL | Agentic Inventory Replenishment Engine</h1>
      <p>Closed-loop paddy, rice, CNF and export replenishment intelligence aligned to KRBL's 45-day harvest window, 324-day inventory hold, 13 CNFs, 850+ dealers and 90+ export markets.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Video loading
# -----------------------------
VIDEO_DIR = Path("videos")
fallback_uploaded = Path("/mnt/data/3817769649-preview.mp4")
video_files = sorted([p for p in VIDEO_DIR.glob("*.mp4")]) if VIDEO_DIR.exists() else []
if not video_files and fallback_uploaded.exists():
    video_files = [fallback_uploaded]
if not video_files:
    st.warning("No MP4 found in /videos. The telemetry dashboard will still run. Add an MP4 to /videos for the live feed panel.")

# -----------------------------
# KRBL-specific baseline and SKU / node catalog
# -----------------------------
KRBL_BASELINE = {
    "revenue_cr": 5660,
    "annual_milling_mt": 1_300_000,
    "harvest_window_days": 45,
    "previous_harvest_window_days": 90,
    "inventory_hold_days": 324,
    "inventory_value_cr": 3000,
    "dealers": 850,
    "cnfs": 13,
    "export_markets": 90,
    "middle_east_export_exposure_pct": 61,
    "fy25_margin_pct": 12,
    "prior_margin_pct": 15,
}

KRBL_CATALOG = {
    "Paddy procurement pool | 45-day harvest window": {
        "node": "Mandi → Dhuri mill",
        "unit": "MT",
        "start_inventory": 148_000,
        "base_daily_demand": 3_900,
        "receipt_batch": 18_000,
        "target_hold_days": 294,
        "risk_note": "Buy-window compression creates high-cost paddy risk.",
    },
    "India Gate Classic | Domestic dealer replenishment": {
        "node": "13 CNFs → 850+ dealers",
        "unit": "MT",
        "start_inventory": 34_000,
        "base_daily_demand": 1_050,
        "receipt_batch": 4_600,
        "target_hold_days": 304,
        "risk_note": "Dealer blind spots create stockout and overstock risk.",
    },
    "Premium aged basmati | Export recovery lane": {
        "node": "Dhuri → Middle East / global distributors",
        "unit": "MT",
        "start_inventory": 41_500,
        "base_daily_demand": 1_250,
        "receipt_batch": 5_400,
        "target_hold_days": 300,
        "risk_note": "61% Middle East exposure needs faster export demand sensing.",
    },
    "New categories | Spices + rice bran oil": {
        "node": "Plant → CNF → dealer network",
        "unit": "cases",
        "start_inventory": 72_000,
        "base_daily_demand": 2_200,
        "receipt_batch": 8_000,
        "target_hold_days": 45,
        "risk_note": "SKU expansion adds complexity to a rice-led distribution layer.",
    },
}

# -----------------------------
# Sidebar controls
# -----------------------------
with st.sidebar:
    st.header("KRBL demo controls")
    default_autoplay = os.environ.get("KRBL_RENDER_DEMO") != "1"
    autoplay = st.toggle("Autoplay telemetry", value=default_autoplay)
    tick_ms = st.slider("Refresh speed (ms)", 150, 1500, 420, 10)

    st.divider()
    st.subheader("Live feed")
    if "video_idx" not in st.session_state:
        st.session_state.video_idx = 0
    if video_files:
        chosen = st.selectbox(
            "Pick a video",
            options=list(range(len(video_files))),
            format_func=lambda i: f"{i+1}. {video_files[i].name}",
            index=st.session_state.video_idx,
        )
        st.session_state.video_idx = chosen
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("⏮ Prev"):
                st.session_state.video_idx = (st.session_state.video_idx - 1) % len(video_files)
        with c2:
            if st.button("▶ Next"):
                st.session_state.video_idx = (st.session_state.video_idx + 1) % len(video_files)
        with c3:
            if st.button("🔁 Reset"):
                st.session_state.video_idx = 0
    else:
        st.caption("Add videos/*.mp4 to enable this selector.")

    st.divider()
    st.subheader("KRBL scenario pressure")
    harvest_pressure = st.slider("Harvest-window pressure", 0.0, 2.5, 1.4, 0.1, help="Models the 90 → 45 day procurement compression.")
    export_volatility = st.slider("Export demand volatility", 0.0, 2.5, 1.1, 0.1, help="Models Middle East and global distributor demand swings.")
    cnf_signal_quality = st.slider("CNF/dealer signal quality", 0.2, 1.0, 0.72, 0.02, help="Higher means cleaner replenishment signal from 13 CNFs and 850+ dealers.")
    lead_time_days = st.slider("Replenishment lead time (days)", 1, 21, 7, 1)
    safety_level = st.slider("Safety-stock guardrail", 0.0, 3.0, 1.4, 0.1)
    policy = st.selectbox("Policy", ["Dynamic release window", "Reorder point", "CNF rebalance"], index=0)

# -----------------------------
# Data generation
# -----------------------------
def stable_seed(*parts: str) -> int:
    key = "|".join(parts).encode("utf-8")
    return int(hashlib.md5(key).hexdigest()[:8], 16)


def make_krbl_series(seed: int, cfg: dict, n: int = 365, harvest_pressure: float = 1.4, export_volatility: float = 1.1, signal_quality: float = 0.72):
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    base_daily = float(cfg["base_daily_demand"])
    start_inventory = float(cfg["start_inventory"])
    batch = float(cfg["receipt_batch"])

    # Demand: seasonal rice demand + export volatility + harvest-window compression.
    seasonality = 0.16 * np.sin(2 * np.pi * t / 110) + 0.10 * np.sin(2 * np.pi * (t - 20) / 42)
    harvest_wave = harvest_pressure * 0.28 * np.maximum(0, np.sin(2 * np.pi * (t - 18) / 90))
    export_wave = export_volatility * 0.18 * np.maximum(0, np.sin(2 * np.pi * (t - 50) / 145))
    noise = rng.normal(0, (1.0 - signal_quality) * 0.16, size=n)
    demand = base_daily * (1 + seasonality + harvest_wave + export_wave + noise)
    demand = np.clip(demand, base_daily * 0.45, base_daily * 1.95)

    # Receipts / milling release: larger receipts during compressed harvest window, smaller CNF releases later.
    receipts = np.zeros(n)
    for k in range(18, n, 38):
        window_boost = 1.0 + harvest_pressure * (0.45 if k < 110 else 0.12)
        width = int(rng.integers(2, 6))
        receipt_qty = batch * window_boost * (0.82 + 0.45 * rng.random())
        receipts[k:k + width] += receipt_qty / width
    receipts += np.clip(rng.normal(0, batch * 0.015, size=n), 0, None)

    # Agent-driven transfers across 13 CNFs: not new supply, but inventory released to where demand is visible.
    rebalance = np.zeros(n)
    for k in range(45, n, 55):
        rebalance[k:k + 3] += batch * 0.20 * signal_quality / 3

    inventory = np.zeros(n)
    backlog = np.zeros(n)
    inventory[0] = start_inventory
    for i in range(1, n):
        inv = inventory[i - 1] - demand[i] + receipts[i] + rebalance[i]
        if inv < 0:
            backlog[i] = backlog[i - 1] + abs(inv)
            inv = 0
        else:
            backlog[i] = max(0, backlog[i - 1] - 0.35 * (receipts[i] + rebalance[i]))
        inventory[i] = inv

    return t, demand, inventory, receipts, rebalance, backlog


def predict_replenishment(demand, inventory, lead_time_days: int, safety_level: float, cfg: dict):
    window = min(60, len(demand))
    mu = float(np.mean(demand[-window:]))
    sigma = float(np.std(demand[-window:]))
    lead_time_demand = mu * lead_time_days
    safety_stock = safety_level * sigma * np.sqrt(max(lead_time_days, 1))
    rop = lead_time_demand + safety_stock
    inv_now = float(inventory[-1])
    days_to_rop = (inv_now - rop) / max(mu, 1e-6)
    days_to_rop = float(np.clip(days_to_rop, -30, 180))

    # KRBL target: reduce 324-day holding period by 20-30 days.
    current_hold = KRBL_BASELINE["inventory_hold_days"]
    target_hold = float(cfg["target_hold_days"])
    projected_hold = max(target_hold, current_hold - (20 + 10 * min(safety_level / 3.0, 1.0)))

    release_horizon = 21.0 if cfg["unit"] == "MT" else 10.0
    release_window_qty = max(0.0, inv_now - (rop + mu * release_horizon))
    rec_qty = max(0.0, rop + mu * 14 - inv_now)

    confidence = float(np.clip(74 + 12 * cnf_signal_quality - 3.5 * export_volatility, 52, 93))

    return {
        "avg_daily_demand": mu,
        "rop": float(rop),
        "days_to_rop": days_to_rop,
        "rec_qty": float(rec_qty),
        "release_window_qty": float(release_window_qty),
        "projected_hold": float(projected_hold),
        "confidence": confidence,
    }


def status_from_inventory(inv_now: float, rop: float, release_qty: float):
    if inv_now <= rop:
        return "ALERT"
    if inv_now <= rop * 1.25:
        return "WATCH"
    if release_qty > rop * 0.35:
        return "RELEASE WINDOW"
    return "NORMAL"

# -----------------------------
# Layout and selection
# -----------------------------
left, right = st.columns([1.18, 1.0], gap="large")

with left:
    st.subheader("🧾 KRBL replenishment scope")
    catalog_names = list(KRBL_CATALOG.keys())
    if "sku" not in st.session_state:
        st.session_state.sku = catalog_names[0]
    selection = st.selectbox("Select replenishment flow", catalog_names, index=catalog_names.index(st.session_state.sku))
    st.session_state.sku = selection
    cfg = KRBL_CATALOG[selection]

    st.markdown(
        f"""
        <div class="tight-card">
          <span class="green-pill">{cfg['node']}</span>
          <span class="pill"><b>Unit:</b> {cfg['unit']}</span>
          <span class="pill"><b>Baseline hold:</b> {KRBL_BASELINE['inventory_hold_days']} days</span>
          <span class="pill"><b>Target reduction:</b> −20–30 days</span><br/>
          <span class="muted small">{cfg['risk_note']}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Generate / reset cursor
current_video = video_files[st.session_state.video_idx] if video_files else Path("no-video")
seed = stable_seed(current_video.name, st.session_state.sku)
t, daily_demand, inventory, receipts, rebalance, backlog = make_krbl_series(
    seed,
    cfg=cfg,
    harvest_pressure=harvest_pressure,
    export_volatility=export_volatility,
    signal_quality=cnf_signal_quality,
)

if "cursor" not in st.session_state:
    st.session_state.cursor = 0
if st.session_state.get("last_key") != (current_video.name, st.session_state.sku):
    st.session_state.last_key = (current_video.name, st.session_state.sku)
    st.session_state.cursor = 0

cursor = int(np.clip(st.session_state.cursor, 0, len(t) - 1))
st.session_state.cursor = cursor
if autoplay:
    st.session_state.cursor = min(cursor + 2, len(t) - 1)
    time.sleep(tick_ms / 1000.0)
    st.rerun()

# Slice to current cursor
idx = cursor + 1
tt = t[:idx]
dd = daily_demand[:idx]
inv = inventory[:idx]
rec = receipts[:idx]
reb = rebalance[:idx]
bl = backlog[:idx]
pred = predict_replenishment(dd, inv, lead_time_days, safety_level, cfg)
inv_now = float(inv[-1])
rop = float(pred["rop"])
days_to_rop = float(pred["days_to_rop"])
release_qty = float(pred["release_window_qty"])
status = status_from_inventory(inv_now, rop, release_qty)
eta_dt = datetime.now() + timedelta(days=max(0.0, days_to_rop))
eta_str = eta_dt.strftime("%d %b %Y")
unit = cfg["unit"]

# -----------------------------
# GenBI rule-based query engine
# -----------------------------
def genbi_answer(q: str, cursor_now: int):
    ql = q.strip().lower()
    if not ql:
        return None, None

    flow = st.session_state.sku
    if ("inventory" in ql or "stock" in ql or "on hand" in ql) and ("current" in ql or "now" in ql):
        return f"[{flow}] Current on-hand inventory is **{inv_now:,.0f} {unit}**. State is **{status}** against ROP **{rop:,.0f} {unit}**.", None

    if "holding" in ql or "hold" in ql or "324" in ql:
        return f"KRBL baseline inventory holding is **324 days**. This demo projects **{pred['projected_hold']:.0f} days**, aligned to the KRBL target of **−20–30 days**.", None

    if "reorder" in ql or "rop" in ql:
        return f"[{flow}] Reorder point is **{rop:,.0f} {unit}** using **{lead_time_days} days** lead time and **{safety_level:.1f}x** safety guardrail.", None

    if ("when" in ql or "eta" in ql or "next" in ql) and ("replen" in ql or "reorder" in ql or "trigger" in ql):
        if days_to_rop <= 0:
            return f"[{flow}] Inventory is at/under ROP **now** → trigger replenishment immediately. Confidence **{pred['confidence']:.0f}%**.", None
        return f"[{flow}] Time to ROP is **{days_to_rop:.1f} days** → next replenishment trigger around **{eta_str}**.", None

    if "release" in ql or "rebalance" in ql or "cnf" in ql:
        return f"[{flow}] Agent recommends **{release_qty:,.0f} {unit}** as potential release / CNF rebalance quantity. Objective: reduce trapped inventory while protecting 98% service level.", None

    if "procurement" in ql or "cost" in ql:
        return "KRBL target outcome: **10–15% procurement cost reduction** through mandi + futures buy-window alerts before the 45-day harvest window closes.", None

    if "dealer" in ql or "service" in ql or "stockout" in ql:
        return "Dealer distribution target: live visibility across **850+ dealers** and **13 CNFs**, exception resolution **<10 min**, order accuracy **99%**, service level **98%**.", None

    m = re.search(r"last\s+(\d+)\s+days", ql)
    n = int(m.group(1)) if m else 90
    n = int(np.clip(n, 20, 240))
    s = max(0, cursor_now - n)

    def line_fig(x, y, name, ytitle):
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=x, y=y, mode="lines", name=name))
        fig.update_layout(height=265, margin=dict(l=10, r=10, t=10, b=10), xaxis_title="Demo day", yaxis_title=ytitle)
        return fig

    if "demand" in ql or "orders" in ql:
        fig = line_fig(t[s:cursor_now + 1], daily_demand[s:cursor_now + 1], "Demand / day", unit)
        return f"[{flow}] Showing last **{cursor_now - s}** demo days of demand.", fig

    if "inventory" in ql or "stock" in ql:
        fig = line_fig(t[s:cursor_now + 1], inventory[s:cursor_now + 1], "Inventory", unit)
        fig.add_hline(y=rop, line_width=1)
        return f"[{flow}] Showing last **{cursor_now - s}** demo days of inventory with ROP line.", fig

    if "receipt" in ql or "inflow" in ql or "replen" in ql:
        fig = line_fig(t[s:cursor_now + 1], receipts[s:cursor_now + 1], "Receipts / milling release", unit)
        return f"[{flow}] Showing last **{cursor_now - s}** demo days of receipts / replenishment inflow.", fig

    return "Ask me about current inventory, 324-day holding period, ROP, next replenishment ETA, CNF rebalance, procurement cost target, dealer service target, or show last N days demand/inventory/replenishment.", None

# -----------------------------
# Left pane
# -----------------------------
with left:
    st.subheader("🎥 Live warehouse / plant feed")
    if video_files:
        st.write(f"**Now playing:** {current_video.name}")
        st.video(str(current_video))
    else:
        st.info("Video placeholder. Add an MP4 in the videos folder before deploying on Streamlit Cloud.")

    st.markdown('<div class="tight-card">', unsafe_allow_html=True)
    st.markdown(f"### 📌 KRBL replenishment executive summary")
    a, b, c = st.columns(3)
    a.metric("State", status)
    b.metric("On-hand inventory", f"{inv_now:,.0f} {unit}")
    c.metric("ROP", f"{rop:,.0f} {unit}")

    d, e, f = st.columns(3)
    d.metric("Time to ROP", "NOW" if days_to_rop <= 0 else f"{days_to_rop:.1f} days")
    e.metric("Release / rebalance qty", f"{release_qty:,.0f} {unit}")
    f.metric("Projected hold", f"{pred['projected_hold']:.0f} days", delta=f"−{KRBL_BASELINE['inventory_hold_days'] - pred['projected_hold']:.0f} days")

    st.markdown(
        f"<span class='muted'>Policy: {policy} | Lead time: {lead_time_days} days | Confidence: {pred['confidence']:.0f}% | Target service level: 98%</span>",
        unsafe_allow_html=True,
    )
    st.markdown("#### 🔎 GenBI quick query")
    quick_q = st.text_input("Ask about KRBL inventory, ROP, 324-day hold, CNF rebalance…", placeholder="e.g., when is next replenishment trigger or show last 120 days inventory")
    st.markdown("</div>", unsafe_allow_html=True)

quick_answer, quick_fig = genbi_answer(quick_q, cursor) if quick_q else (None, None)
if quick_q and quick_answer:
    with left:
        st.info(quick_answer)
        if quick_fig is not None:
            st.plotly_chart(quick_fig, use_container_width=True)

# -----------------------------
# Right pane
# -----------------------------
with right:
    st.subheader("📟 KRBL operating telemetry")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Harvest window", f"{KRBL_BASELINE['harvest_window_days']} days", delta="90 → 45")
    k2.metric("Inventory hold", f"{KRBL_BASELINE['inventory_hold_days']} days")
    k3.metric("CNFs / dealers", f"{KRBL_BASELINE['cnfs']} / {KRBL_BASELINE['dealers']}+")
    k4.metric("Export markets", f"{KRBL_BASELINE['export_markets']}+")

    r1, r2, r3 = st.columns(3)
    r1.metric("Demand / day", f"{dd[-1]:,.0f} {unit}")
    r2.metric("Receipts / release", f"{rec[-1]:,.0f} {unit}")
    r3.metric("Backlog proxy", f"{float(bl[-1]):,.0f} {unit}")

    r4, r5, r6 = st.columns(3)
    r4.metric("Procurement target", "−10–15%")
    r5.metric("Order accuracy", "99%")
    r6.metric("Exception SLA", "<10 min")

    tabs = st.tabs(["📈 Live timeline", "🔮 Agent recommendation", "🧠 KRBL GenBI"])

    with tabs[0]:
        window = 150
        start = max(0, cursor - window)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=t[start:cursor+1], y=daily_demand[start:cursor+1], mode="lines", name=f"Demand / day ({unit})"))
        fig.add_trace(go.Scatter(x=t[start:cursor+1], y=inventory[start:cursor+1], mode="lines", name=f"Inventory ({unit})", yaxis="y2"))
        fig.add_trace(go.Scatter(x=t[start:cursor+1], y=receipts[start:cursor+1] + rebalance[start:cursor+1], mode="lines", name=f"Receipts + CNF rebalance ({unit})", yaxis="y3"))
        fig.add_hline(y=rop, line_width=1)
        fig.add_vline(x=t[cursor], line_width=2)
        fig.update_layout(
            height=385,
            margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            xaxis_title="Demo day",
            yaxis=dict(title="Demand"),
            yaxis2=dict(title="Inventory", overlaying="y", side="right"),
            yaxis3=dict(title="Receipts / rebalance", overlaying="y", side="right", position=0.97, showgrid=False),
        )
        st.plotly_chart(fig, use_container_width=True)
        cx, cy = st.columns([1, 2])
        with cx:
            if st.button("⏩ Advance 10 days"):
                st.session_state.cursor = min(st.session_state.cursor + 10, len(t) - 1)
                st.rerun()
        with cy:
            st.progress(int((cursor / (len(t) - 1)) * 100))

    with tabs[1]:
        c1, c2 = st.columns(2)
        with c1:
            gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=inv_now,
                number={"suffix": f" {unit}"},
                gauge={
                    "axis": {"range": [0, max(rop * 2.0, inv_now * 1.2, 1)]},
                    "bar": {"thickness": 0.35},
                    "threshold": {"line": {"width": 3}, "value": rop},
                },
                title={"text": "Inventory vs KRBL reorder point"},
            ))
            gauge.update_layout(height=280, margin=dict(l=10, r=10, t=50, b=10))
            st.plotly_chart(gauge, use_container_width=True)
        with c2:
            s = max(0, cursor - 150)
            dist = inventory[s:cursor+1] - rop
            risk = 100 * np.clip(1 - (dist / (rop + 1e-6)), 0, 1)
            risk_fig = go.Figure()
            risk_fig.add_trace(go.Scatter(x=t[s:cursor+1], y=risk, mode="lines", name="Stockout risk"))
            risk_fig.add_hline(y=40, line_width=1)
            risk_fig.add_hline(y=70, line_width=1)
            risk_fig.add_vline(x=t[cursor], line_width=2)
            risk_fig.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10), xaxis_title="Demo day", yaxis_title="Risk index", showlegend=False)
            st.plotly_chart(risk_fig, use_container_width=True)

        st.markdown("### Agent recommendation")
        m1, m2, m3 = st.columns(3)
        m1.metric("Next trigger", "Immediate" if days_to_rop <= 0 else eta_str)
        m2.metric("Replenish quantity", f"{pred['rec_qty']:,.0f} {unit}")
        m3.metric("Release / rebalance", f"{release_qty:,.0f} {unit}")

        st.markdown("### 90-day measurable outcomes")
        o1, o2, o3, o4 = st.columns(4)
        o1.metric("Procurement cost", "−10–15%")
        o2.metric("Holding period", "−20–30 days")
        o3.metric("Service level", "98%")
        o4.metric("Order accuracy", "99%")

        if status == "ALERT":
            st.error("🚨 Trigger replenishment immediately. Inventory is at or below KRBL ROP.")
        elif status == "WATCH":
            st.warning("⚠️ Prepare replenishment or CNF rebalance. Inventory is approaching ROP.")
        elif status == "RELEASE WINDOW":
            st.info("🔁 Dynamic release window detected. Agent can release inventory / rebalance CNFs while protecting 98% service level.")
        else:
            st.success("✅ Normal operations. No near-term stockout trigger predicted.")

    with tabs[2]:
        st.markdown("### 💬 KRBL GenBI query")
        st.caption("Rule-based/offline for GitHub + Streamlit deployment. Can be upgraded to LLM-backed GenBI later.")
        q = st.text_input("Your question", placeholder="e.g., What is KRBL's current stock and holding-period target?")
        ans, fig = genbi_answer(q, cursor) if q else (None, None)
        if ans:
            st.info(ans)
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True)

st.caption("AIonOS × KRBL demo | No ERP replacement | MCP connector concept | Built for Streamlit deployment")
