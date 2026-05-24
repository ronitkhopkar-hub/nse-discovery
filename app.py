"""
NSE Discovery - V1 (iteration 5.4)
Main page: ticker analysis with candlestick + indicators + fundamentals.
Screener lives in pages/1_Screener.py (auto-added to sidebar by Streamlit).

Data source: Yahoo Finance via yfinance (~15 min delayed).
"""

from datetime import date, timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf
from plotly.subplots import make_subplots

from formatters import fmt_money_inr, fmt_pct, fmt_ratio, fmt_price

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="NSE Discovery — Analysis",
    layout="wide",
)

st.title("NSE Discovery")
st.caption(
    "Discovery and analysis for NSE/BSE listed stocks. "
    "Data via Yahoo Finance (~15 min delayed). "
    "Use the sidebar to switch to the Screener."
)

# ---------------------------------------------------------------------------
# Sidebar inputs
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Inputs")

    ticker = st.text_input(
        "Ticker symbol",
        value="RELIANCE.NS",
        help="Use .NS for NSE, .BO for BSE. e.g. RELIANCE.NS, TCS.NS, ASIANPAINT.BO",
    ).strip().upper()

    period_options = {
        "3 Months": 90,
        "6 Months": 180,
        "1 Year": 365,
        "2 Years": 730,
        "5 Years": 1825,
    }
    period_label = st.selectbox(
        "Time period", list(period_options.keys()), index=2
    )
    display_days = period_options[period_label]

    st.markdown("---")
    st.caption(
        "Tip: Indian tickers need a suffix. NSE = `.NS`, BSE = `.BO`. "
        "For the 200-day MA to render, pick at least ~1 year."
    )


# ---------------------------------------------------------------------------
# Data fetch
# ---------------------------------------------------------------------------
@st.cache_data(ttl=900)
def fetch_history(ticker: str, end: date, display_days: int) -> pd.DataFrame:
    """Download OHLCV with extra history so 200 DMA exists at the chart's left edge."""
    fetch_start = end - timedelta(days=display_days + 300)
    df = yf.download(
        ticker, start=fetch_start, end=end,
        progress=False, auto_adjust=True,
    )
    if df.empty:
        return df
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] for col in df.columns]
    return df


