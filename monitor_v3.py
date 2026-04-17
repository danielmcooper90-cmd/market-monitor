# ============================================================
# MARKET MONITOR v3 — Hierarchical Drill-Down
# USD Down-Cycle / RoW / Hard Assets tracker
#
# ARCHITECTURE:
#   Tab 0 — Command Centre  (thesis status, regime signals)
#   Tab 1 — Cross-Asset     (ranked returns, asset class quilt — ph2)
#   Tab 2 — Equities        (global map → region → sector → stock)
#   Tab 3 — Fixed Income    (yield curves, credit spreads)
#   Tab 4 — Commodities     (energy, metals, agri, ratios)
#   Tab 5 — FX              (G10 + SGD scorecard)
#   Tab 6 — Macro           (economic calendar shell)
#   Tab 7 — Blotter         (trade log + dividend tracker)
#
# HOW TO RUN:
#   conda activate my_quant_lab
#   streamlit run monitor_v3.py
# ============================================================

import io
import os
import re
import datetime
import pandas as pd
import numpy as np
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="Market Monitor v3",
    layout="wide",
    page_icon="⬡",
    initial_sidebar_state="collapsed",
)

# ============================================================
# CUSTOM CSS — terminal-grade dark theme
# ============================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
    background-color: #080c10;
    color: #c9d1d9;
}

/* Tab bar */
.stTabs [data-baseweb="tab-list"] {
    gap: 0px;
    background: #0d1117;
    border-bottom: 1px solid #1e2a38;
    padding: 0 16px;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #4a5568;
    padding: 12px 20px;
    border-bottom: 2px solid transparent;
    margin-bottom: -1px;
}
.stTabs [aria-selected="true"] {
    color: #58a6ff !important;
    border-bottom: 2px solid #58a6ff !important;
    background: transparent !important;
}
.stTabs [data-baseweb="tab-panel"] {
    padding-top: 20px;
}

/* Metrics */
[data-testid="metric-container"] {
    background: #0d1117;
    border: 1px solid #1e2a38;
    border-radius: 4px;
    padding: 12px 16px;
}
[data-testid="metric-container"] label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #4a5568;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 22px;
    font-weight: 600;
    color: #e6edf3;
}

/* Dataframes */
[data-testid="stDataFrame"] {
    border: 1px solid #1e2a38;
}

/* Expanders */
[data-testid="stExpander"] {
    border: 1px solid #1e2a38;
    border-radius: 4px;
    background: #0d1117;
}

