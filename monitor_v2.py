# ============================================================
# MARKET MONITOR v2 — Thesis-Driven
# USD Down-Cycle / RoW / Hard Assets tracker
#
# HOW TO RUN:
#   conda activate my_quant_lab
#   cd ~/Documents/PyQuantNews
#   streamlit run monitor_v2.py
# ============================================================

import os
import tempfile
import pathlib
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# ── OpenBB tries to write a lock file into its own package
# directory on first import. On Streamlit Cloud that directory
# is read-only, causing a PermissionError.
# We patch the lock path to the temp directory BEFORE importing.
try:
    import openbb_core.app.static.package_builder as _pb
    _pb.PackageBuilder._lock_path = property(
        lambda self: pathlib.Path(tempfile.gettempdir()) / "openbb.lock"
    )
except Exception:
    pass

os.environ["OPENBB_HOME"]         = tempfile.gettempdir()
os.environ["OPENBB_PYTHON_BUILD"] = "false"

from openbb import obb
obb.user.preferences.output_type = "dataframe"

st.set_page_config(page_title="Market Monitor", layout="wide", page_icon="📊")

# ============================================================
# WATCHLIST — edit this section to add/remove tickers
# Organised around your thesis sleeves.
# Tickers marked with * may have limited data via yfinance.
# ============================================================

GROUPS = {

    # ──────────────────────────────────────────────────────
    # BENCHMARKS — everything is measured relative to these
    # ──────────────────────────────────────────────────────
    "Benchmarks": [
        "SPY",   # S&P 500 — US large cap benchmark
        "ACWI",  # All-world including US — global benchmark
        "ACWX",  # All-world ex-US — RoW benchmark
    ],

    # ──────────────────────────────────────────────────────
    # THESIS SIGNALS
    # These confirm or deny the USD down-cycle thesis.
    # Watch these FIRST before acting on anything else.
    #   UUP falling  → USD weakening ✅
    #   TIP rising   → real yields falling ✅
    #   DBC rising   → commodities bid ✅
    #   GLD rising   → monetary regime shift ✅
    # ──────────────────────────────────────────────────────
    "Thesis Signals (USD / Real Rates / Commodities)": [
        "UUP",   # USD ETF proxy (DXY unavailable via yfinance)
        "TIP",   # TIPS ETF — real yield proxy
        "DBC",   # Broad commodities basket
        "GLD",   # Gold spot proxy
        "TLT",   # 20yr Treasury — rates direction
    ],

    # ──────────────────────────────────────────────────────
    # HARD ASSETS — core thesis expression
    # ──────────────────────────────────────────────────────
    "Hard Assets — Energy": [
        "XLE",   # Broad US energy sector
        "XOP",   # Oil & gas E&P (higher oil beta)
        "USO",   # WTI crude oil
        "UNG",   # Natural gas
    ],

    "Hard Assets — Metals & Mining": [
        "GLD",   # Gold
        "GDX",   # Gold miners (levered gold)
        "GDXJ",  # Junior gold miners (higher beta)
        "SLV",   # Silver
        "CPER",  # Copper (leading economic indicator)
        "XME",   # Broad metals & mining
    ],

    "Hard Assets — Broad Commodities": [
        "DBC",   # Broad commodities (diversified)
        "DBA",   # Agriculture
        "DBB",   # Base metals
        "DBE",   # Energy sub-index
    ],

    # ──────────────────────────────────────────────────────
    # EMERGING MARKETS
    # Split by region — they don't move together
    # ──────────────────────────────────────────────────────
    "EM — Broad": [
        "EEM",   # iShares MSCI EM (most liquid)
        "IEMG",  # iShares Core EM (cheaper, slightly different weights)
        "VWO",   # Vanguard EM
    ],

    "EM — Latin America": [
        "ILF",   # iShares Latin America 40
        "EWZ",   # Brazil
        "EWW",   # Mexico
        "ECH",   # Chile
        "GXG",   # Colombia
        "EPU",   # Peru
    ],

    "EM — Asia": [
        "AAXJ",  # Asia ex-Japan broad
        "MCHI",  # China broad (MSCI)
        "FXI",   # China large cap (more liquid)
        "EWT",   # Taiwan
        "EWY",   # South Korea
        "INDA",  # India
        "VNM",   # Vietnam
        "THD",   # Thailand
        "EPHE",  # Philippines
    ],

    "EM — EMEA / Frontier": [
        "TUR",   # Turkey
        "EPOL",  # Poland
        "EGPT",  # Egypt
        "KSA",   # Saudi Arabia
    ],

    # ──────────────────────────────────────────────────────
    # DEVELOPED MARKETS ex-US
    # ──────────────────────────────────────────────────────
    "DM — Broad ex-US": [
        "EFA",   # MSCI EAFE (Europe + Aus + Far East)
        "IEFA",  # iShares Core EAFE (cheaper)
        "EFV",   # EAFE Value tilt
    ],

    "DM — Europe": [
        "VGK",   # Broad Europe
        "EWG",   # Germany
        "EWU",   # United Kingdom
        "EWP",   # Spain
        "EWI",   # Italy
        "EWQ",   # France
        "EPOL",  # Poland (Eastern Europe play)
    ],

    "DM — Asia Pacific": [
        "EWJ",   # Japan
        "EWA",   # Australia
        "EWS",   # Singapore
        "EWH",   # Hong Kong
    ],

    # ──────────────────────────────────────────────────────
    # UK INCOME (LSE-listed — may need .L suffix)
    # If IUKD fails, try "IUKD.L" in the ticker list
    # ──────────────────────────────────────────────────────
    "UK Income (LSE — flag expected)": [
        "IUKD",  # iShares UK Dividend — try IUKD.L if fails
        "IUKP",  # iShares UK Property
    ],

    # ──────────────────────────────────────────────────────
    # CREDIT & BONDS — early warning layer
    # HYG spreads widening = risk-off developing
    # even before equities react
    # ──────────────────────────────────────────────────────
    "Credit & Bonds": [
        "HYG",   # High yield (junk) bonds — risk appetite signal
        "LQD",   # Investment grade corporate bonds
        "TLT",   # 20yr US Treasury — rates direction
        "IEF",   # 7-10yr US Treasury
        "EMB",   # EM sovereign bonds (USD)
        "LEMB",  # EM local currency bonds
    ],

    # ──────────────────────────────────────────────────────
    # US SECTORS — context / reference only
    # All 11 GICS sectors. Useful for rotation signals
    # and understanding what's driving SPY.
    # ──────────────────────────────────────────────────────
    "USA — Sectors (reference)": [
        "XLK",   # Technology
        "XLF",   # Financials
        "XLV",   # Healthcare
        "XLY",   # Consumer Discretionary
        "XLP",   # Consumer Staples
        "XLE",   # Energy
        "XLI",   # Industrials
        "XLB",   # Materials
        "XLC",   # Communications
        "XLU",   # Utilities
        "XLRE",  # Real Estate
    ],

    "USA — Style / Factor": [
        "SPY",   # S&P 500 (cap weight)
        "RSP",   # S&P 500 equal weight (breadth signal)
        "QQQ",   # Nasdaq 100 (growth / tech)
        "IVE",   # S&P 500 Value
        "IVW",   # S&P 500 Growth
        "IWM",   # Russell 2000 small cap
        "VTV",   # Vanguard Value
        "VUG",   # Vanguard Growth
    ],

    # ──────────────────────────────────────────────────────
    # SINGLE STOCKS
    # ──────────────────────────────────────────────────────
    "Single Stocks": [
        "FASTLY",  # Fastly
    ],
}

