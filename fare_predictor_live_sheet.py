
import streamlit as st
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
import time

def load_sheet(sheet_url, sheet_name, credentials_json):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_json, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_url(sheet_url).worksheet(sheet_name)
    df = pd.DataFrame(sheet.get_all_records())
    return df

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

def generate_blurb(cf, sf, occ, dp):
    change = round(sf - cf, 2)
    direction = "increase" if change > 0 else "decrease"
    return (
        f"Dear Operator,\n\n"
        f"Based on current occupancy levels of {occ}% and a demand percentile of {dp}%, "
        f"our pricing model recommends a fare {direction} from ₹{cf} to ₹{sf}.\n\n"
        f"This adjustment is expected to optimize seat fill and improve revenue.\n\n"
        f"Regards,\nPricing Intelligence Team"
    )

st.set_page_config(page_title="Bus Fare Predictor (Live from Sheet)", layout="centered")
st.title("🚌 Bus Fare Predictor - Live Google Sheet Integration")

sheet_url = st.text_input("Google Sheet URL")
sheet_name = st.text_input("Sheet Name", value="Sheet1")
credentials_json = st.file_uploader("Upload Google Service Account JSON", type="json")
refresh = st.checkbox("🔄 Auto-refresh every 30 seconds")

if sheet_url and sheet_name and credentials_json:
    with open("temp_creds.json", "wb") as f:
        f.write(credentials_json.getbuffer())

    while True:
        try:
            df = load_sheet(sheet_url, sheet_name, "temp_creds.json")
            if not df.empty:
                st.write("✅ Data Loaded")
                operator_list = df["operator"].unique().tolist()
                selected_operator = st.selectbox("Select Bus Operator", operator_list)
                service_ids = df[df["operator"] == selected_operator]["service_id"].tolist()
                selected_service_id = st.selectbox("Select Service ID", service_ids)

                selected_row = df[(df["operator"] == selected_operator) & (df["service_id"] == selected_service_id)]

                if not selected_row.empty:
                    row = selected_row.iloc[0]
                    fare, confidence, reason = predict_optimal_fare(
                        row["current_fare"], row["occupancy"],
                        row["market_min"], row["market_max"], row["demand_percentile"]
                    )
                    st.success(f"Suggested Fare: ₹{fare}")
                    st.info(f"Confidence: {confidence}")
                    st.warning(f"Reason: {reason}")
                    blurb = generate_blurb(row["current_fare"], fare, row["occupancy"], row["demand_percentile"])
                    st.text_area("📨 Operator Blurb", blurb, height=200)
            else:
                st.warning("No data found in sheet.")
        except Exception as e:
            st.error(f"Error loading sheet: {e}")

        if not refresh:
            break
        time.sleep(30)
        st.rerun()