@st.cache_data(ttl=3600)
def fetch_info(ticker: str) -> dict:
    """Fetch company fundamentals dict from Yahoo. Returns {} on failure."""
    try:
        return yf.Ticker(ticker).info or {}
    except Exception:
        return {}


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Compute 50 DMA, 200 DMA, RSI(14), MACD(12, 26, 9)."""
    df = df.copy()
    df["MA50"] = df["Close"].rolling(window=50).mean()
    df["MA200"] = df["Close"].rolling(window=200).mean()

    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1 / 14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / 14, adjust=False).mean()
    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))

    ema_fast = df["Close"].ewm(span=12, adjust=False).mean()
    ema_slow = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = ema_fast - ema_slow
    df["MACD_signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_hist"] = df["MACD"] - df["MACD_signal"]
    return df


# ---------------------------------------------------------------------------
# Main view
# ---------------------------------------------------------------------------
if not ticker:
    st.info("Enter a ticker symbol in the sidebar to begin.")
    st.stop()

end_date = date.today()

with st.spinner(f"Fetching {ticker}..."):
    full_df = fetch_history(ticker, end_date, display_days)
    info = fetch_info(ticker)

if full_df.empty:
    st.error(
        f"No data returned for `{ticker}`. "
        "Check the symbol — use `.NS` for NSE and `.BO` for BSE."
    )
    st.stop()

full_df = add_indicators(full_df)
display_start = pd.Timestamp(end_date - timedelta(days=display_days))
df = full_df[full_df.index >= display_start]

# --- Headline metrics ------------------------------------------------------
current_price = float(df["Close"].iloc[-1])
prev_price = float(df["Close"].iloc[-2]) if len(df) > 1 else current_price
change = current_price - prev_price
pct_change = (change / prev_price) * 100 if prev_price else 0.0

current_rsi = float(df["RSI"].iloc[-1]) if not pd.isna(df["RSI"].iloc[-1]) else None
rsi_label = "Oversold" if current_rsi and current_rsi < 30 else (
    "Overbought" if current_rsi and current_rsi > 70 else "Neutral"
)

company_name = info.get("longName") or info.get("shortName") or ticker
st.subheader(company_name)

col1, col2, col3, col4 = st.columns(4)
col1.metric(
    "Last close", fmt_price(current_price),
    f"{change:+.2f} ({pct_change:+.2f}%)",
)
col2.metric("Period high", fmt_price(float(df["High"].max())))
col3.metric("Period low", fmt_price(float(df["Low"].min())))
col4.metric(
    "RSI (14)", f"{current_rsi:.1f}" if current_rsi is not None else "—",
    rsi_label, delta_color="off",
)

# --- Tabs ------------------------------------------------------------------
tab_chart, tab_fundamentals = st.tabs(["Chart", "Fundamentals"])

with tab_chart:
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        row_heights=[0.6, 0.2, 0.2],
        subplot_titles=("Price + 50/200 DMA", "RSI (14)", "MACD (12, 26, 9)"),
    )

    fig.add_trace(
        go.Candlestick(
            x=df.index, open=df["Open"], high=df["High"],
            low=df["Low"], close=df["Close"],
            name="Price", showlegend=False,
        ),
        row=1, col=1,
    )
    fig.add_trace(go.Scatter(x=df.index, y=df["MA50"], name="50 DMA",
                             line=dict(color="#ff9800", width=1.5)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["MA200"], name="200 DMA",
                             line=dict(color="#9c27b0", width=1.5)), row=1, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], name="RSI",
                             line=dict(color="#1976d2", width=1.5), showlegend=False),
                  row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="#d32f2f", line_width=1, row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="#388e3c", line_width=1, row=2, col=1)
    fig.update_yaxes(range=[0, 100], row=2, col=1)

    hist_colors = ["#26a69a" if v >= 0 else "#ef5350" for v in df["MACD_hist"].fillna(0)]
    fig.add_trace(go.Bar(x=df.index, y=df["MACD_hist"], name="Histogram",
                         marker_color=hist_colors, showlegend=False), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["MACD"], name="MACD",
                             line=dict(color="#1976d2", width=1.5)), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["MACD_signal"], name="Signal",
                             line=dict(color="#ff9800", width=1.5)), row=3, col=1)

    fig.update_layout(
        height=850,
        xaxis_rangeslider_visible=False,
        margin=dict(l=0, r=0, t=40, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
    )
    fig.update_yaxes(title_text="Price (INR)", row=1, col=1)
    fig.update_yaxes(title_text="RSI", row=2, col=1)
    fig.update_yaxes(title_text="MACD", row=3, col=1)

    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Raw data with indicators (last 20 bars)"):
        st.dataframe(
            df[["Open", "High", "Low", "Close", "Volume", "MA50", "MA200", "RSI", "MACD"]].tail(20),
            use_container_width=True,
        )

with tab_fundamentals:
    if not info:
        st.warning("No fundamentals returned by Yahoo for this ticker.")
    else:
        st.markdown("### Company")
        oc1, oc2 = st.columns(2)
        with oc1:
            st.write(f"**Sector:** {info.get('sector') or '—'}")
            st.write(f"**Industry:** {info.get('industry') or '—'}")
            st.write(f"**Country:** {info.get('country') or '—'}")
        with oc2:
            employees = info.get("fullTimeEmployees")
            st.write(f"**Employees:** {employees:,}" if employees else "**Employees:** —")
            website = info.get("website")
            st.write(f"**Website:** [{website}]({website})" if website else "**Website:** —")
            exchange = info.get("exchange") or info.get("fullExchangeName") or "—"
            st.write(f"**Exchange:** {exchange}")

        summary = info.get("longBusinessSummary")
        if summary:
            with st.expander("Business summary"):
                st.write(summary)

        st.markdown("---")
        st.markdown("### Valuation")
        v1, v2, v3, v4 = st.columns(4)
        v1.metric("Market cap", fmt_money_inr(info.get("marketCap")))
        v2.metric("P/E (TTM)", fmt_ratio(info.get("trailingPE")))
        v3.metric("Forward P/E", fmt_ratio(info.get("forwardPE")))
        v4.metric("P/B", fmt_ratio(info.get("priceToBook")))

        v5, v6, v7, v8 = st.columns(4)
        v5.metric("Enterprise value", fmt_money_inr(info.get("enterpriseValue")))
        v6.metric("EV / EBITDA", fmt_ratio(info.get("enterpriseToEbitda")))
        v7.metric("P/S (TTM)", fmt_ratio(info.get("priceToSalesTrailing12Months")))
        v8.metric("PEG ratio", fmt_ratio(info.get("trailingPegRatio") or info.get("pegRatio")))

        st.markdown("---")
        st.markdown("### Profitability")
        p1, p2, p3, p4 = st.columns(4)
        p1.metric("ROE", fmt_pct(info.get("returnOnEquity")))
        p2.metric("ROA", fmt_pct(info.get("returnOnAssets")))
        p3.metric("Profit margin", fmt_pct(info.get("profitMargins")))
        p4.metric("Operating margin", fmt_pct(info.get("operatingMargins")))

        st.markdown("---")
        st.markdown("### Balance sheet & yield")
        b1, b2, b3, b4 = st.columns(4)
        b1.metric("Debt / equity", fmt_ratio(info.get("debtToEquity")))
        b2.metric("Current ratio", fmt_ratio(info.get("currentRatio")))
        b3.metric("Dividend yield", fmt_pct(info.get("dividendYield"), already_pct=True))
        b4.metric("Payout ratio", fmt_pct(info.get("payoutRatio")))

        st.markdown("---")
        st.markdown("### Price reference")
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("52W high", fmt_price(info.get("fiftyTwoWeekHigh")))
        r2.metric("52W low", fmt_price(info.get("fiftyTwoWeekLow")))
        r3.metric("50-day avg", fmt_price(info.get("fiftyDayAverage")))
        r4.metric("Beta", fmt_ratio(info.get("beta")))

        target = info.get("targetMeanPrice")
        num_analysts = info.get("numberOfAnalystOpinions")
        if target and num_analysts:
            st.markdown("---")
            st.markdown("### Analyst view")
            a1, a2, a3, a4 = st.columns(4)
            upside = ((target - current_price) / current_price) * 100 if current_price else 0
            a1.metric("Target (mean)", fmt_price(target), f"{upside:+.1f}% upside")
            a2.metric("Target high", fmt_price(info.get("targetHighPrice")))
            a3.metric("Target low", fmt_price(info.get("targetLowPrice")))
            rec = info.get("recommendationKey") or "—"
            a4.metric("Consensus", rec.replace("_", " ").title(),
                      f"{num_analysts} analysts", delta_color="off")