# ──────────────────────────────────────────────────────────
# MACRO RATIOS
# Rising = numerator outperforming denominator.
# Grouped into: Thesis confirmation / Commodity signals /
# Regional leadership / US internals
# ──────────────────────────────────────────────────────────
MACRO_RATIOS = {

    # ── Core thesis confirmation (watch these weekly)
    "ACWX / SPY  — RoW vs US":          ("ACWX", "SPY"),
    "EEM  / SPY  — EM vs US":           ("EEM",  "SPY"),
    "EFA  / SPY  — DM ex-US vs US":     ("EFA",  "SPY"),
    "UUP  / SPY  — USD strength":       ("UUP",  "SPY"),

    # ── Hard asset / commodity signals
    "GLD  / SPY  — Gold vs US":         ("GLD",  "SPY"),
    "GDX  / SPY  — Miners vs US":       ("GDX",  "SPY"),
    "GDX  / GLD  — Miners vs Gold":     ("GDX",  "GLD"),   # miner leverage signal
    "DBC  / SPY  — Commodities vs US":  ("DBC",  "SPY"),
    "CPER / GLD  — Copper/Gold ratio":  ("CPER", "GLD"),   # growth vs safety

    # ── EM regional leadership
    "ILF  / EEM  — LatAm vs broad EM":  ("ILF",  "EEM"),
    "AAXJ / EEM  — Asia vs broad EM":   ("AAXJ", "EEM"),
    "EWZ  / SPY  — Brazil vs US":       ("EWZ",  "SPY"),

    # ── US internal rotation signals
    "IVE  / IVW  — Value vs Growth":    ("IVE",  "IVW"),
    "RSP  / SPY  — Equal vs Cap Weight":("RSP",  "SPY"),
    "XLE  / SPY  — Energy vs US":       ("XLE",  "SPY"),
    "HYG  / TLT  — Risk-on vs Risk-off":("HYG",  "TLT"),  # credit vs safety
}

