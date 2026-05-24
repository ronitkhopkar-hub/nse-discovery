"""Shared formatting helpers for NSE Discovery."""

import pandas as pd


def fmt_money_inr(val) -> str:
    """Format a money value in INR using lakhs, crores, and lakh crores."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "—"
    try:
        val = float(val)
    except (TypeError, ValueError):
        return "—"
    if val >= 1e12:  # 1 lakh crore = 10^12
        return f"₹{val / 1e12:,.2f} L Cr"
    if val >= 1e7:  # 1 crore = 10^7
        return f"₹{val / 1e7:,.2f} Cr"
    if val >= 1e5:  # 1 lakh = 10^5
        return f"₹{val / 1e5:,.2f} L"
    return f"₹{val:,.2f}"


def fmt_pct(val, already_pct: bool = False) -> str:
    """Format a fraction (0.0125) or percent (1.25) as '1.25%'."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "—"
    try:
        val = float(val)
    except (TypeError, ValueError):
        return "—"
    return f"{val:.2f}%" if already_pct else f"{val * 100:.2f}%"


def fmt_ratio(val, decimals: int = 2) -> str:
    """Format a unit-less ratio (P/E, debt/equity, etc.)."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "—"
    try:
        return f"{float(val):.{decimals}f}"
    except (TypeError, ValueError):
        return "—"


def fmt_price(val) -> str:
    """Format a per-share price in INR."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "—"
    try:
        return f"₹{float(val):,.2f}"
    except (TypeError, ValueError):
        return "—"
