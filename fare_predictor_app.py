
import streamlit as st

def predict_optimal_fare(current_fare, occupancy, market_fare_min, market_fare_max, demand_percentile):
    occ = occupancy / 100
    demand_factor = demand_percentile / 100

    if demand_factor >= 0.7 and occ <= 0.5:
        price_multiplier = 1.1 + (0.2 * (1 - occ))
        reason = "High demand, low occupancy → surge to capture value"
        confidence = "High"
    elif demand_factor <= 0.3 and occ >= 0.8:
        price_multiplier = 0.9 - (0.1 * occ)
        reason = "Low demand, high occupancy → reduce to boost occupancy"
        confidence = "Medium"
    else:
        price_multiplier = 1.0 + ((demand_factor - 0.5) * 0.2)
        reason = "Moderate demand → slight adjustment"
        confidence = "Medium"

    raw_price = current_fare * price_multiplier
    suggested_price = max(market_fare_min, min(raw_price, market_fare_max))

    return round(suggested_price, 2), confidence, reason

def generate_operator_blurb(current_fare, suggested_fare, occupancy, demand_percentile):
    change = round(suggested_fare - current_fare, 2)
    direction = "increase" if change > 0 else "decrease"
    blurb = (
        f"Dear Operator,\n\n"
        f"Based on current occupancy levels of {occupancy}% and a demand percentile of {demand_percentile}%, "
        f"our pricing model recommends a fare {direction} from ₹{current_fare} to ₹{suggested_fare}.\n\n"
        f"This adjustment is expected to optimize seat fill and improve revenue per service. "
        f"Our model considers market trends and real-time demand to ensure pricing aligns with competitor benchmarks "
        f"while maximizing your earnings.\n\n"
        f"We recommend applying this change proactively to capture upcoming demand.\n\n"
        f"Regards,\nPricing Intelligence Team"
    )
    return blurb

# Streamlit UI
st.set_page_config(page_title="Bus Fare Predictor", layout="centered")
st.title("🚌 Optimal Bus Fare Predictor")

with st.form("fare_form"):
    current_fare = st.number_input("Current Fare (₹)", value=600.0)
    occupancy = st.slider("Current Occupancy (%)", 0, 100, 45)
    market_fare_min = st.number_input("Market Fare Min (₹)", value=550.0)
    market_fare_max = st.number_input("Market Fare Max (₹)", value=750.0)
    demand_percentile = st.slider("Demand Percentile (0–100)", 0, 100, 80)
    submitted = st.form_submit_button("Predict Fare")

if submitted:
    fare, confidence, reason = predict_optimal_fare(
        current_fare, occupancy, market_fare_min, market_fare_max, demand_percentile
    )
    st.success(f"🔧 Suggested Fare: ₹{fare}")
    st.info(f"✅ Confidence Level: {confidence}")
    st.warning(f"📌 Reason: {reason}")

    blurb = generate_operator_blurb(current_fare, fare, occupancy, demand_percentile)
    st.markdown("### 🧾 Communication Blurb to Bus Operator")
    st.code(blurb)