# ──────────────────────────────────────────────────────────
# G10 + SGD CURRENCY PAIRS
# All quoted as "how many USD does 1 unit of foreign ccy buy"
# so RISING = that currency STRENGTHENING vs USD.
#
# Convention note:
#   EUR, GBP, AUD, NZD, SGD → naturally quoted per USD (rising = stronger)
#   JPY, CHF, CAD, NOK, SEK, DKK → inverted (we store as 1/pair so
#   rising still means that currency is strengthening vs USD)
#
# yfinance format: "EURUSD=X" → euros per dollar... we invert where needed
# ──────────────────────────────────────────────────────────
FX_PAIRS = {
    "EUR":  {"ticker": "EURUSD=X",  "invert": False, "name": "Euro"},
    "GBP":  {"ticker": "GBPUSD=X",  "invert": False, "name": "British Pound"},
    "JPY":  {"ticker": "JPY=X",     "invert": True,  "name": "Japanese Yen"},
    "CHF":  {"ticker": "CHF=X",     "invert": True,  "name": "Swiss Franc"},
    "AUD":  {"ticker": "AUDUSD=X",  "invert": False, "name": "Australian Dollar"},
    "CAD":  {"ticker": "CAD=X",     "invert": True,  "name": "Canadian Dollar"},
    "NZD":  {"ticker": "NZDUSD=X",  "invert": False, "name": "New Zealand Dollar"},
    "NOK":  {"ticker": "NOK=X",     "invert": True,  "name": "Norwegian Krone"},
    "SEK":  {"ticker": "SEK=X",     "invert": True,  "name": "Swedish Krona"},
    "DKK":  {"ticker": "DKK=X",     "invert": True,  "name": "Danish Krone"},
    "SGD":  {"ticker": "SGD=X",     "invert": True,  "name": "Singapore Dollar"},
}
# These will be flagged in the UI rather than silently missing
KNOWN_DIFFICULT = [
    "IUKD", "IUKP",           # LSE-listed — need .L suffix
    "2807.HK", "9807.HK",     # Hong Kong listed
    "DRGN", "HCOLSEL",        # Limited/no yfinance coverage
    "GXG",                    # Colombia — thin volume, may fail
    "LEMB",                   # Sometimes has data gaps
]


# ============================================================
# SIDEBAR — two tabs: Settings and Notes
# ============================================================

with st.sidebar:

    tab_settings, tab_notes = st.tabs(["⚙️ Settings", "📓 Notes"])

    with tab_settings:

        sort_by = st.selectbox(
            "Sort by",
            ["MTD %", "YTD %", "Daily %", "1YR %"],
            index=0
        )

        start_date = st.date_input(
            "History start",
            value=pd.Timestamp("2020-01-01")
        )

        show_history = st.checkbox("Show yearly returns", value=False)
        if show_history:
            years = st.multiselect(
                "Years",
                options=[2025, 2024, 2023, 2022, 2021, 2020],
                default=[2024, 2023, 2022]
            )
        else:
            years = []

        st.divider()

        view_mode = st.radio(
            "View",
            ["📋 Returns Table", "📊 Price Charts", "📐 Ratio Charts", "🟩 Heatmap", "💱 Currencies"],
            index=0
        )

        st.divider()
        st.caption("Thesis: USD down-cycle → RoW / EM / Hard Assets outperform SPY")

    with tab_notes:

        st.markdown("### 📓 Reference & Notes")
        st.caption("Add to this as the monitor evolves.")

        with st.expander("🧭 The Thesis", expanded=True):
            st.markdown("""
**Crescat / Tavi Costa — USD Down-Cycle**

Core idea: USD weakens → real assets and Rest of World outperform US equities.

**For the thesis to be "on", you need:**
1. **UUP falling** — USD weakening
2. **TIP stable or rising** — real yields falling or flat
3. **DBC rising** — broad commodities bid

*All three together = confirmed. Act with conviction.*

If DXY makes higher highs → reduce RoW/EM/commodity exposure.
If real yields rise hard → gold miners and long-duration assets get hurt.
            """)

        with st.expander("📋 Watchlist Breakdown", expanded=False):
            st.markdown("""
| Layer | Key Tickers | Purpose |
|---|---|---|
| Benchmarks | SPY, ACWI, ACWX | Measure everything against these |
| Thesis signals | UUP, TIP, DBC, GLD, TLT | Confirm thesis before acting |
| Energy | XLE, XOP, USO, UNG | Full energy stack |
| Metals | GLD, GDX, GDXJ, SLV, CPER | Gold to juniors to copper |
| Commodities | DBC, DBA, DBB, DBE | Broad + sub-components |
| EM broad | EEM, IEMG, VWO | Three ways to own EM |
| EM LatAm | ILF, EWZ, EWW, ECH, EPU | Country level |
| EM Asia | AAXJ, MCHI, EWT, EWY, INDA, VNM | Full Asia |
| EM EMEA | TUR, EPOL, EGPT, KSA | Frontier + Eastern Europe |
| DM Europe | VGK, EWG, EWU, EWP, EWI | Country level |
| DM Asia-Pac | EWJ, EWA, EWS, EWH | Japan, Aus, Singapore, HK |
| Credit | HYG, LQD, TLT, IEF, EMB | Early warning layer |
| US sectors | XLK to XLRE (all 11) | Reference / rotation signal |
| US style | SPY, RSP, QQQ, IVE, IVW, IWM | Breadth + factor |
            """)

        with st.expander("📐 How to Read Ratio Charts", expanded=False):
            st.markdown("""
**Rising line = numerator outperforming denominator.**

| Ratio | Rising line means |
|---|---|
| ACWX / SPY | RoW beating US — thesis on |
| EEM / SPY | EM beating US — thesis on |
| GLD / SPY | Gold beating equities |
| GDX / GLD | Miners outpacing gold — metals risk-on |
| CPER / GLD | Copper beating gold — growth priced in |
| ILF / EEM | LatAm leading within EM |
| IVE / IVW | Value beating growth |
| RSP / SPY | Broad participation — healthy rally |
| HYG / TLT | Risk-on credit environment |

**Strong confirmation:** GDX/GLD + CPER/GLD + ACWX/SPY all rising together.
            """)

        with st.expander("🛡️ Risk Rules", expanded=False):
            st.markdown("""
**Rule 1 — Max drawdown**
Any sleeve hits -20% peak to trough AND thesis not confirming
→ cut by 1/3

**Rule 2 — Concentration**
Any sleeve exceeds 25% of portfolio due to outperformance
→ rebalance down

**Rule 3 — Wrong-way warning**
DXY up + equities risk-off + commodities down simultaneously
→ reduce exposure, don't average in
            """)

        with st.expander("⚠️ Known Data Issues", expanded=False):
            st.markdown("""
**LSE ETFs** (IUKD, IUKP)
Try `IUKD.L` / `IUKP.L` in the GROUPS config

**Hong Kong ETFs** (2807.HK, 9807.HK)
Use `.HK` suffix — limited yfinance history

**Colombia** (GXG) — thin volume, may fail silently

**UCITS / ISIN-only** (e.g. LU1900066462)
Not available via yfinance — source via broker
            """)

        with st.expander("🗒️ My Notes", expanded=False):
            st.markdown("""
*Edit this section in the .py file to add your own observations.*

**March 2026**
- Monitor built, OpenBB connected
- Next: add Plotly interactive charts
- Watch: copper/gold ratio for growth confirmation
            """)


