import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz

# Set up the app
st.set_page_config(page_title="I'm Bored", page_icon="🎯")
st.title("🎯 I'm Bored")
st.subheader("Find real events near you, right now.")

# User input
city = st.text_input("Enter your city", "New York")

# Validate the city with live geocoding
lat = lon = None
location_info = ""

if city:
    geo_url = "https://nominatim.openstreetmap.org/search"
    geo_params = {"q": city, "format": "json", "limit": 1}
    try:
        geo_resp = requests.get(geo_url, params=geo_params, timeout=5)

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
            
        if geo_data:
            lat = float(geo_data[0]["lat"])
            lon = float(geo_data[0]["lon"])
            location_info = geo_data[0]["display_name"]
            st.success(f"📍 Found: {location_info}")
        else:
            st.warning("❗ Could not find that city. Check the spelling or try a nearby town.")
    except Exception as e:
        st.error(f"🌐 Error connecting to location service: {e}")

# Proceed only if a valid location was found
if lat and lon:
    hours = st.selectbox("How much time do you have?", [2, 4, 6, 8])
    if st.button("Find Events"):
        with st.spinner("Searching for events..."):
            now = datetime.now(pytz.utc)
            end_time = now + timedelta(hours=hours)

            EVENTBRITE_TOKEN = st.secrets.get("EVENTBRITE_TOKEN", "YOUR_EVENTBRITE_TOKEN")
            eb_url = "https://www.eventbriteapi.com/v3/events/search/"
            eb_params = {
                "location.latitude": lat,
                "location.longitude": lon,
                "start_date.range_start": now.isoformat(),
                "start_date.range_end": end_time.isoformat(),
                "expand": "venue",
                "sort_by": "date"
            }
            eb_headers = {"Authorization": f"Bearer {EVENTBRITE_TOKEN}"}
            eb_resp = requests.get(eb_url, params=eb_params, headers=eb_headers)

            if eb_resp.status_code != 200:
                st.error("❌ Eventbrite API error.")
                st.code(eb_resp.text)
            else:
                events = eb_resp.json().get("events", [])
                if not events:
                    st.info("😕 No events found for this time window.")
                else:
                    for e in events:
                        title = e["name"]["text"]
                        start = e["start"]["local"]
                        venue = e.get("venue", {}).get("address", {}).get("localized_address_display", "Unknown location")
                        st.markdown(f"### {title}")
                        st.write(f"📍 {venue}")
                        st.write(f"🕒 Starts at: {start}")
                        st.markdown("---")
else:
    st.info("Enter a valid city to get started.")