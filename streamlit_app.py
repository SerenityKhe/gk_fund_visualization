import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- Page Setup ---
st.set_page_config(page_title="Thesis: Macro Regime Definition", layout="wide")
st.title("📊 Visualization Techniques: Macroeconomic Regime Definition")

@st.cache_data
def load_validated_data():
    start = "2019-01-01"
    end = "2024-12-31"

    # ^VIX: Cboe Volatility Index
    # ^IRX: 13-week Treasury Bill (Interest Rate Proxy)
    tickers = ["^VIX", "^IRX"]

    raw = yf.download(tickers, start=start, end=end)["Close"]

    df = raw.rename(columns={"^VIX": "VIX", "^IRX": "Interest_Rate"}).ffill()
    df.index = pd.to_datetime(df.index)
    return df

def nearest_trading_day(idx: pd.DatetimeIndex, date_str: str) -> pd.Timestamp:
    """
    Snap a calendar date to the nearest available trading day in the downloaded series.
    This prevents annotations from landing on non-trading days and avoids hard-coded y-values.
    """
    target = pd.to_datetime(date_str)
    pos = idx.get_indexer([target], method="nearest")[0]
    return idx[pos]

try:
    data = load_validated_data()

    # Create figure with Dual Y-Axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # 1) VIX (Primary axis)
    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["VIX"],
            name="VIX Volatility Index",
            line=dict(color="#003366", width=2.5),
        ),
        secondary_y=False,
    )

    # 2) Interest rate proxy (Secondary axis)
    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["Interest_Rate"],
            name="Effective Rate Proxy (%)",
            line=dict(color="#ef8a17", width=3, shape="hv"),
        ),
        secondary_y=True,
    )

    # --- Structural Breaks (Vertical Regimes) ---
    regimes = [
        {
            "start": "2019-01-01",
            "end": "2020-01-31",
            "label": "Pre-COVID Baseline<br>(2019)",
            "color": "rgba(173, 216, 230, 0.4)",
        },
        {
            "start": "2020-02-01",
            "end": "2021-12-31",
            "label": "Pandemic & Stimulus Regime",
            "color": "rgba(255, 192, 203, 0.4)",
        },
        {
            "start": "2022-01-01",
            "end": "2024-12-31",
            "label": "Monetary Tightening / Post-COVID Regime",
            "color": "rgba(144, 238, 144, 0.3)",
        },
    ]

    for r in regimes:
        fig.add_vrect(
            x0=r["start"],
            x1=r["end"],
            fillcolor=r["color"],
            opacity=1,
            layer="below",
            line_width=1.5,
            line_color="black",
            annotation_text=r["label"],
            annotation_position="top left",
            annotation_font=dict(size=13, color="black", family="Arial Black"),
        )

    # --- Corrected + data-driven annotations (no hard-coded y) ---
    # Dates are the canonical anchors; y-values are taken from your downloaded series.
    events = [
        {
            "date": "2020-03-16",  # VIX all-time high close (COVID shock)
            "series": "VIX",
            "secondary_y": False,
            "text": "COVID market shock<br>VIX all-time high close (~82.69)",
            "ax": 70,
            "ay": -50,
        },
        {
            "date": "2020-11-09",  # Pfizer/BioNTech vaccine efficacy headline
            "series": "VIX",
            "secondary_y": False,
            "text": "Vaccine efficacy announcement<br>(risk-on / value rotation)",
            "ax": 40,
            "ay": -60,
        },
    ]

    for ev in events:
        x_dt = nearest_trading_day(data.index, ev["date"])
        y_val = float(data.loc[x_dt, ev["series"]])

        fig.add_annotation(
            x=x_dt,
            y=y_val,
            text=ev["text"],
            showarrow=True,
            arrowhead=2,
            ax=ev["ax"],
            ay=ev["ay"],
            bgcolor="white",
            bordercolor="black",
            secondary_y=ev["secondary_y"],
        )

    # --- Layout & Scaling ---
    fig.update_layout(
        xaxis=dict(showgrid=True, gridcolor="lightgrey", range=["2019-01-01", "2025-01-01"]),
        template="plotly_white",
        height=900,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        margin=dict(l=60, r=60, t=120, b=60),
    )

    fig.update_yaxes(
        title_text="<b>VIX Volatility Index</b>",
        secondary_y=False,
        range=[0, 105],
        color="#003366",
    )

    fig.update_yaxes(
        title_text="<b>Effective Federal Funds Rate (%)</b>",
        secondary_y=True,
        range=[0, 6],
        color="#ef8a17",
    )

    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Error: {e}")
