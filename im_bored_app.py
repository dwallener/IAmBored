import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz

# App setup
st.set_page_config(page_title="I'm Bored", page_icon="🎯")

# Debug: Confirm secret loads
#st.write("Token preview:", st.secrets.get("PREDICTHQ_TOKEN", "Not found")[:10] + "...")

st.title("🎯 I'm Bored")
st.subheader("Find real events near you, right now.")

# User input
city = st.text_input("Enter your city", "New York")

# Location resolution
lat = lon = None
location_info = ""
geo_data = None

if city:
    geo_url = "https://nominatim.openstreetmap.org/search"
    geo_params = {"q": city, "format": "json", "limit": 1}
    headers = {"User-Agent": "im-bored-app/0.1 (damir00@gmail.com)"}
    try:
        geo_resp = requests.get(geo_url, params=geo_params, headers=headers, timeout=5)
        if geo_resp.status_code == 200 and geo_resp.content:
            geo_data = geo_resp.json()
            if geo_data:
                lat = float(geo_data[0]["lat"])
                lon = float(geo_data[0]["lon"])
                location_info = geo_data[0]["display_name"]
                st.success(f"📍 Found: {location_info}")
            else:
                st.warning("❗ Could not find that city. Try a nearby one.")
        else:
            st.error("🌐 Location lookup failed. Try again in a moment.")
    except Exception as e:
        st.error(f"🌐 Error connecting to location service: {e}")
else:
    st.info("Enter a city to get started.")

# Continue if valid coordinates
if lat and lon:
    hours = st.selectbox("How many hours do you have?", [2, 4, 6, 8])
    if st.button("Find Events"):
        with st.spinner("Searching for events..."):
            now = datetime.utcnow()
            end_time = now + timedelta(hours=hours)

            PREDICTHQ_TOKEN = st.secrets["PREDICTHQ_TOKEN"]
            phq_url = "https://api.predicthq.com/v1/events/"
            phq_params = {
                #"location": f"{lat},{lon}",
                #"within": "10km",
                "within": f"10km@{lat},{lon}",
                "start.gte": now.isoformat() + "Z",
                "start.lte": end_time.isoformat() + "Z",
                "limit": 10,
                "sort": "start"
            }
            phq_headers = {
                "Authorization": f"Bearer {PREDICTHQ_TOKEN}",
                "Accept": "application/json"
            }

            # Optional debug
            # st.write("Request headers:", phq_headers)
            # st.write("Params:", phq_params)

            phq_resp = requests.get(phq_url, params=phq_params, headers=phq_headers)

            if phq_resp.status_code != 200:
                st.error("❌ PredictHQ API error.")
                st.code(phq_resp.text)
            else:
                events = phq_resp.json().get("results", [])
                if not events:
                    st.info("😕 No events found for this time window.")
                else:
                    for e in events:
                        title = e.get("title", "No Title")
                        start = e.get("start", "No Start Time")
                        category = e.get("category", "No Category")
                        entities = e.get("entities", [])
                        venue = "Unknown location"
                        for entity in entities:
                            if entity.get("type") == "venue":
                                venue = entity.get("name", "Unknown location")
                                break
                        st.markdown(f"### {title}")
                        st.write(f"📍 {venue}")
                        st.write(f"🗂️ Category: {category}")
                        st.write(f"🕒 Starts at: {start}")
                        st.markdown("---")