"""
Screener page: scan a static universe of NSE stocks and filter by
valuation, profitability, dividend yield, and momentum (RSI, vs 200 DMA).

First scan takes ~1-2 minutes (one Yahoo API hit per ticker). Results are
cached for 1 hour, so subsequent scans within the hour are instant.
"""

import pandas as pd
import streamlit as st
import yfinance as yf

from formatters import fmt_money_inr, fmt_pct, fmt_price, fmt_ratio
from tickers import ALL_TICKERS, NIFTY_50

st.set_page_config(
    page_title="Screener — NSE Discovery",
    layout="wide",
)

st.title("Screener")
st.caption(
    "Scan a static universe of large-cap NSE stocks and filter by valuation, "
    "profitability, dividend yield, and momentum."
)

# ---------------------------------------------------------------------------
# Sidebar: universe and filters
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Universe")
    universe_choice = st.radio(
        "Stocks to scan",
        ["Nifty 50", "Nifty 50 + extras (~70)"],
        index=0,
    )
    universe = NIFTY_50 if universe_choice == "Nifty 50" else ALL_TICKERS

    st.markdown("---")
    st.header("Filters")

    min_mcap_lcr = st.slider(
        "Min market cap (₹ lakh crore)",
        min_value=0.0, max_value=20.0, value=0.0, step=0.5,
        help="0 = no minimum. ₹1 lakh crore = ₹1 trillion.",
    )
    pe_max = st.slider(
        "Max P/E (TTM)",
        min_value=5, max_value=100, value=100, step=1,
        help="100 = no maximum. Negative-P/E stocks (losses) are excluded when a max is set.",
    )
    div_yield_min = st.slider(
        "Min dividend yield (%)",
        min_value=0.0, max_value=10.0, value=0.0, step=0.25,
    )
    roe_min = st.slider(
        "Min ROE (%)",
        min_value=-20.0, max_value=50.0, value=-20.0, step=1.0,
        help="-20 = no minimum.",
    )
    rsi_min, rsi_max = st.slider(
        "RSI (14) range",
        min_value=0, max_value=100, value=(0, 100),
    )
    above_200dma = st.checkbox("Price above 200 DMA only", value=False)


# ---------------------------------------------------------------------------
# Per-ticker fetch (cached individually for 1 hour)
# ---------------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_screener_row(ticker: str) -> dict:
    """
    Fetch info + recent price history for one ticker, returning a flat dict
    of the columns the screener needs. Errors return {'symbol': ..., 'error': ...}.
    """
    try:
        t = yf.Ticker(ticker)
        info = t.info or {}
        hist = t.history(period="14mo", auto_adjust=True)
        if hist.empty:
            return {"symbol": ticker, "error": "No price history"}

        close = hist["Close"]
        ma50 = close.rolling(50).mean().iloc[-1]
        ma200 = close.rolling(200).mean().iloc[-1]

        # RSI(14) with Wilder smoothing
        delta = close.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        avg_gain = gain.ewm(alpha=1 / 14, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1 / 14, adjust=False).mean()
        rs = avg_gain / avg_loss
        rsi_series = 100 - (100 / (1 + rs))
        rsi = rsi_series.iloc[-1]

        last_close = float(close.iloc[-1])
        prev_close = float(close.iloc[-2]) if len(close) > 1 else last_close
        day_chg_pct = ((last_close - prev_close) / prev_close * 100) if prev_close else 0.0

        return {
            "symbol": ticker,
            "name": info.get("shortName") or info.get("longName") or ticker,
            "sector": info.get("sector") or "—",
            "price": last_close,
            "day_chg_pct": day_chg_pct,
            "market_cap": info.get("marketCap"),
            "pe": info.get("trailingPE"),
            "pb": info.get("priceToBook"),
            "div_yield": info.get("dividendYield"),
            "roe": info.get("returnOnEquity"),
            "rsi": float(rsi) if not pd.isna(rsi) else None,
            "vs_50dma_pct": (
                (last_close - ma50) / ma50 * 100
                if pd.notna(ma50) and ma50 else None
            ),
            "vs_200dma_pct": (
                (last_close - ma200) / ma200 * 100
                if pd.notna(ma200) and ma200 else None
            ),
        }
    except Exception as e:
        return {"symbol": ticker, "error": str(e)}