# ============================================================
# DATA LOADING
# ============================================================

@st.cache_data(ttl=300)
def load_prices(tickers, start_date, provider="yfinance"):
    """
    Fetches prices via OpenBB. Skips tickers that fail and
    returns whatever it could load. Missing tickers are reported.
    """
    closes = []
    failed = []
    for t in tickers:
        try:
            s = obb.equity.price.historical(
                t, start_date=str(start_date), provider=provider
            ).close.rename(t)
            closes.append(s)
        except Exception:
            failed.append(t)
    if not closes:
        return pd.DataFrame(), failed
    df = pd.concat(closes, axis=1)
    df.index = pd.to_datetime(df.index)
    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)
    return df.sort_index(), failed


# ── Collect all unique tickers across groups + ratios
all_tickers   = list(dict.fromkeys(t for grp in GROUPS.values() for t in grp))
ratio_tickers = list(dict.fromkeys(t for pair in MACRO_RATIOS.values() for t in pair))
fetch_tickers = list(dict.fromkeys(all_tickers + ratio_tickers))

with st.spinner("Loading prices… (first load may take 30–60 seconds)"):
    prices, failed_tickers = load_prices(tuple(fetch_tickers), start_date)


@st.cache_data(ttl=300)
def load_fx(fx_pairs, start_date):
    """
    Fetches FX spot rates via yfinance directly.
    Returns a dict: ccy -> Series (all expressed as "USD per 1 unit of foreign ccy"
    so that rising always means that currency is strengthening vs USD).
    """
    import yfinance as yf
    fx_data = {}
    for ccy, info in fx_pairs.items():
        try:
            raw = yf.download(
                info["ticker"],
                start=str(start_date),
                progress=False,
                auto_adjust=True
            )["Close"].squeeze()
            raw.index = pd.to_datetime(raw.index)
            if raw.index.tz is not None:
                raw.index = raw.index.tz_localize(None)
            # Invert pairs that are quoted as USDXXX so rising = ccy strengthening
            fx_data[ccy] = (1 / raw) if info["invert"] else raw
        except Exception:
            pass
    return fx_data

with st.spinner("Loading FX rates…"):
    fx_data = load_fx(FX_PAIRS, start_date)


@st.cache_data(ttl=86400)
def load_names(tickers):
    """
    Fetches long name for each ticker via OpenBB / yfinance.
    yfinance returns a 'name' column in equity.profile().
    Cached 24hrs. Falls back to ticker string if lookup fails.
    """
    names = {}
    for t in tickers:
        try:
            profile = obb.equity.profile(t, provider="yfinance")
            val = profile["name"].iloc[0]
            names[t] = str(val).strip() if val and str(val).strip() else t
        except Exception:
            names[t] = t
    return names

with st.spinner("Loading ticker names…"):
    ticker_names = load_names(tuple(t for t in fetch_tickers if t in prices.columns))


# ============================================================
# METRICS HELPERS
# ============================================================

def safe_index(series):
    """Ensure index is tz-naive DatetimeIndex."""
    s = series.copy()
    s.index = pd.to_datetime(s.index)
    if s.index.tz is not None:
        s.index = s.index.tz_localize(None)
    return s

def pct_from(series, dt):
    s = safe_index(series.dropna())
    s2 = s[s.index >= pd.Timestamp(dt)]
    if s.empty or s2.empty:
        return float("nan")
    return (s.iloc[-1] / s2.iloc[0]) - 1

def pct_1yr(series):
    s = safe_index(series.dropna())
    if len(s) < 2:
        return float("nan")
    target = s.index[-1] - pd.Timedelta(days=365)
    s2 = s[s.index >= target]
    if s2.empty:
        return float("nan")
    return (s.iloc[-1] / s2.iloc[0]) - 1

