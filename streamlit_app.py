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

    try:
        # Add user agent and more robust download settings for Streamlit Cloud
        raw = yf.download(
            tickers,
            start=start,
            end=end,
            progress=False,  # Disable progress bar for cloud deployment
            threads=False    # Disable threading for stability
        )["Close"]

        if raw.empty or raw.isna().all().all():
            raise ValueError("No data retrieved from yfinance")

        df = raw.rename(columns={"^VIX": "VIX", "^IRX": "Interest_Rate"}).ffill()
        df.index = pd.to_datetime(df.index)

        # Validate that we have VIX data
        if "VIX" not in df.columns or df["VIX"].isna().all():
            raise ValueError("VIX data is missing or all NaN")

        return df

    except Exception as e:
        st.error(f"Failed to load data from Yahoo Finance: {e}")
        # Create fallback synthetic data for demonstration
        dates = pd.date_range(start=start, end=end, freq='D')
        # Create realistic VIX-like data
        np.random.seed(42)  # For reproducible results
        vix_data = []
        current_vix = 20
        for i in range(len(dates)):
            if "2020-03" in str(dates[i]):  # COVID spike
                current_vix = min(80, current_vix * 1.1 + np.random.normal(0, 5))
            elif "2020-04" <= str(dates[i]) <= "2021-12":  # Recovery
                current_vix = max(15, current_vix * 0.99 + np.random.normal(0, 2))
            else:  # Normal times
                current_vix = max(10, min(50, current_vix + np.random.normal(0, 1)))
            vix_data.append(max(8, current_vix))

        # Create interest rate data with more dramatic changes
        ir_data = []
        current_ir = 2.5  # Start at 2.5%
        for i, date in enumerate(dates):
            date_str = str(date)
            if "2020-03" <= date_str <= "2021-12":  # COVID low rates
                if "2020-03" <= date_str <= "2020-06":  # Sharp drop to zero
                    current_ir = max(0.1, current_ir * 0.95)
                else:  # Stay low
                    current_ir = max(0.1, min(0.5, current_ir + np.random.normal(0, 0.05)))
            elif date_str >= "2022-03":  # Aggressive rate hikes starting March 2022
                if "2022-03" <= date_str <= "2023-12":  # Hiking cycle
                    current_ir = min(5.5, current_ir * 1.002 + np.random.normal(0, 0.1))
                else:  # Recent period
                    current_ir = max(4.0, min(5.5, current_ir + np.random.normal(0, 0.05)))
            else:  # Pre-COVID normal
                current_ir = max(1.5, min(3.0, current_ir + np.random.normal(0, 0.02)))
            ir_data.append(max(0.1, current_ir))

        fallback_df = pd.DataFrame({
            "VIX": vix_data,
            "Interest_Rate": ir_data
        }, index=dates)

        st.warning("⚠️ Using fallback synthetic data due to Yahoo Finance connection issues")
        return fallback_df

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

    # Debug information
    st.write("**Data Debug Info:**")
    st.write(f"Data shape: {data.shape}")
    st.write(f"Columns: {list(data.columns)}")
    st.write(f"VIX range: {data['VIX'].min():.2f} - {data['VIX'].max():.2f}")
    st.write(f"Interest Rate range: {data['Interest_Rate'].min():.2f} - {data['Interest_Rate'].max():.2f}")
    st.write("Sample data:")
    st.write(data.head())

    # Create figure with Dual Y-Axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # 1) VIX (Primary axis) - Dark blue color and thick line
    fig.add_trace(
        go.Scatter(
            x=data.index,
            y=data["VIX"],
            name="VIX Volatility Index",
            line=dict(color="#003366", width=4),  # Dark blue, thick line
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
            "color": "rgba(144,238,144,0.18)",  # LightGreen
        },
        {
            "start": "2020-02-01",
            "end": "2021-12-31",
            "label": "Pandemic & Stimulus Regime",
            "color": "rgba(255,160,122,0.18)",  # LightSalmon
        },
        {
            "start": "2022-01-01",
            "end": "2024-12-31",
            "label": "Monetary Tightening / Post-COVID Regime",
            "color": "rgba(135,206,250,0.18)",  # LightSkyBlue
        },
    ]

    for r in regimes:
        fig.add_vrect(
            x0=r["start"],
            x1=r["end"],
            fillcolor=r["color"],
            opacity=1,
            layer="below",
            line_width=0,
            annotation_text=r["label"],
            annotation_position="top left",
            annotation_font=dict(size=13, color="black", family="Arial Black"),
        )

    # Add vertical dashed lines at regime boundaries
    regime_boundaries = ["2020-02-01", "2022-01-01"]
    for boundary in regime_boundaries:
        fig.add_vline(
            x=boundary,
            line_width=2,
            line_dash="dash",
            line_color="black",
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
        color="#003366",  # Match the dark blue VIX line
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