# ---------------------------------------------------------------------------
# Run scan
# ---------------------------------------------------------------------------
col_run, col_clear = st.columns([1, 6])
with col_run:
    run = st.button("Run scan", type="primary", use_container_width=True)
with col_clear:
    if st.button("Clear cache", use_container_width=False):
        st.cache_data.clear()
        st.session_state.pop("scan_results", None)
        st.rerun()

if run:
    progress = st.progress(0.0, text="Starting scan...")
    rows = []
    errors = []
    for i, ticker in enumerate(universe):
        progress.progress(
            (i + 1) / len(universe),
            text=f"Fetching {ticker}  ({i + 1}/{len(universe)})",
        )
        row = fetch_screener_row(ticker)
        if "error" in row:
            errors.append(f"{row['symbol']}: {row['error']}")
        else:
            rows.append(row)
    progress.empty()

    st.session_state["scan_results"] = pd.DataFrame(rows)
    st.session_state["scan_errors"] = errors

if "scan_results" not in st.session_state:
    st.info(
        "Click **Run scan** to fetch fresh data. First scan takes ~1-2 minutes "
        "(one Yahoo API call per ticker). Results are cached per-ticker for 1 hour."
    )
    st.stop()

df = st.session_state["scan_results"].copy()

# ---------------------------------------------------------------------------
# Apply filters
# ---------------------------------------------------------------------------
mask = pd.Series([True] * len(df), index=df.index)

if min_mcap_lcr > 0:
    mask &= df["market_cap"].fillna(0) >= min_mcap_lcr * 1e12

if pe_max < 100:
    mask &= df["pe"].notna() & (df["pe"] > 0) & (df["pe"] <= pe_max)

if div_yield_min > 0:
    # yfinance returns dividendYield already as a percentage (e.g. 1.7 = 1.7%).
    mask &= df["div_yield"].fillna(0) >= div_yield_min

if roe_min > -20:
    mask &= df["roe"].notna() & (df["roe"] * 100 >= roe_min)

if rsi_min > 0 or rsi_max < 100:
    mask &= df["rsi"].notna() & df["rsi"].between(rsi_min, rsi_max)

if above_200dma:
    mask &= df["vs_200dma_pct"].notna() & (df["vs_200dma_pct"] > 0)

filtered = df[mask].copy()

# ---------------------------------------------------------------------------
# Render results
# ---------------------------------------------------------------------------
st.subheader(f"{len(filtered)} of {len(df)} stocks match")

if len(filtered) == 0:
    st.warning("No stocks pass the current filters. Loosen one or more filters in the sidebar.")
else:
    # Sort by market cap descending by default
    filtered = filtered.sort_values("market_cap", ascending=False, na_position="last")

    display = pd.DataFrame({
        "Symbol": filtered["symbol"].str.replace(".NS", "", regex=False),
        "Name": filtered["name"],
        "Sector": filtered["sector"],
        "Price": filtered["price"].apply(fmt_price),
        "Day %": filtered["day_chg_pct"].apply(
            lambda x: f"{x:+.2f}%" if pd.notna(x) else "—"
        ),
        "Market cap": filtered["market_cap"].apply(fmt_money_inr),
        "P/E": filtered["pe"].apply(fmt_ratio),
        "P/B": filtered["pb"].apply(fmt_ratio),
        "Div yld": filtered["div_yield"].apply(lambda x: fmt_pct(x, already_pct=True)),
        "ROE": filtered["roe"].apply(fmt_pct),
        "RSI": filtered["rsi"].apply(
            lambda x: f"{x:.1f}" if pd.notna(x) else "—"
        ),
        "vs 50DMA": filtered["vs_50dma_pct"].apply(
            lambda x: f"{x:+.1f}%" if pd.notna(x) else "—"
        ),
        "vs 200DMA": filtered["vs_200dma_pct"].apply(
            lambda x: f"{x:+.1f}%" if pd.notna(x) else "—"
        ),
    })

    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
        height=min(800, 60 + 35 * len(display)),
    )

    with st.expander("Raw numeric data (sortable, exportable)"):
        st.dataframe(filtered, use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
# Errors (if any)
# ---------------------------------------------------------------------------
errors = st.session_state.get("scan_errors", [])
if errors:
    with st.expander(f"{len(errors)} tickers failed to fetch"):
        for err in errors:
            st.text(err)