def year_return(series, year):
    s = safe_index(series.dropna())
    end  = s.loc[:pd.Timestamp(f"{year}-12-31")]
    prev = s.loc[:pd.Timestamp(f"{year-1}-12-31")]
    if end.empty or prev.empty:
        return float("nan")
    return (end.iloc[-1] / prev.iloc[-1]) - 1

def drawdown(series):
    """Current drawdown from rolling peak."""
    s = series.dropna()
    if s.empty:
        return float("nan")
    peak = s.cummax()
    dd = (s - peak) / peak
    return float(dd.iloc[-1])

def build_table(prices, tickers, names=None, years=None):
    if prices.empty:
        return pd.DataFrame()
    px = prices.copy()
    px.index = pd.to_datetime(px.index)
    if px.index.tz is not None:
        px.index = px.index.tz_localize(None)
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
            "Ticker":  t,
            "Name":    (names or {}).get(t, t),   # long name — falls back to ticker
            "Last":    round(float(s.iloc[-1]), 2),
            "Daily %": pct_from(s, s.index[-2]) if len(s) > 1 else float("nan"),
            "MTD %":   pct_from(s, mtd_start),
            "YTD %":   pct_from(s, ytd_start),
            "1YR %":   pct_1yr(s),
            "Drawdown":drawdown(s),
        }
        for y in (years or []):
            row[f"{y} %"] = year_return(s, y)
        rows.append(row)
    df = pd.DataFrame(rows).set_index("Ticker")
    return df


monitor_table = build_table(prices, all_tickers, names=ticker_names, years=years if show_history else None)


# ============================================================
# PAGE HEADER
# ============================================================

st.title("📊 Market Monitor")

# Data freshness + missing ticker warnings
if not prices.empty:
    st.caption(f"Data as of {prices.index.max().date()}  ·  {len(prices.columns)} tickers loaded")
else:
    st.error("No price data loaded. Check your OpenBB connection.")
    st.stop()

# Flag missing / failed tickers prominently
all_missing = [t for t in all_tickers if t not in prices.columns]
if all_missing:
    with st.expander(f"⚠️  {len(all_missing)} tickers could not be loaded — click to see", expanded=False):
        difficult = [t for t in all_missing if t in KNOWN_DIFFICULT]
        other     = [t for t in all_missing if t not in KNOWN_DIFFICULT]
        if difficult:
            st.warning(f"**Known difficult tickers** (non-US / LSE listed): {', '.join(difficult)}\n\n"
                       f"Try adding `.L` suffix for LSE stocks (e.g. `IUKD.L`) or source these manually.")
        if other:
            st.error(f"**Unexpected failures**: {', '.join(other)}\n\nThese should work — check ticker spelling.")

st.divider()

# ── Top scorecard
if not monitor_table.empty:
    c1, c2, c3, c4, c5 = st.columns(5)
    avg_mtd = monitor_table["MTD %"].mean()
    avg_ytd = monitor_table["YTD %"].mean()
    adv     = int((monitor_table["MTD %"] > 0).sum())
    dec     = int((monitor_table["MTD %"] < 0).sum())
    worst_dd = monitor_table["Drawdown"].min()
    worst_t  = monitor_table["Drawdown"].idxmin() if not monitor_table.empty else "—"

    with c1: st.metric("Avg MTD",  f"{avg_mtd*100:.1f}%", delta=f"{avg_mtd*100:.1f}%")
    with c2: st.metric("Avg YTD",  f"{avg_ytd*100:.1f}%", delta=f"{avg_ytd*100:.1f}%")
    with c3: st.metric("Advancing", f"{adv}", delta=f"of {adv+dec}", delta_color="off")
    with c4: st.metric("Declining", f"{dec}", delta=f"of {adv+dec}", delta_color="off")
    with c5: st.metric("Worst Drawdown", f"{worst_dd*100:.1f}%", delta=worst_t, delta_color="off")

st.divider()


# ============================================================
# VIEW: RETURNS TABLE
# ============================================================

if view_mode == "📋 Returns Table":

    # Download button — export whatever you see as CSV
    csv = monitor_table.to_csv().encode("utf-8")
    st.download_button(
        "⬇️  Download as CSV",
        csv,
        file_name="monitor_export.csv",
        mime="text/csv"
    )

    for group, tickers in GROUPS.items():
        available = [t for t in tickers if t in monitor_table.index]
        missing   = [t for t in tickers if t not in monitor_table.index]

        # Skip groups where nothing loaded
        if not available:
            st.warning(f"**{group}** — no data loaded for any ticker: {', '.join(missing)}")
            continue

        block = monitor_table.loc[available].copy()
        block = block[~block.index.duplicated()]
        block = block.sort_values(sort_by, ascending=False)

        # Group header label — show if any tickers are missing
        label = f"**{group}**  —  {len(available)} tickers"
        if missing:
            label += f"  ·  ⚠️ missing: {', '.join(missing)}"

        with st.expander(label, expanded=True):

            # Name first, then metrics
            base_cols    = ["Name", "Last", "Daily %", "MTD %", "YTD %", "1YR %", "Drawdown"]
            year_cols    = [f"{y} %" for y in years]
            display_cols = [c for c in base_cols + year_cols if c in block.columns]
            pct_cols     = [c for c in display_cols if "%" in c and c != "Drawdown"]
            dd_cols      = ["Drawdown"] if "Drawdown" in display_cols else []

            fmt = {"Last": "{:.2f}"}
            fmt.update({c: "{:.2%}" for c in pct_cols})
            fmt.update({c: "{:.2%}" for c in dd_cols})

            styled = (
                block[display_cols]
                .style
                .format(fmt, na_rep="—")
                .background_gradient(subset=pct_cols, cmap="RdYlGn", vmin=-0.15, vmax=0.15)
                .background_gradient(subset=dd_cols,  cmap="RdYlGn_r", vmin=-0.30, vmax=0.0)
            )

            st.dataframe(styled, use_container_width=True)


