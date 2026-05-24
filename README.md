# NSE Discovery

A small discovery and analysis tool for stocks listed on the NSE and BSE. Built as a Sunday learning project — Python, Streamlit, Git, GitHub, Claude Code.

## Stack

- Python 3.14
- Streamlit (web UI, mobile-responsive)
- yfinance (free market data with ~15 min delay)
- pandas, numpy (analysis)
- plotly (interactive charts)

## Local setup (Windows)

Open PowerShell in the project folder:

    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt
    streamlit run app.py

Streamlit opens automatically at http://localhost:8501.

## Features (V1)

- Enter any NSE/BSE ticker (e.g. `RELIANCE.NS`, `TCS.NS`, `ASIANPAINT.BO`)
- Price chart with 50/200-day moving averages, RSI, MACD
- Fundamentals snapshot: P/E, P/B, market cap, debt/equity, ROE
- Simple screener filtering NSE stocks by user-defined criteria

## Out of scope (for now)

- Trade execution (no broker API integration)
- Real-time tick data (yfinance is delayed)
- User accounts / persistence

## Deployment

Public deployment on Streamlit Community Cloud. Auto-deploys on push to `main`.
