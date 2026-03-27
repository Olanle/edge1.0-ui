import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# ── Page Config ──────────────────────────────────────────
st.set_page_config(
    page_title="Smart Home Energy Predictor",
    page_icon="⚡",
    layout="centered"
)

# ── Session State for History ─────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []

# ── Title ─────────────────────────────────────────────────
st.title("⚡ Smart Home Energy Predictor")
st.markdown("### Nigerian Home — Power Source Decision System")
st.markdown("Fill in the current readings below and click **Predict** to get the next hour's energy forecast and recommended power source.")
st.divider()

# ── Input Form ────────────────────────────────────────────
st.subheader("🔌 Power Meter Readings")
col1, col2 = st.columns(2)

with col1:
    Global_active_power   = st.number_input("Global Active Power (kW)",    min_value=0.0, value=1.5,   step=0.1)
    Global_reactive_power = st.number_input("Global Reactive Power (kW)",  min_value=0.0, value=0.1,   step=0.01)
    Voltage               = st.number_input("Voltage (V)",                 min_value=0.0, value=234.5, step=0.1)
    Global_intensity      = st.number_input("Global Intensity (A)",        min_value=0.0, value=6.4,   step=0.1)
    Sub_metering_1        = st.number_input("Sub Metering 1 - Kitchen (Wh)",    min_value=0.0, value=0.0,  step=1.0)

with col2:
    Sub_metering_2        = st.number_input("Sub Metering 2 - Laundry (Wh)",   min_value=0.0, value=1.0,  step=1.0)
    Sub_metering_3        = st.number_input("Sub Metering 3 - AC/Heater (Wh)", min_value=0.0, value=16.0, step=1.0)
    lag_1h                = st.number_input("Consumption 1 Hour Ago (kW)",     min_value=0.0, value=1.4,  step=0.1)
    lag_24h               = st.number_input("Consumption 24 Hours Ago (kW)",   min_value=0.0, value=1.6,  step=0.1)
    lag_168h              = st.number_input("Consumption 1 Week Ago (kW)",     min_value=0.0, value=1.3,  step=0.1)

st.divider()
st.subheader("🕐 Time Information")
col3, col4 = st.columns(2)

with col3:
    hour        = st.slider("Hour of Day",               min_value=0, max_value=23, value=18)
    day_of_week = st.slider("Day of Week (0=Mon, 6=Sun)", min_value=0, max_value=6,  value=2)
    month       = st.slider("Month",                     min_value=1, max_value=12,  value=7)

with col4:
    is_weekend       = st.selectbox("Is Weekend?", options=[0, 1], format_func=lambda x: "Yes" if x else "No")
    is_daytime       = st.selectbox("Is Daytime?", options=[0, 1], format_func=lambda x: "Yes" if x else "No")
    rolling_mean_24h = st.number_input("Rolling Mean 24h (kW)", min_value=0.0, value=1.45, step=0.01)
    rolling_std_24h  = st.number_input("Rolling Std 24h (kW)",  min_value=0.0, value=0.30, step=0.01)

st.divider()
st.subheader("🔋 Power Source Status")
col5, col6 = st.columns(2)

with col5:
    grid_available  = st.selectbox("Grid Available?",   options=[0, 1], format_func=lambda x: "Yes ✅" if x else "No ❌")
    solar_available = st.selectbox("Solar Available?",  options=[0, 1], format_func=lambda x: "Yes ✅" if x else "No ❌")
    gen_active      = st.selectbox("Generator Active?", options=[0, 1], format_func=lambda x: "Yes ✅" if x else "No ❌")

with col6:
    solar_battery_level = st.slider("Solar Battery Level (%)",  min_value=0.0, max_value=100.0, value=60.0)
    gen_fuel_level      = st.slider("Generator Fuel Level (%)", min_value=0.0, max_value=100.0, value=80.0)

st.divider()

# ── Predict Button ────────────────────────────────────────
if st.button("⚡ Predict Next Hour Consumption", width='stretch'):
    payload = {
        "Global_active_power"  : Global_active_power,
        "Global_reactive_power": Global_reactive_power,
        "Voltage"              : Voltage,
        "Global_intensity"     : Global_intensity,
        "Sub_metering_1"       : Sub_metering_1,
        "Sub_metering_2"       : Sub_metering_2,
        "Sub_metering_3"       : Sub_metering_3,
        "hour"                 : hour,
        "day_of_week"          : day_of_week,
        "month"                : month,
        "is_weekend"           : is_weekend,
        "is_daytime"           : is_daytime,
        "solar_available"      : solar_available,
        "grid_available"       : grid_available,
        "gen_active"           : gen_active,
        "lag_1h"               : lag_1h,
        "lag_24h"              : lag_24h,
        "lag_168h"             : lag_168h,
        "rolling_mean_24h"     : rolling_mean_24h,
        "rolling_std_24h"      : rolling_std_24h,
        "solar_battery_level"  : solar_battery_level,
        "gen_fuel_level"       : gen_fuel_level
    }

    try:
        headers  = {"access_token": "project3.0"}
        response = requests.post("https://edge1-0-api.onrender.com/predict", json=payload, headers=headers)
        result   = response.json()

        st.divider()
        st.subheader("📊 Prediction Results")

        # Prediction value
        st.metric(
            label="Predicted Next Hour Consumption",
            value=f"{result['predicted_next_hour_consumption_kw']} kW"
        )

        # Power source decision
        source  = result["recommended_power_source"]
        message = result["action_message"]

        if source == "GRID":
            st.success(f"⚡ Recommended Source: **{source}**\n\n{message}")
        elif source == "SOLAR":
            st.info(f"☀️ Recommended Source: **{source}**\n\n{message}")
        elif source == "GENERATOR":
            st.warning(f"⛽ Recommended Source: **{source}**\n\n{message}")
        else:
            st.error(f"🚨 Recommended Source: **{source}**\n\n{message}")

        # ── Save to history ───────────────────────────────
        st.session_state.history.append({
            "Prediction #"      : len(st.session_state.history) + 1,
            "Predicted (kW)"    : result["predicted_next_hour_consumption_kw"],
            "Power Source"      : source,
            "Hour"              : hour,
            "Grid"              : "Yes" if grid_available else "No",
            "Solar Battery (%)" : solar_battery_level,
            "Gen Fuel (%)"      : gen_fuel_level,
        })

    except Exception as e:
        st.error(f"Could not connect to API. Make sure the FastAPI server is running.\n\nError: {e}")

# ── Prediction History & Chart ────────────────────────────
if len(st.session_state.history) > 0:
    st.divider()
    st.subheader("📈 Consumption Trend")

    df_history = pd.DataFrame(st.session_state.history)

    # Line chart
    fig = px.line(
        df_history,
        x="Prediction #",
        y="Predicted (kW)",
        color="Power Source",
        markers=True,
        title="Predicted Energy Consumption Over Multiple Predictions",
        labels={"Predicted (kW)": "Consumption (kW)", "Prediction #": "Prediction"},
        color_discrete_map={
            "GRID"         : "#00CC96",
            "SOLAR"        : "#636EFA",
            "GENERATOR"    : "#FFA15A",
            "LOAD_SHEDDING": "#EF553B"
        }
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="white",
        legend_title="Power Source"
    )
    st.plotly_chart(fig, use_container_width=True)

    # History table
    st.subheader("🗂️ Prediction History")
    st.dataframe(df_history, width='stretch')

    # Clear history button
    if st.button("🗑️ Clear History", width='stretch'):
        st.session_state.history = []
        st.rerun()