# ============================================================
# VIEW: PRICE CHARTS
# ============================================================

# ============================================================
# VIEW: PRICE CHARTS (Plotly — interactive)
# ============================================================

elif view_mode == "📊 Price Charts":
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    st.subheader("Price Charts with Moving Averages")
    st.caption("Hover to see exact values · Scroll to zoom · Drag to pan · Double-click to reset")

    available_tickers = [t for t in all_tickers if t in prices.columns]
    selected = st.multiselect(
        "Select tickers",
        options=available_tickers,
        default=[t for t in ["SPY", "GLD", "GDX", "EEM", "XLE", "UUP", "DBC", "EWZ"] if t in available_tickers]
    )

    ma_fast = st.slider("Fast MA", min_value=10, max_value=100, value=50, step=5)
    ma_slow = st.slider("Slow MA", min_value=50, max_value=300, value=200, step=10)

    # Layout: 2 columns of charts
    # Each chart is a self-contained Plotly figure
    chart_cols = st.columns(2)

    for i, t in enumerate(selected):
        s = prices[t].dropna()
        name = ticker_names.get(t, t)

        # go.Figure() is the Plotly equivalent of plt.subplots()
        # Instead of ax.plot() you use fig.add_trace()
        # Each trace is a line, bar, or other element added to the chart
        fig = go.Figure()

        # Price line
        fig.add_trace(go.Scatter(
            x=s.index, y=s,
            name="Price",
            line=dict(color="#60a5fa", width=2),
            hovertemplate="%{x|%d %b %Y}<br>$%{y:.2f}<extra></extra>"
        ))

        # Fast MA
        if len(s) >= ma_fast:
            ma_f = s.rolling(ma_fast).mean()
            fig.add_trace(go.Scatter(
                x=ma_f.index, y=ma_f,
                name=f"MA{ma_fast}",
                line=dict(color="#fbbf24", width=1.2, dash="dot"),
                hovertemplate=f"MA{ma_fast}: $%{{y:.2f}}<extra></extra>"
            ))

        # Slow MA
        if len(s) >= ma_slow:
            ma_s = s.rolling(ma_slow).mean()
            fig.add_trace(go.Scatter(
                x=ma_s.index, y=ma_s,
                name=f"MA{ma_slow}",
                line=dict(color="#f87171", width=1.2, dash="dash"),
                hovertemplate=f"MA{ma_slow}: $%{{y:.2f}}<extra></extra>"
            ))

        # layout() controls everything matplotlib did with set_facecolor,
        # tick_params, set_title etc — but in one clean dict
        fig.update_layout(
            title=dict(text=f"<b>{t}</b>  {name}", font=dict(size=12, color="#e2e8f0")),
            paper_bgcolor="#0d1117",
            plot_bgcolor="#0d1117",
            font=dict(color="#94a3b8", size=10),
            legend=dict(
                orientation="h", yanchor="bottom", y=1.01,
                bgcolor="rgba(0,0,0,0)", font=dict(size=9)
            ),
            xaxis=dict(
                gridcolor="#1e293b", showgrid=True,
                rangeslider=dict(visible=False),  # cleaner without the range slider
            ),
            yaxis=dict(gridcolor="#1e293b", showgrid=True, tickprefix="$"),
            hovermode="x unified",   # all traces show on hover at the same x position
            margin=dict(l=10, r=10, t=40, b=10),
            height=320,
        )

        with chart_cols[i % 2]:
            # st.plotly_chart() replaces st.pyplot()
            # use_container_width=True makes it fill the column
            st.plotly_chart(fig, use_container_width=True)

    if not selected:
        st.info("Select tickers above to display charts.")


# ============================================================
# VIEW: RATIO CHARTS (Plotly — interactive)
# ============================================================