/* Section headers */
h1 { font-family: 'IBM Plex Mono', monospace; font-size: 18px; font-weight: 600; letter-spacing: 0.05em; color: #e6edf3; }
h2 { font-family: 'IBM Plex Mono', monospace; font-size: 14px; font-weight: 500; letter-spacing: 0.08em; text-transform: uppercase; color: #58a6ff; margin-top: 24px; }
h3 { font-family: 'IBM Plex Mono', monospace; font-size: 12px; font-weight: 500; letter-spacing: 0.1em; text-transform: uppercase; color: #4a5568; }

/* Signal badges */
.signal-on  { background:#0d2818; border:1px solid #238636; color:#3fb950; padding:4px 12px; border-radius:3px; font-family:'IBM Plex Mono',monospace; font-size:11px; font-weight:600; }
.signal-off { background:#2d1111; border:1px solid #6e1515; color:#f85149; padding:4px 12px; border-radius:3px; font-family:'IBM Plex Mono',monospace; font-size:11px; font-weight:600; }
.signal-warn{ background:#2d2211; border:1px solid #9e6a03; color:#d29922; padding:4px 12px; border-radius:3px; font-family:'IBM Plex Mono',monospace; font-size:11px; font-weight:600; }

/* Divider */
hr { border-color: #1e2a38; margin: 20px 0; }

/* Sidebar */
[data-testid="stSidebar"] { background: #080c10; border-right: 1px solid #1e2a38; }

/* Buttons */
.stButton button {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    letter-spacing: 0.05em;
    background: #0d1117;
    border: 1px solid #30363d;
    color: #8b949e;
}
.stButton button:hover { border-color: #58a6ff; color: #58a6ff; }

/* Select / multiselect */
[data-baseweb="select"] { font-family: 'IBM Plex Mono', monospace; font-size: 12px; }

/* Caption */
.stCaption { font-family: 'IBM Plex Mono', monospace; font-size: 10px; color: #4a5568; }

/* Status banner */
.status-banner {
    background: #0d1117;
    border: 1px solid #1e2a38;
    border-left: 3px solid #58a6ff;
    padding: 10px 16px;
    margin-bottom: 16px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    color: #8b949e;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# UNIVERSE — imported from config.py
# To add/remove tickers, groups, or ratios: edit config.py only.
# ============================================================

from config import (
    UNIVERSE,
    FX_PAIRS,
    MACRO_RATIOS,
    CROSS_ASSET,
    THESIS_SIGNALS,
    KNOWN_DIFFICULT,
    all_tickers as _all_tickers_fn,
    tickers_for,
    flat_groups,
)

# ── Derived flat lists used throughout the app
EQUITY_GROUPS  = flat_groups()
_all_eq        = tickers_for("Equities")
_fi_tickers    = tickers_for("Fixed Income")
_cmd_tickers   = tickers_for("Commodities")
_real_tickers  = tickers_for("Real Assets")
_crypto        = tickers_for("Crypto")

# Yield curve ETF proxies (subset of Fixed Income universe)
YIELD_CURVE = {
    "US": {"2Y": "SHY", "3-7Y": "IEI", "7-10Y": "IEF", "10-20Y": "TLH", "20Y+": "TLT", "TIPS": "TIP"},
    "Credit": {"IG": "LQD", "HY": "HYG", "EM": "EMB"},
}

# ============================================================
# GLOBAL SETTINGS — sidebar
# ============================================================

with st.sidebar:
    st.markdown("### ⚙️ Settings")
    start_date = st.date_input("History start", value=pd.Timestamp("2020-01-01"))
    sort_by    = st.selectbox("Default sort", ["MTD %", "YTD %", "Daily %", "1YR %"], index=0)
    st.divider()
    st.markdown("### 📓 Thesis")
    st.markdown("""
**Crescat / Tavi Costa — USD Down-Cycle**

USD weakens → RoW / EM / Hard Assets outperform US equities.

**Confirmation (all 3 needed):**
1. UUP falling — USD weakening
2. TIP stable/rising — real yields falling
3. DBC rising — commodities bid

*Higher-highs on DXY → reduce exposure.*
    """)

# ============================================================
# DATA LOADING
# ============================================================

@st.cache_data(ttl=300)
def load_prices(tickers, start):
    """Batch download — significantly faster than per-ticker loop."""
    try:
        raw = yf.download(
            list(tickers),
            start=str(start),
            progress=False,
            auto_adjust=True,
            threads=True,
        )
        if isinstance(raw.columns, pd.MultiIndex):
            df = raw["Close"].copy()
        else:
            df = raw[["Close"]].copy()
        df.index = pd.to_datetime(df.index)
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        failed = [t for t in tickers if t not in df.columns]
        return df.sort_index(), failed
    except Exception as e:
        return pd.DataFrame(), list(tickers)


@st.cache_data(ttl=300)
def load_fx(start):
    fx_data = {}
    for ccy, info in FX_PAIRS.items():
        try:
            raw = yf.download(info["ticker"], start=str(start), progress=False, auto_adjust=True)["Close"].squeeze()
            raw.index = pd.to_datetime(raw.index)
            if raw.index.tz is not None:
                raw.index = raw.index.tz_localize(None)
            fx_data[ccy] = (1 / raw) if info["invert"] else raw
        except Exception:
            pass
    return fx_data


@st.cache_data(ttl=86400)
def load_names(tickers):
    names = {}
    for t in tickers:
        try:
            info  = yf.Ticker(t).info
            names[t] = info.get("longName") or info.get("shortName") or t
        except Exception:
            names[t] = t
    return names


# ── Collect all unique tickers across the full universe
_ratio_t      = list(dict.fromkeys(t for pair in MACRO_RATIOS.values() for t in pair))
_cross_t      = list(CROSS_ASSET.keys())
_yield_t      = list(dict.fromkeys(t for sub in YIELD_CURVE.values() for t in sub.values()))
_universe_all = _all_tickers_fn()
fetch_tickers = list(dict.fromkeys(_universe_all + _ratio_t + _cross_t + _yield_t))

with st.spinner("Loading prices…"):
    prices, failed_tickers = load_prices(tuple(fetch_tickers), start_date)

with st.spinner("Loading FX…"):
    fx_data = load_fx(start_date)

with st.spinner("Loading ticker names…"):
    loaded_tickers = [t for t in fetch_tickers if t in prices.columns]
    ticker_names   = load_names(tuple(loaded_tickers))

# ============================================================
# METRICS HELPERS
# ============================================================

def safe_idx(s):
    s = s.copy()
    s.index = pd.to_datetime(s.index)
    if s.index.tz is not None:
        s.index = s.index.tz_localize(None)
    return s

def pct_from(s, dt):
    s = safe_idx(s.dropna())
    s2 = s[s.index >= pd.Timestamp(dt)]
    if s.empty or s2.empty:
        return float("nan")
    return (s.iloc[-1] / s2.iloc[0]) - 1

def pct_1yr(s):
    s = safe_idx(s.dropna())
    if len(s) < 2:
        return float("nan")
    s2 = s[s.index >= s.index[-1] - pd.Timedelta(days=365)]
    if s2.empty:
        return float("nan")
    return (s.iloc[-1] / s2.iloc[0]) - 1

def drawdown(s):
    s = s.dropna()
    if s.empty:
        return float("nan")
    return float(((s - s.cummax()) / s.cummax()).iloc[-1])

def ma(s, n):
    return s.rolling(n).mean()

def above_ma(s, n):
    """Return True/False whether last price is above MA(n)."""
    if len(s.dropna()) < n:
        return None
    return float(s.dropna().iloc[-1]) > float(ma(s.dropna(), n).iloc[-1])

def build_table(tickers, years=None):
    if prices.empty:
        return pd.DataFrame()
    px = prices.copy()
    px.index = pd.to_datetime(px.index)
    last_dt   = px.index.max()
    mtd_start = pd.Timestamp(year=last_dt.year, month=last_dt.month, day=1)
    ytd_start = pd.Timestamp(year=last_dt.year, month=1, day=1)
    rows = []
    for t in tickers:
        if t not in px.columns:
            continue
        s = px[t].dropna()
        if s.empty:
            continue
        row = {
            "Ticker":   t,
            "Name":     ticker_names.get(t, t),
            "Last":     round(float(s.iloc[-1]), 2),
            "Daily %":  pct_from(s, s.index[-2]) if len(s) > 1 else float("nan"),
            "MTD %":    pct_from(s, mtd_start),
            "YTD %":    pct_from(s, ytd_start),
            "1YR %":    pct_1yr(s),
            "Drawdown": drawdown(s),
            "vs MA200": "▲" if above_ma(s, 200) else ("▼" if above_ma(s, 200) is False else "—"),
        }
        if years:
            for y in years:
                s_yr  = s.loc[:f"{y}-12-31"]
                s_pre = s.loc[:f"{y-1}-12-31"]
                row[f"{y}"] = (s_yr.iloc[-1] / s_pre.iloc[-1]) - 1 if (not s_yr.empty and not s_pre.empty) else float("nan")
        rows.append(row)
    return pd.DataFrame(rows).set_index("Ticker")

def style_pct_table(df, pct_cols, dd_cols=None):
    fmt = {"Last": "{:.2f}"}
    fmt.update({c: "{:.2%}" for c in pct_cols if c in df.columns})
    if dd_cols:
        fmt.update({c: "{:.2%}" for c in dd_cols if c in df.columns})
    styled = df.style.format(fmt, na_rep="—")
    if pct_cols:
        cols_present = [c for c in pct_cols if c in df.columns]
        if cols_present:
            styled = styled.background_gradient(subset=cols_present, cmap="RdYlGn", vmin=-0.15, vmax=0.15)
    if dd_cols:
        dd_present = [c for c in dd_cols if c in df.columns]
        if dd_present:
            styled = styled.background_gradient(subset=dd_present, cmap="RdYlGn_r", vmin=-0.30, vmax=0.0)
    return styled

PLOTLY_LAYOUT = dict(
    paper_bgcolor="#0d1117",
    plot_bgcolor="#0d1117",
    font=dict(color="#8b949e", size=10, family="IBM Plex Mono"),
    xaxis=dict(gridcolor="#1e2a38", showgrid=True, zeroline=False),
    yaxis=dict(gridcolor="#1e2a38", showgrid=True, zeroline=False),
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.01, bgcolor="rgba(0,0,0,0)", font=dict(size=9)),
    margin=dict(l=10, r=10, t=40, b=10),
)

@st.cache_data(ttl=300)
def load_ohlcv(ticker, start):
    """Fetch full OHLCV data for a single ticker."""
    try:
        df = yf.download(ticker, start=str(start), progress=False, auto_adjust=True)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df.index = pd.to_datetime(df.index)
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        return df.sort_index()
    except Exception:
        return pd.DataFrame()

def ohlcv_chart(ticker, height=400, ma_fast=20, ma_slow=50, show_volume=True):
    """
    Candlestick chart with dual MAs and optional volume on secondary axis.
    Uses go.Candlestick + go.Bar with yaxis2.
    """
    df = load_ohlcv(ticker, start_date)
    if df.empty or not all(c in df.columns for c in ["Open", "High", "Low", "Close"]):
        return None

    name = ticker_names.get(ticker, ticker)
    ytd_ret = pct_from(df["Close"], pd.Timestamp(start_date))
    ret_col = "#3fb950" if ytd_ret >= 0 else "#f85149"
    arr     = "▲" if ytd_ret >= 0 else "▼"

    row_heights = [0.75, 0.25] if show_volume and "Volume" in df.columns else [1.0]
    rows        = 2 if (show_volume and "Volume" in df.columns) else 1

    fig = make_subplots(
        rows=rows, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        row_heights=row_heights,
    )

    # ── Candlesticks
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"], high=df["High"],
        low=df["Low"],   close=df["Close"],
        name="OHLC",
        increasing=dict(line=dict(color="#3fb950", width=1), fillcolor="#1a3a22"),
        decreasing=dict(line=dict(color="#f85149", width=1), fillcolor="#3a1a1a"),
        hovertext=[
            f"O: {o:.2f}  H: {h:.2f}  L: {l:.2f}  C: {c:.2f}"
            for o, h, l, c in zip(df["Open"], df["High"], df["Low"], df["Close"])
        ],
        hoverinfo="x+text",
    ), row=1, col=1)

    # ── Fast MA
    if len(df) >= ma_fast:
        mf = df["Close"].rolling(ma_fast).mean()
        fig.add_trace(go.Scatter(
            x=mf.index, y=mf, name=f"MA{ma_fast}",
            line=dict(color="#58a6ff", width=1.2),
            hovertemplate=f"MA{ma_fast}: %{{y:.2f}}<extra></extra>",
        ), row=1, col=1)

    # ── Slow MA
    if len(df) >= ma_slow:
        ms = df["Close"].rolling(ma_slow).mean()
        fig.add_trace(go.Scatter(
            x=ms.index, y=ms, name=f"MA{ma_slow}",
            line=dict(color="#f87171", width=1.4, dash="dash"),
            hovertemplate=f"MA{ma_slow}: %{{y:.2f}}<extra></extra>",
        ), row=1, col=1)

    # ── Volume bars
    if show_volume and "Volume" in df.columns and rows == 2:
        vol_colors = [
            "#3fb950" if c >= o else "#f85149"
            for c, o in zip(df["Close"], df["Open"])
        ]
        fig.add_trace(go.Bar(
            x=df.index, y=df["Volume"],
            name="Volume",
            marker=dict(color=vol_colors, opacity=0.5, line=dict(width=0)),
            hovertemplate="Vol: %{y:,.0f}<extra></extra>",
        ), row=2, col=1)

    fig.update_layout(
        **{**PLOTLY_LAYOUT,
           "height": height,
           "title": dict(
               text=f"<b>{ticker}</b>  {name[:40]}  "
                    f"<span style='color:{ret_col};font-size:10px'>{arr} {ytd_ret*100:.1f}% since {start_date}</span>",
               font=dict(size=12, color="#c9d1d9"),
           ),
           "xaxis_rangeslider_visible": False,
        }
    )
    fig.update_xaxes(gridcolor="#1e2a38", showgrid=True)
    fig.update_yaxes(gridcolor="#1e2a38", showgrid=True)
    return fig


def price_chart(ticker, height=300, ma_fast=50, ma_slow=200):
    """Line chart fallback (used for ratio overlays and FX)."""
    if ticker not in prices.columns:
        return None
    s    = prices[ticker].dropna()
    name = ticker_names.get(ticker, ticker)
    fig  = go.Figure()
    fig.add_trace(go.Scatter(x=s.index, y=s, name="Price",
        line=dict(color="#58a6ff", width=1.8),
        hovertemplate="%{x|%d %b %Y}<br>$%{y:.2f}<extra></extra>"))
    if len(s) >= ma_fast:
        mf = ma(s, ma_fast)
        fig.add_trace(go.Scatter(x=mf.index, y=mf, name=f"MA{ma_fast}",
            line=dict(color="#fbbf24", width=1, dash="dot")))
    if len(s) >= ma_slow:
        ms_ = ma(s, ma_slow)
        fig.add_trace(go.Scatter(x=ms_.index, y=ms_, name=f"MA{ma_slow}",
            line=dict(color="#f87171", width=1, dash="dash")))
        fig.add_trace(go.Scatter(x=s.index, y=s, fill=None, mode="lines",
            line=dict(color="rgba(0,0,0,0)"), showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=ms_.index, y=ms_, fill="tonexty",
            fillcolor="rgba(88,166,255,0.05)", mode="none", showlegend=False, hoverinfo="skip"))
    ytd_ret = pct_from(s, pd.Timestamp(start_date))
    col     = "#3fb950" if ytd_ret >= 0 else "#f85149"
    arr     = "▲" if ytd_ret >= 0 else "▼"
    layout  = {**PLOTLY_LAYOUT,
        "height": height,
        "title": dict(text=f"<b>{ticker}</b>  <span style='color:{col};font-size:10px'>{arr} {ytd_ret*100:.1f}%</span>",
                      font=dict(size=12, color="#c9d1d9"))}
    fig.update_layout(**layout)
    return fig

def ratio_chart(num, den, label, height=280):
    if num not in prices.columns or den not in prices.columns:
        return None
    ratio = (prices[num] / prices[den]).dropna()
    ma200 = ma(ratio, 200)
    fig   = go.Figure()
    fig.add_trace(go.Scatter(x=ratio.index, y=ratio, name=label,
        line=dict(color="#c9d1d9", width=1.5),
        hovertemplate="%{x|%d %b %Y}<br>%{y:.4f}<extra></extra>"))
    if len(ratio) >= 200:
        fig.add_trace(go.Scatter(x=ratio.index, y=ratio, fill=None, mode="lines",
            line=dict(color="rgba(0,0,0,0)"), showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=ma200.index, y=ma200, fill="tonexty",
            fillcolor="rgba(63,185,80,0.07)", mode="none", showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=ma200.index, y=ma200, name="MA200",
            line=dict(color="#3fb950", width=1, dash="dash")))
    layout = {**PLOTLY_LAYOUT, "height": height,
        "title": dict(text=f"<b>{label}</b>", font=dict(size=11, color="#c9d1d9"))}
    fig.update_layout(**layout)
    return fig


# ============================================================
# PAGE HEADER
# ============================================================

c_title, c_data = st.columns([6, 2])
with c_title:
    st.markdown("# MARKET MONITOR")
with c_data:
    if not prices.empty:
        st.caption(f"Data as of {prices.index.max().date()}  ·  {len(prices.columns)} tickers  ·  TTL 5min")

# ── Missing ticker warning (compact)
missing_unexpected = [t for t in fetch_tickers if t not in prices.columns and t not in KNOWN_DIFFICULT]
if missing_unexpected:
    with st.expander(f"⚠️ {len(missing_unexpected)} unexpected failures", expanded=False):
        st.error(", ".join(missing_unexpected))

# ============================================================
# MAIN TABS
# ============================================================

tab_cmd, tab_cross, tab_eq, tab_fi, tab_cmd_, tab_fx, tab_macro, tab_blotter = st.tabs([
    "⬡ COMMAND",
    "◈ CROSS-ASSET",
    "▦ EQUITIES",
    "⊟ FIXED INCOME",
    "◆ COMMODITIES",
    "◉ FX",
    "◷ MACRO",
    "⊞ BLOTTER",
])

# ════════════════════════════════════════════════════════════
# TAB 0 — COMMAND CENTRE
# ════════════════════════════════════════════════════════════

with tab_cmd:

    st.markdown("## Thesis Status")

    if not prices.empty:
        thesis_cols = st.columns(4)
        thesis_ok   = 0
        thesis_total = len(THESIS_SIGNALS)

        for i, (tkr, meta) in enumerate(THESIS_SIGNALS.items()):
            with thesis_cols[i]:
                if tkr not in prices.columns:
                    st.markdown(f'<span class="signal-warn">— NO DATA<br>{meta["label"]}</span>', unsafe_allow_html=True)
                    continue
                s      = prices[tkr].dropna()
                ytd    = pct_from(s, pd.Timestamp(start_date))
                mtd    = pct_from(s, pd.Timestamp(year=s.index.max().year, month=s.index.max().month, day=1))
                ma200  = above_ma(s, 200)
                # For UUP: falling is thesis-confirming. For others: rising is.
                if meta["bearish_is_good"]:
                    on = (mtd < 0) and (ma200 is False)
                else:
                    on = (mtd > 0) and (ma200 is True)
                if on:
                    thesis_ok += 1
                    cls = "signal-on";  icon = "✅"
                elif ma200 is None:
                    cls = "signal-warn"; icon = "⚠️"
                else:
                    cls = "signal-off"; icon = "❌"
                direction = "FALLING" if mtd < 0 else "RISING"
                ma_label  = "ABOVE MA200" if ma200 else "BELOW MA200"
                st.markdown(
                    f'<div class="{cls}">{icon} {meta["label"]}<br>'
                    f'<span style="font-size:10px;opacity:0.7">{direction} {mtd*100:.1f}% MTD · {ma_label}</span></div>',
                    unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Overall thesis verdict
        if thesis_ok == thesis_total:
            st.success(f"✅ THESIS CONFIRMED — all {thesis_total}/{thesis_total} signals aligned. Act with conviction.")
        elif thesis_ok >= 2:
            st.warning(f"⚠️ THESIS PARTIAL — {thesis_ok}/{thesis_total} signals aligned. Monitor closely.")
        else:
            st.error(f"❌ THESIS INACTIVE — {thesis_ok}/{thesis_total} signals. Reduce exposure, don't average in.")

    st.markdown("---")
    st.markdown("## Risk Rules")

    rule_cols = st.columns(3)
    with rule_cols[0]:
        st.markdown("**Rule 1 — Max Drawdown**")
        st.caption("Any sleeve hits −20% peak-to-trough AND thesis not confirming → cut by ⅓")
    with rule_cols[1]:
        st.markdown("**Rule 2 — Concentration**")
        st.caption("Any sleeve exceeds 25% of portfolio due to outperformance → rebalance down")
    with rule_cols[2]:
        st.markdown("**Rule 3 — Wrong-Way Warning**")
        st.caption("DXY up + equities risk-off + commodities down simultaneously → reduce, don't add")

    st.markdown("---")
    st.markdown("## Watchlist Snapshot")

    # Quick scorecard across all loaded tickers
    snapshot_tickers = [t for t in _all_eq if t in prices.columns]
    snap_table = build_table(snapshot_tickers)
    if not snap_table.empty:
        c1, c2, c3, c4, c5 = st.columns(5)
        avg_mtd = snap_table["MTD %"].mean()
        avg_ytd = snap_table["YTD %"].mean()
        adv     = int((snap_table["MTD %"] > 0).sum())
        dec     = int((snap_table["MTD %"] < 0).sum())
        worst_t = snap_table["Drawdown"].idxmin()
        worst_d = snap_table["Drawdown"].min()
        with c1: st.metric("Avg MTD",       f"{avg_mtd*100:.1f}%")
        with c2: st.metric("Avg YTD",       f"{avg_ytd*100:.1f}%")
        with c3: st.metric("Advancing MTD", f"{adv}")
        with c4: st.metric("Declining MTD", f"{dec}")
        with c5: st.metric("Worst Drawdown",f"{worst_d*100:.1f}%  {worst_t}")

    st.markdown("---")
    st.markdown("## Broad Market Overview")
    st.caption("Candlestick overview across key regional benchmarks and macro indicators · Uses last 6 months of data")

    # ── Region groups for the broad market grid
    BROAD_MARKET_GROUPS = {
        "US Equities": ["SPY", "QQQ", "IWM", "RSP"],
        "Global / EM":  ["ACWX", "EEM", "EFA", "VGK", "EWJ"],
        "Rates / Credit": ["TLT", "IEF", "HYG", "TIP"],
        "Hard Assets":  ["GLD", "DBC", "SLV", "USO"],
        "Thesis Signals": ["UUP", "TIP", "DBC", "GLD"],
    }

    cmd_grp_sel = st.selectbox(
        "Group",
        list(BROAD_MARKET_GROUPS.keys()),
        key="cmd_bm_group",
    )
    bm_tickers = [t for t in BROAD_MARKET_GROUPS[cmd_grp_sel] if t in prices.columns]

    bm_ma_fast = st.select_slider("Fast MA", options=[10, 20, 50], value=20, key="bm_maf")
    bm_ma_slow = st.select_slider("Slow MA", options=[50, 100, 200], value=50, key="bm_mas")
    bm_show_vol = st.checkbox("Show volume", value=False, key="bm_vol")

    if bm_tickers:
        bm_cols = st.columns(2)
        for i, t in enumerate(bm_tickers):
            fig = ohlcv_chart(t, height=340, ma_fast=bm_ma_fast, ma_slow=bm_ma_slow, show_volume=bm_show_vol)
            if fig:
                with bm_cols[i % 2]:
                    st.plotly_chart(fig, use_container_width=True)

# ════════════════════════════════════════════════════════════
# TAB 1 — CROSS-ASSET
# ════════════════════════════════════════════════════════════

with tab_cross:

    st.markdown("## Cross-Asset Returns")

    # Period selector
    period = st.radio("Period", ["Daily %", "MTD %", "YTD %", "1YR %"], horizontal=True, index=2)

    cross_tickers = [t for t in CROSS_ASSET.keys() if t in prices.columns]
    cross_table   = build_table(cross_tickers)

    if not cross_table.empty and period in cross_table.columns:

        # ── Ranked waterfall bar chart (Image 1 style)
        plot_df = cross_table[[period]].dropna().copy()
        plot_df["Label"] = [CROSS_ASSET.get(t, t) for t in plot_df.index]
        plot_df = plot_df.sort_values(period, ascending=True)

        colors = ["#3fb950" if v >= 0 else "#f85149" for v in plot_df[period]]

        fig = go.Figure(go.Bar(
            x=plot_df[period] * 100,
            y=plot_df["Label"],
            orientation="h",
            marker=dict(color=colors, line=dict(width=0)),
            text=[f"{v*100:.1f}%" for v in plot_df[period]],
            textposition="outside",
            textfont=dict(size=9, color="#8b949e", family="IBM Plex Mono"),
            hovertemplate="%{y}<br>%{x:.2f}%<extra></extra>",
        ))
        fig.update_layout(
            **{**PLOTLY_LAYOUT,
               "height": max(400, len(plot_df) * 26),
               "title": dict(text=f"<b>Cross-Asset Ranked Returns — {period}</b>",
                             font=dict(size=13, color="#c9d1d9")),
               "xaxis": dict(**PLOTLY_LAYOUT["xaxis"], ticksuffix="%"),
               "yaxis": dict(gridcolor="#1e2a38"),
               "margin": dict(l=10, r=80, t=50, b=10),
            })
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        # ── Table with all periods side by side
        st.markdown("## Returns Table")
        pct_cols = ["Daily %", "MTD %", "YTD %", "1YR %"]
        display  = cross_table[["Name"] + pct_cols + ["Drawdown"]].copy()
        display  = display.sort_values(period, ascending=False)
        styled   = style_pct_table(display, pct_cols, ["Drawdown"])
        st.dataframe(styled, use_container_width=True)

    else:
        st.info("No cross-asset data loaded.")

    st.markdown("---")
    st.markdown("## Macro Ratio Charts")
    st.caption("Rising = numerator outperforming denominator · Green shading = above MA200")

    ratio_cols = st.columns(2)
    for i, (label, (num, den)) in enumerate(MACRO_RATIOS.items()):
        fig = ratio_chart(num, den, label)
        if fig:
            with ratio_cols[i % 2]:
                st.plotly_chart(fig, use_container_width=True)


# ════════════════════════════════════════════════════════════
# TAB 2 — EQUITIES
# Drill-down: Asset Class → Geography → Sleeve → Chart/Table
# ════════════════════════════════════════════════════════════

with tab_eq:

    st.markdown("## Equities")

    # ── Top-level view selector
    eq_view = st.radio(
        "View",
        ["Returns Table", "Candle Charts", "Ratio Charts"],
        horizontal=True,
        key="eq_view_radio",
    )

    st.markdown("---")

    # ── Geography / sleeve selector — mirrors UNIVERSE hierarchy
    # Level 1: Region
    eq_regions = list(UNIVERSE["Equities"].keys())  # USA, Europe, Asia-Pacific, Emerging Markets, Global
    sel_region = st.selectbox("Region", ["All"] + eq_regions, key="eq_region")

    # Level 2: Group within region (dynamic based on region selection)
    if sel_region == "All":
        available_groups = {
            f"{reg}  ›  {grp}": tickers
            for reg, reg_val in UNIVERSE["Equities"].items()
            for grp, tickers in reg_val.items()
        }
    else:
        available_groups = {
            grp: tickers
            for grp, tickers in UNIVERSE["Equities"][sel_region].items()
        }

    group_keys   = list(available_groups.keys())
    default_grps = group_keys[:3] if len(group_keys) >= 3 else group_keys
    sel_groups   = st.multiselect("Sleeves", group_keys, default=default_grps, key="eq_sleeves")

    # ── Collect selected tickers
    sel_tickers = list(dict.fromkeys(
        t for grp in sel_groups
        for t in available_groups.get(grp, [])
        if t in prices.columns
    ))

    if not sel_tickers:
        st.info("Select at least one sleeve above.")
        st.stop()

    # ════════════════════════════
    # VIEW: RETURNS TABLE
    # ════════════════════════════
    if eq_view == "Returns Table":

        pct_cols = ["Daily %", "MTD %", "YTD %", "1YR %"]

        for grp in sel_groups:
            tickers   = available_groups.get(grp, [])
            available = [t for t in tickers if t in prices.columns]
            if not available:
                continue
            block = build_table(available).sort_values(sort_by, ascending=False)
            if block.empty:
                continue

            with st.expander(f"**{grp}** — {len(available)} tickers", expanded=True):
                display = block[["Name", "Last"] + pct_cols + ["Drawdown", "vs MA200"]].copy()
                styled  = style_pct_table(display, pct_cols, ["Drawdown"])
                st.dataframe(styled, use_container_width=True)
                csv = block.to_csv().encode("utf-8")
                st.download_button(
                    f"⬇ CSV",
                    csv,
                    file_name=f"{grp.replace(' ','_').replace('>','').replace('›','')}.csv",
                    mime="text/csv",
                    key=f"dl_eq_{grp}",
                )

    # ════════════════════════════
    # VIEW: CANDLE CHARTS
    # ════════════════════════════
    elif eq_view == "Candle Charts":

        # Chart controls
        ctrl1, ctrl2, ctrl3, ctrl4, ctrl5 = st.columns([2, 1, 1, 1, 1])
        with ctrl1:
            chart_ticker = st.selectbox(
                "Ticker",
                options=sel_tickers,
                key="eq_chart_ticker",
            )
        with ctrl2:
            ma_fast = st.number_input("Fast MA", min_value=5, max_value=100, value=20, step=5, key="eq_maf")
        with ctrl3:
            ma_slow = st.number_input("Slow MA", min_value=20, max_value=300, value=50, step=10, key="eq_mas")
        with ctrl4:
            show_vol = st.checkbox("Volume", value=True, key="eq_vol")
        with ctrl5:
            chart_height = st.selectbox("Height", [400, 500, 600], index=1, key="eq_h")

        # Single focused chart
        fig = ohlcv_chart(chart_ticker, height=chart_height, ma_fast=ma_fast, ma_slow=ma_slow, show_volume=show_vol)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

        # ── Mini overview grid: line charts for all selected tickers
        st.markdown("### Overview — All Selected Tickers")
        st.caption("Candle charts for individual tickers above · Click any ticker in the selector to focus")

        grid_cols = st.columns(3)
        for i, t in enumerate(sel_tickers):
            if t == chart_ticker:
                continue  # skip the focused one
            fig_mini = price_chart(t, height=220, ma_fast=ma_fast, ma_slow=ma_slow)
            if fig_mini:
                with grid_cols[i % 3]:
                    st.plotly_chart(fig_mini, use_container_width=True)

    # ════════════════════════════
    # VIEW: RATIO CHARTS
    # ════════════════════════════
    else:

        # Filter ratios to only those whose tickers are in the selected universe
        all_sel = set(sel_tickers) | set(prices.columns)
        relevant_ratios = {
            lbl: (n, d) for lbl, (n, d) in MACRO_RATIOS.items()
            if n in all_sel and d in all_sel
        }

        if not relevant_ratios:
            st.info("No ratios available for the selected sleeves. Try selecting broader groups.")
        else:
            ratio_cols = st.columns(2)
            for i, (label, (num, den)) in enumerate(relevant_ratios.items()):
                fig = ratio_chart(num, den, label)
                if fig:
                    with ratio_cols[i % 2]:
                        st.plotly_chart(fig, use_container_width=True)


# ════════════════════════════════════════════════════════════
# TAB 3 — FIXED INCOME
# ════════════════════════════════════════════════════════════

with tab_fi:

    st.markdown("## Fixed Income")

    fi_view = st.radio("View", ["Returns", "Yield Curve Proxies", "Credit Spreads"], horizontal=True)

    fi_tickers = list(dict.fromkeys(
        [t for sub in YIELD_CURVE.values() for t in sub.values()] +
        ["HYG", "LQD", "TLT", "IEF", "SHY", "EMB"]
    ))
    fi_table = build_table([t for t in fi_tickers if t in prices.columns])

    if fi_view == "Returns":
        if not fi_table.empty:
            pct_cols = ["Daily %", "MTD %", "YTD %", "1YR %"]
            display  = fi_table[["Name", "Last"] + pct_cols + ["Drawdown"]].sort_values(sort_by, ascending=False)
            styled   = style_pct_table(display, pct_cols, ["Drawdown"])
            st.dataframe(styled, use_container_width=True)

    elif fi_view == "Yield Curve Proxies":
        st.caption("ETF prices as proxies for rate direction — not actual yields. Falling price = rising yield.")

        curve_tickers = {"SHY": "2yr", "IEF": "7-10yr", "TLT": "20yr+", "TIP": "TIPS"}
        chart_cols    = st.columns(2)
        for i, (t, label) in enumerate(curve_tickers.items()):
            fig = price_chart(t, height=280)
            if fig:
                fig.update_layout(title=dict(text=f"<b>{t}</b>  ({label})", font=dict(size=12, color="#c9d1d9")))
                with chart_cols[i % 2]:
                    st.plotly_chart(fig, use_container_width=True)

    else:  # Credit Spreads (relative returns)
        st.caption("HYG/TLT ratio = risk-on vs risk-off credit signal. Rising = credit risk appetite expanding.")
        spread_ratios = {
            "HYG / TLT — Risk-on vs Risk-off":  ("HYG", "TLT"),
            "LQD / TLT — IG vs Rates":           ("LQD", "TLT"),
            "EMB / LQD — EM vs IG":              ("EMB", "LQD"),
            "HYG / LQD — HY vs IG":              ("HYG", "LQD"),
        }
        chart_cols = st.columns(2)
        for i, (label, (num, den)) in enumerate(spread_ratios.items()):
            fig = ratio_chart(num, den, label)
            if fig:
                with chart_cols[i % 2]:
                    st.plotly_chart(fig, use_container_width=True)


# ════════════════════════════════════════════════════════════
# TAB 4 — COMMODITIES
# ════════════════════════════════════════════════════════════

with tab_cmd_:  # Note: tab var is tab_cmd_ for commodities

    st.markdown("## Commodities")

    cmd_groups = {
        "Broad":    ["DBC", "DBA", "DBB"],
        "Energy":   ["XLE", "XOP", "USO", "UNG"],
        "Metals":   ["GLD", "GDX", "GDXJ", "SLV", "CPER", "XME"],
    }
    cmd_view = st.radio("View", ["Returns", "Price Charts", "Ratio Charts"], horizontal=True, key="cmd_view")

    cmd_tickers = list(dict.fromkeys(t for grp in cmd_groups.values() for t in grp))
    cmd_table   = build_table([t for t in cmd_tickers if t in prices.columns])

    if cmd_view == "Returns":
        if not cmd_table.empty:
            pct_cols = ["Daily %", "MTD %", "YTD %", "1YR %"]
            display  = cmd_table[["Name", "Last"] + pct_cols + ["Drawdown"]].sort_values(sort_by, ascending=False)
            styled   = style_pct_table(display, pct_cols, ["Drawdown"])
            st.dataframe(styled, use_container_width=True)

    elif cmd_view == "Price Charts":
        avail    = [t for t in cmd_tickers if t in prices.columns]
        selected = st.multiselect("Tickers", avail,
            default=[t for t in ["GLD", "DBC", "GDX", "CPER"] if t in prices.columns],
            key="cmd_sel")
        chart_cols = st.columns(2)
        for i, t in enumerate(selected):
            fig = price_chart(t, height=300)
            if fig:
                with chart_cols[i % 2]:
                    st.plotly_chart(fig, use_container_width=True)

    else:  # Ratios
        comm_ratios = {
            "GLD  / SPY  — Gold vs US":        ("GLD",  "SPY"),
            "GDX  / GLD  — Miners vs Gold":    ("GDX",  "GLD"),
            "DBC  / SPY  — Commodities vs US": ("DBC",  "SPY"),
            "CPER / GLD  — Copper/Gold ratio": ("CPER", "GLD"),
            "XLE  / SPY  — Energy vs US":      ("XLE",  "SPY"),
            "SLV  / GLD  — Silver vs Gold":    ("SLV",  "GLD"),
        }
        chart_cols = st.columns(2)
        for i, (label, (num, den)) in enumerate(comm_ratios.items()):
            fig = ratio_chart(num, den, label)
            if fig:
                with chart_cols[i % 2]:
                    st.plotly_chart(fig, use_container_width=True)


# ════════════════════════════════════════════════════════════
# TAB 5 — FX
# ════════════════════════════════════════════════════════════

with tab_fx:

    st.markdown("## G10 + SGD vs USD")
    st.caption("All pairs expressed as USD per 1 unit of foreign currency. Rising = that currency strengthening vs USD.")

    if not fx_data:
        st.error("No FX data loaded.")
    else:
        last_dt = prices.index.max() if not prices.empty else pd.Timestamp.today()
        mtd_s   = pd.Timestamp(year=last_dt.year, month=last_dt.month, day=1)
        ytd_s   = pd.Timestamp(year=last_dt.year, month=1, day=1)

        rows = []
        for ccy, s in fx_data.items():
            s = safe_idx(s.dropna())
            if s.empty:
                continue
            rows.append({
                "CCY":     ccy,
                "Name":    FX_PAIRS[ccy]["name"],
                "Spot":    round(float(s.iloc[-1]), 4),
                "Daily %": pct_from(s, s.index[-2]) if len(s) > 1 else float("nan"),
                "MTD %":   pct_from(s, mtd_s),
                "YTD %":   pct_from(s, ytd_s),
                "1YR %":   pct_1yr(s),
            })

        fx_table = pd.DataFrame(rows).set_index("CCY").sort_values(sort_by, ascending=False)

        # ── Scorecard
        strengthening = int((fx_table["MTD %"] > 0).sum())
        weakening     = int((fx_table["MTD %"] < 0).sum())
        avg_mtd       = fx_table["MTD %"].mean()

        c1, c2, c3 = st.columns(3)
        with c1: st.metric("Strengthening vs USD (MTD)", strengthening, delta=f"of {strengthening+weakening}", delta_color="off")
        with c2: st.metric("Weakening vs USD (MTD)",     weakening,     delta=f"of {strengthening+weakening}", delta_color="off")
        with c3: st.metric("Avg G10 MTD vs USD",         f"{avg_mtd*100:.2f}%")

        if strengthening >= 8:
            st.success(f"✅ {strengthening}/11 currencies strengthening — broad dollar weakness, thesis supported")
        elif strengthening >= 5:
            st.warning(f"⚠️ {strengthening}/11 currencies strengthening — mixed USD picture")
        else:
            st.error(f"❌ {strengthening}/11 currencies strengthening — USD holding firm, thesis under pressure")

        st.divider()

        pct_cols = ["Daily %", "MTD %", "YTD %", "1YR %"]
        fmt      = {"Spot": "{:.4f}"}
        fmt.update({c: "{:.2%}" for c in pct_cols})
        styled = (fx_table[["Name", "Spot"] + pct_cols]
                  .style.format(fmt, na_rep="—")
                  .background_gradient(subset=pct_cols, cmap="RdYlGn", vmin=-0.05, vmax=0.05))
        st.dataframe(styled, use_container_width=True)

        st.divider()
        st.markdown("## FX Charts")

        chart_cols = st.columns(2)
        for i, (ccy, s) in enumerate(fx_data.items()):
            s = safe_idx(s.dropna())
            if s.empty:
                continue
            fig  = go.Figure()
            name = FX_PAIRS[ccy]["name"]
            fig.add_trace(go.Scatter(x=s.index, y=s, name="Spot",
                line=dict(color="#58a6ff", width=1.8),
                hovertemplate="%{x|%d %b %Y}<br>%{y:.4f}<extra></extra>"))
            if len(s) >= 50:
                fig.add_trace(go.Scatter(x=s.index, y=ma(s, 50), name="MA50",
                    line=dict(color="#fbbf24", width=1, dash="dot")))
            if len(s) >= 200:
                ma2 = ma(s, 200)
                fig.add_trace(go.Scatter(x=s.index, y=s, fill=None, mode="lines",
                    line=dict(color="rgba(0,0,0,0)"), showlegend=False, hoverinfo="skip"))
                fig.add_trace(go.Scatter(x=ma2.index, y=ma2, fill="tonexty",
                    fillcolor="rgba(63,185,80,0.07)", mode="none", showlegend=False, hoverinfo="skip"))
                fig.add_trace(go.Scatter(x=ma2.index, y=ma2, name="MA200",
                    line=dict(color="#f87171", width=1, dash="dash")))
            ytd_ret = pct_from(s, ytd_s)
            col     = "#3fb950" if ytd_ret >= 0 else "#f85149"
            arr     = "▲" if ytd_ret >= 0 else "▼"
            layout  = {**PLOTLY_LAYOUT, "height": 280,
                "title": dict(text=f"<b>{ccy}</b>  {name}  <span style='color:{col};font-size:10px'>{arr} {ytd_ret*100:.1f}% YTD</span>",
                              font=dict(size=11, color="#c9d1d9")),
                "yaxis": dict(**PLOTLY_LAYOUT["yaxis"], tickformat=".4f")}
            fig.update_layout(**layout)
            with chart_cols[i % 2]:
                st.plotly_chart(fig, use_container_width=True)


# ════════════════════════════════════════════════════════════
# TAB 6 — MACRO CALENDAR (shell — manual data entry for now)
# ════════════════════════════════════════════════════════════

with tab_macro:

    st.markdown("## Macro Calendar")
    st.caption("Manual entry — paste upcoming events below. Auto-feed via API in a future version.")

    st.markdown("### Upcoming Events")

    # Editable dataframe for manual calendar entries
    # Note: Date stored as string (YYYY-MM-DD) to avoid Streamlit DateColumn/string incompatibility
    default_events = pd.DataFrame([
        {"Date": "", "Time (UTC)": "", "Country": "", "Event": "", "Period": "", "Forecast": "", "Prior": "", "Notes": ""},
    ])

    edited = st.data_editor(
        default_events,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "Date":         st.column_config.TextColumn("Date (YYYY-MM-DD)", max_chars=12),
            "Time (UTC)":   st.column_config.TextColumn("Time (UTC)", max_chars=10),
            "Country":      st.column_config.TextColumn("Country", max_chars=20),
            "Event":        st.column_config.TextColumn("Event"),
            "Period":       st.column_config.TextColumn("Period", max_chars=10),
            "Forecast":     st.column_config.TextColumn("Forecast"),
            "Prior":        st.column_config.TextColumn("Prior"),
            "Notes":        st.column_config.TextColumn("Notes"),
        },
    )

    csv_cal = edited.to_csv(index=False).encode("utf-8")
    st.download_button("⬇ Export Calendar CSV", csv_cal, file_name="macro_calendar.csv", mime="text/csv")

    st.divider()
    st.markdown("### Key Macro Themes")
    theme_notes = st.text_area(
        "Add your notes here (free text):",
        height=200,
        placeholder="e.g. Fed on hold until June · BOJ hiking cycle continues · EUR benefiting from US tariff rotation…",
    )


# ════════════════════════════════════════════════════════════
# TAB 7 — TRADE BLOTTER
# Supports: manual entry, CSV upload (IB format parser),
# dividends, P&L summary
# ════════════════════════════════════════════════════════════

with tab_blotter:

    st.markdown("## Trade Blotter")

    blotter_view = st.radio("Mode", ["Manual Entry", "Import IB Statement", "View Positions"], horizontal=True)

    # ── Session-state store for trades
    if "trades" not in st.session_state:
        st.session_state.trades = pd.DataFrame(columns=[
            "Date", "Type", "Ticker", "Action",
            "Qty", "Price", "Currency", "Commission", "Notes",
        ])

    # ── Helper: format trade log
    def format_trade_df(df):
        if df.empty:
            return df
        df = df.copy()
        for c in ["Qty", "Price", "Commission"]:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")
        return df

    # ────────────────────────────────────────────────────────
    # Mode 1 — Manual Entry
    # ────────────────────────────────────────────────────────
    if blotter_view == "Manual Entry":

        st.markdown("### Add Trade or Dividend")

        with st.form("add_trade", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                t_date   = st.date_input("Date", value=datetime.date.today())
                t_type   = st.selectbox("Type", ["BUY", "SELL", "DIVIDEND", "INTEREST", "FEE"])
                t_ticker = st.text_input("Ticker", placeholder="e.g. GLD")
            with c2:
                t_action = st.selectbox("Action", ["OPEN", "CLOSE", "ADD", "REDUCE", "INCOME"])
                t_qty    = st.number_input("Quantity", value=0.0, step=1.0, format="%.4f")
                t_price  = st.number_input("Price / Amount", value=0.0, step=0.01, format="%.4f")
            with c3:
                t_ccy    = st.selectbox("Currency", ["USD", "SGD", "EUR", "GBP", "JPY", "AUD", "HKD"])
                t_comm   = st.number_input("Commission", value=0.0, step=0.01, format="%.4f")
                t_notes  = st.text_input("Notes", placeholder="Optional context")

            submitted = st.form_submit_button("➕ Add Entry")
            if submitted:
                new_row = pd.DataFrame([{
                    "Date":       str(t_date),
                    "Type":       t_type,
                    "Ticker":     t_ticker.upper().strip(),
                    "Action":     t_action,
                    "Qty":        t_qty,
                    "Price":      t_price,
                    "Currency":   t_ccy,
                    "Commission": t_comm,
                    "Notes":      t_notes,
                }])
                st.session_state.trades = pd.concat([st.session_state.trades, new_row], ignore_index=True)
                st.success(f"Added: {t_type} {t_qty} {t_ticker} @ {t_price}")

    # ────────────────────────────────────────────────────────
    # Mode 2 — IB Statement Parser
    # ────────────────────────────────────────────────────────
    elif blotter_view == "Import IB Statement":

        st.markdown("### Import Interactive Brokers Statement")
        st.caption(
            "Export from IB: **Account Management → Reports → Activity Statement → CSV**. "
            "This parser handles the Trades and Dividends sections automatically."
        )

        uploaded = st.file_uploader("Upload IB Activity Statement (.csv)", type=["csv"])

        def parse_ib_statement(file_bytes):
            """
            Parse IB Activity Statement CSV.
            IB CSVs have section headers mid-file (e.g. 'Trades,Header,...')
            so we read line by line and extract the relevant sections.
            """
            content  = file_bytes.decode("utf-8", errors="replace")
            lines    = content.splitlines()
            trades_rows   = []
            div_rows      = []
            trades_header = None
            div_header    = None

            for line in lines:
                parts = [p.strip().strip('"') for p in line.split(",")]
                if not parts:
                    continue

                section = parts[0] if parts else ""

                # ── Trades section
                if section == "Trades":
                    if len(parts) < 3:
                        continue
                    if parts[1] == "Header":
                        trades_header = parts[2:]
                    elif parts[1] == "Data" and trades_header:
                        trades_rows.append(dict(zip(trades_header, parts[2:])))

                # ── Dividends section
                elif section in ("Dividends", "Withholding Tax"):
                    if len(parts) < 3:
                        continue
                    if parts[1] == "Header":
                        div_header = parts[2:]
                    elif parts[1] == "Data" and div_header:
                        div_rows.append(dict(zip(div_header, parts[2:])))

            # ── Normalise trades
            trade_records = []
            for r in trades_rows:
                try:
                    # IB field names vary slightly by account type
                    date_raw  = r.get("Date/Time") or r.get("TradeDate") or r.get("Date") or ""
                    symbol    = r.get("Symbol") or r.get("Ticker") or ""
                    qty_raw   = r.get("Quantity") or "0"
                    price_raw = r.get("T. Price") or r.get("TradePrice") or r.get("Price") or "0"
                    comm_raw  = r.get("Comm/Fee") or r.get("Commission") or r.get("IBCommission") or "0"
                    ccy       = r.get("Currency") or r.get("Curr") or "USD"
                    asset     = r.get("Asset Category") or ""

                    qty       = float(str(qty_raw).replace(",", "").replace(" ", "") or 0)
                    price     = float(str(price_raw).replace(",", "").replace(" ", "") or 0)
                    comm      = float(str(comm_raw).replace(",", "").replace(" ", "") or 0)

                    action    = "BUY" if qty > 0 else "SELL"
                    date_str  = str(date_raw).split(",")[0].strip()

                    if symbol and price != 0:
                        trade_records.append({
                            "Date":       date_str,
                            "Type":       action,
                            "Ticker":     symbol,
                            "Action":     "OPEN" if qty > 0 else "CLOSE",
                            "Qty":        abs(qty),
                            "Price":      price,
                            "Currency":   ccy,
                            "Commission": abs(comm),
                            "Notes":      asset,
                        })
                except Exception:
                    continue

            # ── Normalise dividends
            div_records = []
            for r in div_rows:
                try:
                    date_str = r.get("Date") or ""
                    desc     = r.get("Description") or ""
                    amount   = float(str(r.get("Amount") or "0").replace(",", "") or 0)
                    ccy      = r.get("Currency") or "USD"
                    # Extract ticker from description (e.g. "GLD(US12345) Cash Dividend")
                    ticker_match = re.match(r"^([A-Z0-9\.]+)", desc)
                    ticker = ticker_match.group(1) if ticker_match else desc[:8]

                    if amount != 0:
                        div_records.append({
                            "Date":       date_str,
                            "Type":       "DIVIDEND",
                            "Ticker":     ticker,
                            "Action":     "INCOME",
                            "Qty":        1.0,
                            "Price":      amount,
                            "Currency":   ccy,
                            "Commission": 0.0,
                            "Notes":      desc,
                        })
                except Exception:
                    continue

            all_records = trade_records + div_records
            if not all_records:
                return pd.DataFrame(), 0, 0
            df = pd.DataFrame(all_records)
            return df, len(trade_records), len(div_records)

        if uploaded:
            file_bytes = uploaded.read()
            with st.spinner("Parsing IB statement…"):
                parsed_df, n_trades, n_divs = parse_ib_statement(file_bytes)

            if parsed_df.empty:
                st.error("Could not parse any trades or dividends from this file. "
                         "Check that you exported an Activity Statement (not a Portfolio Analyst report) in CSV format.")
            else:
                st.success(f"Parsed {n_trades} trades + {n_divs} dividend entries.")
                st.dataframe(parsed_df, use_container_width=True)

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Append to Blotter"):
                        st.session_state.trades = pd.concat(
                            [st.session_state.trades, parsed_df], ignore_index=True
                        )
                        st.success("Appended to blotter.")
                with col2:
                    csv_out = parsed_df.to_csv(index=False).encode("utf-8")
                    st.download_button("⬇ Download Parsed CSV", csv_out,
                                       file_name="ib_parsed.csv", mime="text/csv")

    # ────────────────────────────────────────────────────────
    # Mode 3 — View Positions & Summary
    # ────────────────────────────────────────────────────────
    elif blotter_view == "View Positions":

        st.markdown("### Position Summary")

        df = format_trade_df(st.session_state.trades)

        if df.empty:
            st.info("No trades logged yet. Use Manual Entry or Import IB Statement to add trades.")
        else:
            # ── Full log
            st.markdown("#### Full Trade Log")
            st.dataframe(df, use_container_width=True)

            # ── Summary by ticker
            st.markdown("#### Summary by Ticker")
            trades_only = df[df["Type"].isin(["BUY", "SELL"])].copy()

            if not trades_only.empty:
                summary_rows = []
                for tkr, grp in trades_only.groupby("Ticker"):
                    buys  = grp[grp["Type"] == "BUY"]
                    sells = grp[grp["Type"] == "SELL"]
                    net_qty   = buys["Qty"].sum() - sells["Qty"].sum()
                    buy_val   = (buys["Qty"] * buys["Price"]).sum()
                    buy_qty   = buys["Qty"].sum()
                    avg_cost  = buy_val / buy_qty if buy_qty > 0 else 0
                    total_comm = grp["Commission"].sum()

                    # Last price from yfinance
                    last_px = float("nan")
                    if tkr in prices.columns:
                        last_px = float(prices[tkr].dropna().iloc[-1])

                    unreal_pnl = (last_px - avg_cost) * net_qty if not np.isnan(last_px) else float("nan")
                    pnl_pct    = (last_px / avg_cost - 1) if (not np.isnan(last_px) and avg_cost > 0) else float("nan")

                    summary_rows.append({
                        "Ticker":       tkr,
                        "Net Qty":      round(net_qty, 4),
                        "Avg Cost":     round(avg_cost, 4),
                        "Last Price":   round(last_px, 4) if not np.isnan(last_px) else "—",
                        "Unrealised PnL": round(unreal_pnl, 2) if not np.isnan(unreal_pnl) else "—",
                        "Return %":     pnl_pct,
                        "Commission":   round(total_comm, 2),
                        "Status":       "OPEN" if net_qty > 0.001 else "CLOSED",
                    })

                sum_df = pd.DataFrame(summary_rows).set_index("Ticker")
                pct_cols_sum = ["Return %"]
                fmt_sum = {c: "{:.2%}" for c in pct_cols_sum if c in sum_df.columns}
                styled_sum = sum_df.style.format(fmt_sum, na_rep="—")
                if "Return %" in sum_df.columns:
                    def color_pnl(v):
                        if isinstance(v, float) and not np.isnan(v):
                            return f"color: {'#3fb950' if v >= 0 else '#f85149'}"
                        return ""
                    styled_sum = styled_sum.applymap(color_pnl, subset=["Return %"])
                st.dataframe(styled_sum, use_container_width=True)

            # ── Dividend summary
            st.markdown("#### Dividends & Income")
            divs = df[df["Type"] == "DIVIDEND"].copy()
            if not divs.empty:
                div_summary = (divs.groupby("Ticker")["Price"]
                               .sum().reset_index()
                               .rename(columns={"Price": "Total Received"})
                               .sort_values("Total Received", ascending=False))
                st.dataframe(div_summary.set_index("Ticker"), use_container_width=True)
                total_div = divs["Price"].sum()
                st.metric("Total Dividends / Income Received", f"{total_div:,.2f}")
            else:
                st.info("No dividend entries yet.")

            # ── Export
            st.divider()
            col1, col2 = st.columns(2)
            with col1:
                csv_full = df.to_csv(index=False).encode("utf-8")
                st.download_button("⬇ Export Full Blotter CSV", csv_full,
                                   file_name="blotter_full.csv", mime="text/csv")
            with col2:
                if st.button("🗑 Clear Blotter", type="secondary"):
                    st.session_state.trades = pd.DataFrame(columns=[
                        "Date", "Type", "Ticker", "Action",
                        "Qty", "Price", "Currency", "Commission", "Notes",
                    ])
                    st.rerun()

    # ── Always show current blotter count
    n = len(st.session_state.trades)
    if n > 0:
        st.caption(f"{n} entries in blotter this session  ·  trades persist until page refresh")
