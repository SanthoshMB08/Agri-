import base64
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from groq import Groq 
import os
from pdf import generate_pdf

import requests
from streamlit_js_eval import streamlit_js_eval

from wether import get_geolocation, reverse_geocode, get_temperature, get_soil_and_moisture



# Load crop requirement data (already generated)
crop_df = pd.read_csv("crop_requirements.csv")
load_dotenv() 
GROQ_API_KEY = os.getenv("api_key")
groq_client = Groq(api_key=GROQ_API_KEY)

def get_ai_suggestion(prompt):
    try:
        response = groq_client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {"role": "system", "content": "You are an expert agricultural advisor."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {str(e)}"

# --- Streamlit App UI ---
st.set_page_config(page_title="Smart Crop Advisor", layout="wide")
def set_background(image_path,side):
    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    with open(side, "rb") as f:
        encoded1 = base64.b64encode(f.read()).decode()
        #background-size: cover;
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpeg;base64,{encoded}");
            
            background-repeat: no-repeat;
            background-position: center;
        }}
        
        /* Sidebar background */
        section[data-testid="stSidebar"] {{
            background-image: url("data:image/jpeg;base64,{encoded1}");
            background-size: cover;
            background-repeat: no-repeat;
            background-position: center;
        }}

        /* Optional: make sidebar text bold/colored */
        section[data-testid="stSidebar"] .css-1d391kg {{
            color: black;
            font-weight: bold;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

image_path = os.path.join("temps", "agri.jpg") 
side=os.path.join("temps", "side.jpg") 
set_background(image_path,side)
st.title("🌾 Smart Crop Advisor - AI Powered")

option = st.sidebar.selectbox("Select Mode", [
    "1. Suggest Crop from Soil & Weather",
    "2. Crop Info & Fertilizer Advice",
    "3. Suitability Check"
])
if option.startswith("1"):
    st.header("1️⃣ Suggest Crops Based on Soil and Weather (Improved Matching)")
    soil = st.selectbox("Soil Type", crop_df["Preferred_Soil_Types"].str.split(", ").explode().unique())
    moisture = st.slider("Soil Moisture (%)", 0, 100, 25)
    temp = st.slider("Temperature (°C)", 0, 50, 30)
     # --- Section: Auto-fetch using location ---
    st.subheader("📍 Auto-fill Soil, Moisture & Temp from Location")

  

    if st.button("📍 Fetch by Location"):
        
        lat,lon= get_geolocation()
        st.write(lat,lon)
        if lat and lon:
           
            district = reverse_geocode(lat, lon)
         
            temperature = get_temperature(lat, lon)
            st.write(temperature)
            soil, moisture = get_soil_and_moisture(district)

            if all([district, soil, moisture, temperature]):
                st.success(f"✅ Location Detected: **{district}**")
                st.markdown(f"- **Soil Type:** `{soil}`")
                st.markdown(f"- **Moisture Level:** `{moisture}%`")
                st.markdown(f"- **Temperature:** `{temperature}°C`")

                # These will be used to populate the main inputs
                soil = soil
                moisture = moisture
                temp = temperature
            else:
                st.warning("⚠️ Could not fetch complete data for this location.")
        else:
            st.error("❌ Failed to get location. Please allow access or try again.")

    def calculate_match(row):
        score = 0

        # Soil type
        if soil.lower() in row["Preferred_Soil_Types"].lower():
            score += 40

        # Moisture score
        moisture_diff = abs(moisture - row["Ideal_Moisture_Level (%)"])
        if moisture_diff <= 5:
            score += 30
        elif moisture_diff <= 10:
            score += 20
        elif moisture_diff <= 15:
            score += 10

        # Temperature score
        if pd.notna(row["Temp_Min"]) and pd.notna(row["Temp_Max"]):
            if row["Temp_Min"] <= temp <= row["Temp_Max"]:
                score += 30
            elif abs(temp - row["Temp_Min"]) <= 5 or abs(temp - row["Temp_Max"]) <= 5:
                score += 20
            elif abs(temp - row["Temp_Min"]) <= 10 or abs(temp - row["Temp_Max"]) <= 10:
                score += 10

        return score

    if st.button("Suggest Crops"):
        crop_df["Match Score"] = crop_df.apply(calculate_match, axis=1)
        result = crop_df.sort_values(by="Match Score", ascending=False).head(5)
        st.success(f"Top {len(result)} crop suggestions based on your input:")
        st.dataframe(result[["Crop", "Match Score", "Ideal_Moisture_Level (%)", "Preferred_Soil_Types", "Temperature_Range (°C)"]])

        prompt = f"Suggest how to improve crop yield for soil type {soil}, moisture {moisture}%, temperature {temp}°C."
        st.subheader("AI Suggestion to Improve Yield")
        suggestion= get_ai_suggestion(prompt)
        st.info(suggestion)
        user_input = f"Soil Type: {soil}\nMoisture: {moisture}%\nTemperature: {temp}°C"
        match_data = result.to_string(index=False)
        
    # 🔻 Button that triggers PDF generation and download
        st.download_button(
        label="📄 Download Report",
        data=generate_pdf("Crop Suggestion Report", user_input, match_data, suggestion),
        file_name="crop_suggestion.pdf",
        mime="application/pdf"
         )
# --- 2. Crop Info ---
elif option.startswith("2"):
    st.header("2️⃣ Crop Requirements and Fertilizer Suggestions")
    crop = st.selectbox("Select Crop", crop_df["Crop"])

    row = crop_df[crop_df["Crop"] == crop].iloc[0]
    st.markdown(f"**Soil:** {row['Preferred_Soil_Types']}")
    st.markdown(f"**Moisture Level:** {row['Ideal_Moisture_Level (%)']}%")
    st.markdown(f"**Temperature:** {row['Temperature_Range (°C)']}")
    st.markdown(f"**Rainfall:** {row['Rainfall_Need (mm/year)']}")

    st.subheader("AI Fertilizer Suggestion")
    prompt = f"What type of fertilizers are best for growing {crop} in {row['Preferred_Soil_Types']} soil?"
    suggestion = get_ai_suggestion(prompt)
    st.info(suggestion)
   
    user_input = f"Crop: {crop}"
    match_data = f"Preferred Soil: {row['Preferred_Soil_Types']}\nIdeal Moisture Level: {row['Ideal_Moisture_Level (%)']}%\nTemperature Range: {row['Temperature_Range (°C)']}" 
 # 🔻 Button that triggers PDF generation and download
    st.download_button(
    label="📄 Download Report",
        data=generate_pdf("Crop Suggestion Report", user_input, match_data, suggestion),
        file_name="crop_suggestion.pdf",
        mime="application/pdf"
         )

# --- 3. Suitability Check ---
else:
    st.header("3️⃣ Crop & Soil Suitability Checker")
    crop = st.selectbox("Select Crop", crop_df["Crop"])
    soil = st.selectbox("Soil Type", crop_df["Preferred_Soil_Types"].str.split(", ").explode().unique())
    moisture = st.slider("Soil Moisture (%)", 0, 100, 25)
    temp = st.slider("Temperature (°C)", 0, 50, 30)

    row = crop_df[crop_df["Crop"] == crop].iloc[0]
    match = 0

    if soil in row['Preferred_Soil_Types']:
        match += 40
    if abs(moisture - row['Ideal_Moisture_Level (%)']) <= 5:
        match += 30
    tmin=int(row['Temp_Min'])
    tmax=int(row['Temp_Max'])
    #tmin, tmax = map(int, row['Temperature_Range (°C)'].split('-'))
    if tmin <= temp <= tmax:
        match += 30

    st.subheader("Suitability Result")
    st.metric("Suitability Match %", f"{match}%")
    if match >= 70:
        var="✅ Suitable for this crop"
        st.success(var)
    else:
        var="❌ Not suitable for this crop"
        st.warning(var)

    prompt = f"The user wants to grow {crop} in {soil} soil with {moisture}% moisture and {temp}°C temperature. Suggest improvements."
    st.subheader("AI Suggestions for Improvement")
    suggestion = get_ai_suggestion(prompt)
    st.info(suggestion)
    user_input = f"Crop: {crop}\nSoil Type: {soil}\nMoisture: {moisture}%\nTemperature: {temp}°C"
    match_data=var
    # 🔻 Button that triggers PDF generation and download
    st.download_button(
    label="📄 Download Report",
        data=generate_pdf("Crop Suggestion Report", user_input, match_data, suggestion),
        file_name="crop_suggestion.pdf",
        mime="application/pdf"
         )