elif view_mode == "📐 Ratio Charts":
    import plotly.graph_objects as go

    st.subheader("Relative Performance Ratios")
    st.caption("Rising = numerator outperforming. Green shading = above MA200 (thesis on). Red = below (thesis stalling).")

    ratio_chart_cols = st.columns(2)

    for i, (label, (num, den)) in enumerate(MACRO_RATIOS.items()):
        if num not in prices.columns or den not in prices.columns:
            with ratio_chart_cols[i % 2]:
                missing = num if num not in prices.columns else den
                st.warning(f"{label} — missing: {missing}")
            continue

        ratio = (prices[num] / prices[den]).dropna()
        ma50  = ratio.rolling(50).mean()  if len(ratio) >= 50  else None
        ma200 = ratio.rolling(200).mean() if len(ratio) >= 200 else None

        fig = go.Figure()

        # Green fill above MA200, red fill below — shows trend direction at a glance
        if ma200 is not None:
            fig.add_trace(go.Scatter(
                x=ratio.index, y=ratio,
                fill=None, mode="lines",
                line=dict(color="#60a5fa", width=0),
                showlegend=False, hoverinfo="skip"
            ))
            fig.add_trace(go.Scatter(
                x=ma200.index, y=ma200,
                fill="tonexty",
                fillcolor="rgba(74,222,128,0.08)",
                mode="none", name="_fill", showlegend=False, hoverinfo="skip"
            ))

        # Ratio line (on top of fill)
        fig.add_trace(go.Scatter(
            x=ratio.index, y=ratio,
            name="Ratio",
            line=dict(color="#60a5fa", width=1.8),
            hovertemplate="%{x|%d %b %Y}<br>%{y:.4f}<extra></extra>"
        ))

        if ma50 is not None:
            fig.add_trace(go.Scatter(
                x=ma50.index, y=ma50,
                name="MA50",
                line=dict(color="#fbbf24", width=1.2, dash="dot"),
                hovertemplate="MA50: %{y:.4f}<extra></extra>"
            ))

        if ma200 is not None:
            fig.add_trace(go.Scatter(
                x=ma200.index, y=ma200,
                name="MA200",
                line=dict(color="#f87171", width=1.2, dash="dash"),
                hovertemplate="MA200: %{y:.4f}<extra></extra>"
            ))

        fig.update_layout(
            title=dict(text=f"<b>{label}</b>", font=dict(size=11, color="#e2e8f0")),
            paper_bgcolor="#0d1117",
            plot_bgcolor="#0d1117",
            font=dict(color="#94a3b8", size=9),
            legend=dict(
                orientation="h", yanchor="bottom", y=1.01,
                bgcolor="rgba(0,0,0,0)", font=dict(size=8)
            ),
            xaxis=dict(gridcolor="#1e293b", showgrid=True),
            yaxis=dict(gridcolor="#1e293b", showgrid=True),
            hovermode="x unified",
            margin=dict(l=10, r=10, t=36, b=10),
            height=300,
        )

        with ratio_chart_cols[i % 2]:
            st.plotly_chart(fig, use_container_width=True)


# ============================================================
# VIEW: HEATMAP
# ============================================================

elif view_mode == "🟩 Heatmap":

    st.subheader(f"Return Heatmap — {sort_by}")

    col = sort_by
    if col in monitor_table.columns:
        heat = monitor_table[[col]].dropna().sort_values(col, ascending=False)
        values = heat[col].values
        colors = ["#2ecc71" if v >= 0 else "#e74c3c" for v in values]

        fig, ax = plt.subplots(figsize=(12, max(5, len(heat) * 0.38)))
        bars = ax.barh(heat.index, values * 100, color=colors, edgecolor="none", height=0.7)
        ax.axvline(0, color="white", linewidth=0.8, alpha=0.4)

        # Label each bar with its value
        for bar, val in zip(bars, values):
            xpos = bar.get_width() + (0.1 if val >= 0 else -0.1)
            align = "left" if val >= 0 else "right"
            ax.text(xpos, bar.get_y() + bar.get_height()/2,
                    f"{val*100:.1f}%", va="center", ha=align,
                    color="white", fontsize=7.5)

        ax.set_xlabel(f"{col} (%)", color="#94a3b8")
        ax.set_facecolor("#0d1117")
        fig.patch.set_facecolor("#0d1117")
        ax.tick_params(colors="#94a3b8", labelsize=8)
        ax.spines[:].set_color("#334155")
        ax.invert_yaxis()
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)


# ============================================================
# VIEW: CURRENCIES
# ============================================================

