"""
Static universe of tickers for the screener.

Curated from Nifty 50 + a handful of large-cap names beyond it. Static for V1;
in V2 we'd pull the constituent list dynamically from NSE/BSE.
"""

# Nifty 50 (approximate, as of 2025-26). Stable enough for a Sunday project.
NIFTY_50 = [
    "ADANIENT.NS", "ADANIPORTS.NS", "APOLLOHOSP.NS", "ASIANPAINT.NS", "AXISBANK.NS",
    "BAJAJ-AUTO.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS", "BEL.NS", "BHARTIARTL.NS",
    "BPCL.NS", "BRITANNIA.NS", "CIPLA.NS", "COALINDIA.NS", "DRREDDY.NS",
    "EICHERMOT.NS", "GRASIM.NS", "HCLTECH.NS", "HDFCBANK.NS", "HDFCLIFE.NS",
    "HEROMOTOCO.NS", "HINDALCO.NS", "HINDUNILVR.NS", "ICICIBANK.NS", "INDUSINDBK.NS",
    "INFY.NS", "ITC.NS", "JSWSTEEL.NS", "KOTAKBANK.NS", "LT.NS",
    "M&M.NS", "MARUTI.NS", "NESTLEIND.NS", "NTPC.NS", "ONGC.NS",
    "POWERGRID.NS", "RELIANCE.NS", "SBILIFE.NS", "SBIN.NS", "SHRIRAMFIN.NS",
    "SUNPHARMA.NS", "TATACONSUM.NS", "TATAMOTORS.NS", "TATASTEEL.NS", "TCS.NS",
    "TECHM.NS", "TITAN.NS", "TRENT.NS", "ULTRACEMCO.NS", "WIPRO.NS",
]

# A few additional large-cap names you might want to scan beyond Nifty 50.
EXTRAS = [
    "DMART.NS", "PIDILITIND.NS", "GODREJCP.NS", "DABUR.NS", "HAVELLS.NS",
    "DIVISLAB.NS", "LTIM.NS", "AMBUJACEM.NS", "ADANIGREEN.NS", "ZOMATO.NS",
    "PAYTM.NS", "NYKAA.NS", "POLICYBZR.NS", "IRCTC.NS", "IRFC.NS",
    "BANKBARODA.NS", "PNB.NS", "CANBK.NS", "IDFCFIRSTB.NS", "FEDERALBNK.NS",
]

ALL_TICKERS = NIFTY_50 + EXTRAS
