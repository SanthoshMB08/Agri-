import streamlit as st
import pandas as pd
import requests
from streamlit_js_eval import get_geolocation
import os
import geocoder


# Load your district-wise soil/moisture data
district_df = pd.read_csv("district.csv")

# Get your weather API key (from OpenWeatherMap)
WEATHER_API_KEY = os.getenv("weather_api")
def get_geolocation():
    try:
        response = requests.get("https://ipinfo.io/json")
        data = response.json()
        loc = data.get("loc")  # format: "latitude,longitude"
        if loc:
            lat, lon = map(float, loc.split(','))
            return lat, lon
    except:
        return None
def reverse_geocode(lat, lon):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat={lat}&lon={lon}"
        headers = {"User-Agent": "agro/1.0 (santhoshmb08@gamil.com)"}
        res = requests.get(url, headers=headers)
        
        if res.status_code != 200:
            print(f"Error: HTTP {res.status_code} for reverse geocode request")
            print("Response content:", res.text)
            return None
        
        data = res.json()  # Now safe to parse
        address = data.get("address", {})

        district = address.get("state_district") or address.get("district") or address.get("county")
        return district
    except Exception as e:
        print("Error in reverse_geocode:", e)
        return None


def get_temperature(lat, lon):
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric"
    try:
        response = requests.get(url).json()
        return response['main']['temp']
    except:
        return None

def get_soil_and_moisture(district):
    row = district_df[district_df["DistrictName"].str.lower() == district.lower()]
    if not row.empty:
        return row.iloc[0]["Soil_Type"], row.iloc[0]["Moisture_Percentage"]
    return None, None
print(reverse_geocode(12.9719, 77.5937) ) # Example coordinates for Bangalore