elif view_mode == "💱 Currencies":
    import plotly.graph_objects as go

    st.subheader("💱 G10 + SGD vs USD")
    st.caption(
        "All pairs expressed as USD per 1 unit of foreign currency. "
        "**Rising = that currency strengthening vs USD.** "
        "A falling USD (your thesis) should show most pairs rising."
    )

    # ── Build returns table for FX ────────────────────────────
    if not fx_data:
        st.error("No FX data loaded. Check your yfinance connection.")
    else:
        # Compute returns for each currency
        fx_rows = []
        for ccy, s in fx_data.items():
            s = safe_index(s.dropna())
            if s.empty:
                continue
            last_dt   = s.index.max()
            mtd_start = pd.Timestamp(year=last_dt.year, month=last_dt.month, day=1)
            ytd_start = pd.Timestamp(year=last_dt.year, month=1, day=1)
            fx_rows.append({
                "CCY":      ccy,
                "Name":     FX_PAIRS[ccy]["name"],
                "Spot":     round(float(s.iloc[-1]), 4),
                "Daily %":  pct_from(s, s.index[-2]) if len(s) > 1 else float("nan"),
                "MTD %":    pct_from(s, mtd_start),
                "YTD %":    pct_from(s, ytd_start),
                "1YR %":    pct_1yr(s),
            })

        fx_table = pd.DataFrame(fx_rows).set_index("CCY")
        fx_table = fx_table.sort_values(sort_by, ascending=False)

        # ── Scorecard: how many ccys are strengthening vs USD
        strengthening = int((fx_table["MTD %"] > 0).sum())
        weakening     = int((fx_table["MTD %"] < 0).sum())
        avg_fx_mtd    = fx_table["MTD %"].mean()

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric(
                "Strengthening vs USD (MTD)",
                strengthening,
                delta=f"of {strengthening + weakening}",
                delta_color="off"
            )
        with c2:
            st.metric(
                "Weakening vs USD (MTD)",
                weakening,
                delta=f"of {strengthening + weakening}",
                delta_color="off"
            )
        with c3:
            st.metric(
                "Avg G10 MTD vs USD",
                f"{avg_fx_mtd*100:.2f}%",
                delta=f"{avg_fx_mtd*100:.2f}%"
            )

        # ── Thesis signal note
        if strengthening >= 8:
            st.success(f"✅ {strengthening}/11 currencies strengthening vs USD — broad dollar weakness, thesis supported")
        elif strengthening >= 5:
            st.warning(f"⚠️ {strengthening}/11 currencies strengthening vs USD — mixed USD picture")
        else:
            st.error(f"❌ Only {strengthening}/11 currencies strengthening vs USD — USD holding firm, thesis under pressure")

        st.divider()

        # ── Returns table with colour gradient
        pct_display = ["Daily %", "MTD %", "YTD %", "1YR %"]
        fmt = {"Spot": "{:.4f}"}
        fmt.update({c: "{:.2%}" for c in pct_display})

        styled = (
            fx_table[["Name", "Spot"] + pct_display]
            .style
            .format(fmt, na_rep="—")
            .background_gradient(subset=pct_display, cmap="RdYlGn", vmin=-0.05, vmax=0.05)
        )
        st.dataframe(styled, use_container_width=True)

        st.divider()

        # ── Plotly charts — 2 column grid, one per currency
        st.subheader("Spot Rate Charts vs USD")
        st.caption("MA50 = dotted yellow · MA200 = dashed red · Rising = stronger vs USD")

        chart_cols = st.columns(2)
        for i, (ccy, s) in enumerate(fx_data.items()):
            s = safe_index(s.dropna())
            if s.empty:
                continue

            name = FX_PAIRS[ccy]["name"]
            fig  = go.Figure()

            # Price line
            fig.add_trace(go.Scatter(
                x=s.index, y=s,
                name="Spot",
                line=dict(color="#60a5fa", width=2),
                hovertemplate="%{x|%d %b %Y}<br>%{y:.4f}<extra></extra>"
            ))

            # MA50
            if len(s) >= 50:
                ma50 = s.rolling(50).mean()
                fig.add_trace(go.Scatter(
                    x=ma50.index, y=ma50,
                    name="MA50",
                    line=dict(color="#fbbf24", width=1.2, dash="dot"),
                    hovertemplate="MA50: %{y:.4f}<extra></extra>"
                ))

            # MA200 + shading
            if len(s) >= 200:
                ma200 = s.rolling(200).mean()

                # Shade fill — green above MA200, shows ccy trending stronger
                fig.add_trace(go.Scatter(
                    x=s.index, y=s,
                    fill=None, mode="lines",
                    line=dict(color="rgba(0,0,0,0)", width=0),
                    showlegend=False, hoverinfo="skip"
                ))
                fig.add_trace(go.Scatter(
                    x=ma200.index, y=ma200,
                    fill="tonexty",
                    fillcolor="rgba(74,222,128,0.07)",
                    mode="none", showlegend=False, hoverinfo="skip"
                ))

                fig.add_trace(go.Scatter(
                    x=ma200.index, y=ma200,
                    name="MA200",
                    line=dict(color="#f87171", width=1.2, dash="dash"),
                    hovertemplate="MA200: %{y:.4f}<extra></extra>"
                ))

            # Current return vs start of period
            period_return = pct_from(s, pd.Timestamp(start_date))
            title_color   = "#4ade80" if period_return >= 0 else "#f87171"
            arrow         = "▲" if period_return >= 0 else "▼"

            fig.update_layout(
                title=dict(
                    text=f"<b>{ccy}</b>  {name}  "
                         f"<span style='color:{title_color};font-size:11px'>"
                         f"{arrow} {period_return*100:.1f}% since {start_date}</span>",
                    font=dict(size=12, color="#e2e8f0")
                ),
                paper_bgcolor="#0d1117",
                plot_bgcolor="#0d1117",
                font=dict(color="#94a3b8", size=9),
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.01,
                    bgcolor="rgba(0,0,0,0)", font=dict(size=8)
                ),
                xaxis=dict(gridcolor="#1e293b", showgrid=True),
                yaxis=dict(gridcolor="#1e293b", showgrid=True,
                           tickformat=".4f"),
                hovermode="x unified",
                margin=dict(l=10, r=10, t=50, b=10),
                height=300,
            )

            with chart_cols[i % 2]:
                st.plotly_chart(fig, use_container_width=True)
