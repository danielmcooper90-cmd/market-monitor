# ============================================================
# config.py — Universe & Taxonomy
# ============================================================
# Structure:
#   UNIVERSE  — full hierarchy: asset class → region → group → tickers
#   FX_PAIRS  — G10 + Asia/EM pairs with yfinance tickers + invert flag
#   MACRO_RATIOS — named ratio pairs for relative value charts
#   CROSS_ASSET  — flat list of cross-asset proxies for the waterfall chart
#   THESIS_SIGNALS — the 4 confirmation signals for the USD down-cycle thesis
#   KNOWN_DIFFICULT — tickers expected to fail or have limited data
#
# To add a ticker: find the right group and append.
# To add a group:  add a new key under the relevant region.
# To add a region: add a new key under the relevant asset class.
# Nothing else needs to change in the app.
# ============================================================


# ============================================================
# UNIVERSE
# Nested dict: Asset Class → Region → Group → [tickers]
# ============================================================

UNIVERSE = {

    # ──────────────────────────────────────────────────────
    # EQUITIES
    # ──────────────────────────────────────────────────────
    "Equities": {

        "USA": {
            "Benchmarks": [
                "SPY",   # S&P 500
                "QQQ",   # Nasdaq 100
                "IWM",   # Russell 2000 small cap
                "RSP",   # S&P 500 equal weight — breadth signal
                "DIA",   # Dow Jones
            ],
            "Sectors": [
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
            "Style / Factor": [
                "IVE",   # S&P 500 Value
                "IVW",   # S&P 500 Growth
                "VTV",   # Vanguard Value
                "VUG",   # Vanguard Growth
                "MTUM",  # Momentum factor
                "QUAL",  # Quality factor
                "USMV",  # Low volatility
            ],
        },

        "Europe": {
            "Broad": [
                "VGK",   # Vanguard Europe broad
                "EFA",   # MSCI EAFE
                "IEFA",  # iShares Core EAFE
                "EFV",   # EAFE Value
            ],
            "Country": [
                "EWG",   # Germany
                "EWU",   # United Kingdom
                "EWP",   # Spain
                "EWI",   # Italy
                "EWQ",   # France
                "EWN",   # Netherlands
                "EWK",   # Belgium
                "EWD",   # Sweden
                "EPOL",  # Poland
                "EWO",   # Austria
            ],
        },

        "Asia-Pacific": {
            "Broad": [
                "EWJ",   # Japan (Topix proxy)
                "AAXJ",  # Asia ex-Japan
            ],
            "Country": [
                "EWA",   # Australia
                "EWS",   # Singapore
                "EWH",   # Hong Kong
                "EWT",   # Taiwan
                "EWY",   # South Korea
                "INDA",  # India
            ],
        },

        "Emerging Markets": {
            "Broad": [
                "EEM",   # iShares MSCI EM (most liquid)
                "IEMG",  # iShares Core EM
                "VWO",   # Vanguard EM
            ],
            "LatAm": [
                "ILF",   # Latin America 40
                "EWZ",   # Brazil
                "EWW",   # Mexico
                "ECH",   # Chile
                "EPU",   # Peru
            ],
            "EM Asia": [
                "MCHI",  # China MSCI
                "FXI",   # China large cap
                "EWT",   # Taiwan
                "EWY",   # South Korea
                "INDA",  # India
                "VNM",   # Vietnam
            ],
            "EM EMEA": [
                "TUR",   # Turkey
                "EPOL",  # Poland
                "EGPT",  # Egypt
                "KSA",   # Saudi Arabia
            ],
        },

        "Global": {
            "Benchmarks": [
                "ACWI",  # MSCI All World (incl. US)
                "ACWX",  # MSCI All World ex-US
            ],
        },

    },

    # ──────────────────────────────────────────────────────
    # FIXED INCOME
    # ──────────────────────────────────────────────────────
    "Fixed Income": {

        "USA": {
            "Treasuries": [
                "SHY",   # 1-3yr (2Y proxy)
                "IEI",   # 3-7yr
                "IEF",   # 7-10yr (10Y proxy)
                "TLH",   # 10-20yr
                "TLT",   # 20yr+ (long end)
            ],
            "Real Rates": [
                "TIP",   # TIPS broad
                "SCHP",  # Schwab TIPS
            ],
            "Credit — IG": [
                "LQD",   # iShares IG Corp
                "VCIT",  # Vanguard IG Corp
            ],
            "Credit — HY": [
                "HYG",   # iShares High Yield
                "JNK",   # SPDR High Yield
            ],
        },

        "Europe": {
            "Government": [
                "IBTE",  # German Bunds (short)
                "IBTM",  # Euro IG broad
            ],
        },

        "Emerging Markets": {
            "Sovereign": [
                "EMB",   # EM sovereign USD
                "LEMB",  # EM local currency
            ],
        },

        "Global": {
            "Broad": [
                "AGG",   # US Aggregate
                "BND",   # Vanguard Total Bond
            ],
        },

    },

    # ──────────────────────────────────────────────────────
    # COMMODITIES
    # ──────────────────────────────────────────────────────
    "Commodities": {

        "Global": {
            "Broad": [
                "DBC",   # DB Commodity basket
                "PDBC",  # Invesco Optimum Yield Commodities
            ],
            "Energy": [
                "USO",   # WTI Crude Oil
                "UNG",   # Natural Gas
                "XLE",   # US Energy sector
                "XOP",   # Oil & Gas E&P
            ],
            "Metals — Precious": [
                "GLD",   # Gold
                "SLV",   # Silver
                "PPLT",  # Platinum
            ],
            "Metals — Industrial": [
                "CPER",  # Copper
                "DBB",   # Base metals basket
                "XME",   # Metals & Mining equity
            ],
            "Agriculture": [
                "DBA",   # Agriculture basket
                "WEAT",  # Wheat
                "CORN",  # Corn
                "SOYB",  # Soybeans
            ],
        },

    },

    # ──────────────────────────────────────────────────────
    # REAL ASSETS
    # ──────────────────────────────────────────────────────
    "Real Assets": {

        "USA": {
            "REITs": [
                "VNQ",   # Vanguard US REITs
                "XLRE",  # S&P Real Estate sector
            ],
        },

        "Global": {
            "REITs": [
                "RWX",   # SPDR Global ex-US REITs
                "VNQI",  # Vanguard Global ex-US REITs
            ],
            "Infrastructure": [
                "IGF",   # iShares Global Infrastructure
                "IFRA",  # US Infrastructure
            ],
        },

    },

    # ──────────────────────────────────────────────────────
    # CRYPTO
    # ──────────────────────────────────────────────────────
    "Crypto": {

        "Global": {
            "Major": [
                "BTC-USD",  # Bitcoin
                "ETH-USD",  # Ethereum
            ],
        },

    },

}


# ============================================================
# FX PAIRS
# All expressed as "USD per 1 unit of foreign currency"
# so RISING always means that currency STRENGTHENING vs USD.
#
# invert=True  → yfinance quotes as USDXXX, we flip it
# invert=False → yfinance quotes as XXXUSD, use as-is
# ============================================================

FX_PAIRS = {

    # G10
    "EUR": {"ticker": "EURUSD=X", "invert": False, "name": "Euro",               "region": "G10"},
    "GBP": {"ticker": "GBPUSD=X", "invert": False, "name": "British Pound",      "region": "G10"},
    "JPY": {"ticker": "JPY=X",    "invert": True,  "name": "Japanese Yen",       "region": "G10"},
    "CHF": {"ticker": "CHF=X",    "invert": True,  "name": "Swiss Franc",        "region": "G10"},
    "AUD": {"ticker": "AUDUSD=X", "invert": False, "name": "Australian Dollar",  "region": "G10"},
    "CAD": {"ticker": "CAD=X",    "invert": True,  "name": "Canadian Dollar",    "region": "G10"},
    "NZD": {"ticker": "NZDUSD=X", "invert": False, "name": "New Zealand Dollar", "region": "G10"},
    "NOK": {"ticker": "NOK=X",    "invert": True,  "name": "Norwegian Krone",    "region": "G10"},
    "SEK": {"ticker": "SEK=X",    "invert": True,  "name": "Swedish Krona",      "region": "G10"},
    "DKK": {"ticker": "DKK=X",    "invert": True,  "name": "Danish Krone",       "region": "G10"},

    # Asia / EM
    "SGD": {"ticker": "SGD=X",    "invert": True,  "name": "Singapore Dollar",   "region": "Asia/EM"},
    "CNH": {"ticker": "CNH=X",    "invert": True,  "name": "Chinese Renminbi",   "region": "Asia/EM"},
    "KRW": {"ticker": "KRW=X",    "invert": True,  "name": "Korean Won",         "region": "Asia/EM"},
    "INR": {"ticker": "INR=X",    "invert": True,  "name": "Indian Rupee",       "region": "Asia/EM"},
    "BRL": {"ticker": "BRL=X",    "invert": True,  "name": "Brazilian Real",     "region": "Asia/EM"},
    "MXN": {"ticker": "MXN=X",    "invert": True,  "name": "Mexican Peso",       "region": "Asia/EM"},

}


# ============================================================
# MACRO RATIOS
# Rising = numerator outperforming denominator.
# Grouped by theme.
# ============================================================

MACRO_RATIOS = {

    # ── Core thesis confirmation
    "ACWX / SPY  — RoW vs US":           ("ACWX", "SPY"),
    "EEM  / SPY  — EM vs US":            ("EEM",  "SPY"),
    "EFA  / SPY  — DM ex-US vs US":      ("EFA",  "SPY"),
    "UUP  / SPY  — USD strength":        ("UUP",  "SPY"),

    # ── Hard asset signals
    "GLD  / SPY  — Gold vs US":          ("GLD",  "SPY"),
    "GDX  / GLD  — Miners vs Gold":      ("GDX",  "GLD"),
    "DBC  / SPY  — Commodities vs US":   ("DBC",  "SPY"),
    "CPER / GLD  — Copper/Gold ratio":   ("CPER", "GLD"),

    # ── EM regional
    "ILF  / EEM  — LatAm vs EM":         ("ILF",  "EEM"),
    "AAXJ / EEM  — Asia vs EM":          ("AAXJ", "EEM"),
    "EWZ  / SPY  — Brazil vs US":        ("EWZ",  "SPY"),

    # ── US internals
    "IVE  / IVW  — Value vs Growth":     ("IVE",  "IVW"),
    "RSP  / SPY  — Equal vs Cap Weight": ("RSP",  "SPY"),
    "XLE  / SPY  — Energy vs US":        ("XLE",  "SPY"),
    "HYG  / TLT  — Risk-on vs Risk-off": ("HYG",  "TLT"),
    "MTUM / SPY  — Momentum vs Market":  ("MTUM", "SPY"),
    "QUAL / SPY  — Quality vs Market":   ("QUAL", "SPY"),

    # ── Fixed income
    "LQD  / TLT  — IG vs Rates":         ("LQD",  "TLT"),
    "HYG  / LQD  — HY vs IG":           ("HYG",  "LQD"),
    "EMB  / LQD  — EM vs IG":           ("EMB",  "LQD"),
    "TIP  / TLT  — Real vs Nominal":    ("TIP",  "TLT"),

}


# ============================================================
# CROSS-ASSET WATERFALL
# Flat list used in the Cross-Asset tab ranked returns chart.
# Label is the display name.
# ============================================================

CROSS_ASSET = {
    # Equities
    "SPY":   "US Equities (SPY)",
    "QQQ":   "US Tech (QQQ)",
    "IWM":   "US Small Cap (IWM)",
    "ACWX":  "RoW Equities (ACWX)",
    "EEM":   "EM Equities (EEM)",
    "EFA":   "DM ex-US (EFA)",
    "VGK":   "Europe (VGK)",
    "EWJ":   "Japan (EWJ)",
    "EWZ":   "Brazil (EWZ)",
    "INDA":  "India (INDA)",
    # Fixed Income
    "TLT":   "US 20yr Treasury",
    "IEF":   "US 7-10yr Treasury",
    "SHY":   "US 2yr Treasury",
    "TIP":   "TIPS (Real Rates)",
    "HYG":   "US High Yield",
    "LQD":   "US IG Credit",
    "EMB":   "EM Bonds (USD)",
    # Commodities
    "DBC":   "Broad Commodities",
    "GLD":   "Gold",
    "SLV":   "Silver",
    "CPER":  "Copper",
    "USO":   "Crude Oil",
    "UNG":   "Natural Gas",
    # FX / Real Rates
    "UUP":   "USD (DXY proxy)",
    # Real Assets
    "VNQ":   "US REITs",
    # Crypto
    "BTC-USD": "Bitcoin",
}


# ============================================================
# THESIS SIGNALS
# The 4 confirmation signals for the USD down-cycle thesis.
# bearish_is_good=True  → falling price confirms thesis (UUP)
# bearish_is_good=False → rising price confirms thesis
# ============================================================

THESIS_SIGNALS = {
    "UUP": {"label": "USD (UUP)",         "bearish_is_good": True},
    "TIP": {"label": "TIPS (Real Rates)", "bearish_is_good": False},
    "DBC": {"label": "Commodities (DBC)", "bearish_is_good": False},
    "GLD": {"label": "Gold (GLD)",        "bearish_is_good": False},
}


# ============================================================
# KNOWN DIFFICULT TICKERS
# Expected to fail or have limited yfinance coverage.
# Flagged in the UI rather than surfaced as unexpected errors.
# ============================================================

KNOWN_DIFFICULT = [
    "IUKD", "IUKP",        # LSE-listed — need .L suffix
    "IBTE", "IBTM",        # European bond ETFs — limited yfinance history
    "PPLT",                # Platinum — sometimes thin
    "LEMB",                # EM local ccy bonds — data gaps
    "GXG",                 # Colombia — thin volume
    "FSLY",                # Correct ticker (was FASTLY in v2 — typo)
]


# ============================================================
# HELPERS — derived flat lists used by the app
# ============================================================

def all_tickers():
    """Flat deduplicated list of every equity/fi/commodity/crypto ticker."""
    seen = set()
    out  = []
    for asset_class in UNIVERSE.values():
        for region in asset_class.values():
            for group in region.values():
                for t in group:
                    if t not in seen:
                        seen.add(t)
                        out.append(t)
    return out


def tickers_for(asset_class=None, region=None, group=None):
    """
    Filtered flat ticker list.
    Examples:
        tickers_for("Equities")
        tickers_for("Equities", "USA")
        tickers_for("Equities", "USA", "Sectors")
    """
    src = UNIVERSE
    if asset_class:
        src = {asset_class: src[asset_class]} if asset_class in src else {}
    out = []
    seen = set()
    for ac_val in src.values():
        for reg_key, reg_val in ac_val.items():
            if region and reg_key != region:
                continue
            for grp_key, grp_val in reg_val.items():
                if group and grp_key != group:
                    continue
                for t in grp_val:
                    if t not in seen:
                        seen.add(t)
                        out.append(t)
    return out


def flat_groups():
    """
    Returns a flat dict of {display_label: [tickers]} for use in
    the returns table — preserves hierarchy in the label.
    e.g. "Equities › USA › Sectors": ["XLK", "XLF", ...]
    """
    out = {}
    for ac_key, ac_val in UNIVERSE.items():
        for reg_key, reg_val in ac_val.items():
            for grp_key, grp_val in reg_val.items():
                label = f"{ac_key}  ›  {reg_key}  ›  {grp_key}"
                out[label] = grp_val
    return out
