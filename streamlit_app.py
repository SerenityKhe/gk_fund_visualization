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
    
    # Validated Tickers:
    # ^VIX: Cboe Volatility Index
    # ^IRX: 13-week Treasury Bill (Interest Rate Proxy)
    tickers = ["^VIX", "^IRX"]
    
    raw = yf.download(tickers, start=start, end=end)['Close']
    
    df = raw.rename(columns={
        '^VIX': 'VIX',
        '^IRX': 'Interest_Rate'
    }).ffill()
    
    return df

try:
    data = load_validated_data()

    # Create figure with Dual Y-Axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # 1. VIX Index (Dark Blue Line) - Primary Axis (LEFT)
    # This remains the core 'fear gauge' metric for your analysis
    fig.add_trace(
        go.Scatter(
            x=data.index, y=data['VIX'], 
            name="VIX Volatility Index", 
            line=dict(color='#003366', width=2.5)
        ),
        secondary_y=False,
    )

    # 2. FIXED: Effective Rate (Orange Line) - Secondary Axis (RIGHT)
    # Using 'shape=hv' to show the stepped nature of policy moves
    fig.add_trace(
        go.Scatter(
            x=data.index, y=data['Interest_Rate'], 
            name="Effective Rate Proxy (%)", 
            line=dict(color='#ef8a17', width=3, shape='hv') 
        ),
        secondary_y=True,
    )

    # --- Structural Breaks (Vertical Regimes) ---
    # Shaded regions defining the thesis study periods
    regimes = [
        {"start": "2019-01-01", "end": "2020-01-31", "label": "Pre-COVID Baseline<br>(2019)", "color": "rgba(173, 216, 230, 0.4)"},
        {"start": "2020-02-01", "end": "2021-12-31", "label": "Pandemic & Stimulus Regime", "color": "rgba(255, 192, 203, 0.4)"},
        {"start": "2022-01-01", "end": "2024-12-31", "label": "Monetary Tightening / Post-COVID Regime", "color": "rgba(144, 238, 144, 0.3)"}
    ]

    for r in regimes:
        fig.add_vrect(
            x0=r['start'], x1=r['end'],
            fillcolor=r['color'], opacity=1, layer="below", line_width=1.5, line_color="black",
            annotation_text=r['label'], annotation_position="top left",
            annotation_font=dict(size=13, color="black", family="Arial Black")
        )

    # --- Precise Callout Annotations ---
    # COVID-19 Lockdown
    fig.add_annotation(
        x="2020-03-16", y=82.69,
        text="COVID-19 Lockdown /<br>VIX Peak (~82)",
        showarrow=True, arrowhead=2, ax=70, ay=-50,
        bgcolor="white", bordercolor="black", secondary_y=False
    )

    # Vaccine Announcement
    fig.add_annotation(
        x="2020-11-09", y=40,
        text="Vaccine Announcement<br>(Value Rotation)",
        showarrow=True, arrowhead=2, ax=40, ay=-60,
        bgcolor="white", bordercolor="black", secondary_y=False
    )

    # First Fed Rate Hike
    fig.add_annotation(
        x="2022-03-16", y=0.5,
        text="First Fed Rate Hike<br>(End of 'Cheap Money')",
        showarrow=True, arrowhead=2, ax=-80, ay=-40,
        bgcolor="white", bordercolor="black", secondary_y=True
    )

    # --- Layout & Scaling Fix ---
    fig.update_layout(
        xaxis=dict(showgrid=True, gridcolor='lightgrey', range=["2019-01-01", "2025-01-01"]),
        template="plotly_white",
        height=900,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        margin=dict(l=60, r=60, t=120, b=60)
    )

    # FIXED: Scale ranges adjusted for clarity and zero-baseline visibility
    # VIX Axis (Left)
    fig.update_yaxes(title_text="<b>VIX Volatility Index</b>", secondary_y=False, range=[0, 105], color="#003366")
    
    # Interest Rate Axis (Right)
    fig.update_yaxes(title_text="<b>Effective Federal Funds Rate (%)</b>", secondary_y=True, range=[0, 6], color="#ef8a17")

    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Error: {e}")