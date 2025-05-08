import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz

# Title
st.set_page_config(page_title="I'm Bored", page_icon="🎯")
st.title("🎯 I'm Bored")
st.subheader("Find real events near you, right now.")

# Input fields
city = st.text_input("Enter your city", "New York")
hours = st.selectbox("How much time do you have?", [2, 4, 6, 8])

# API key (store safely in local testing or Streamlit Secrets)
EVENTBRITE_TOKEN = st.secrets.get("EVENTBRITE_TOKEN", "YOUR_EVENTBRITE_TOKEN")

if st.button("Find Events"):
    with st.spinner("Finding cool things nearby..."):
        # Geocode city to lat/lon
        geo_url = "https://nominatim.openstreetmap.org/search"
        geo_params = {"q": city, "format": "json", "limit": 1}
        geo_resp = requests.get(geo_url, params=geo_params)
        geo_data = geo_resp.json()

        if not geo_data:
            st.error("❌ Could not find that city. Try another.")
        else:
            lat = float(geo_data[0]["lat"])
            lon = float(geo_data[0]["lon"])

            now = datetime.now(pytz.utc)
            end_time = now + timedelta(hours=hours)

            # Eventbrite call
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
                    st.info("😕 No events found for that window.")
                else:
                    for e in events:
                        title = e["name"]["text"]
                        start = e["start"]["local"]
                        venue = e.get("venue", {}).get("address", {}).get("localized_address_display", "Unknown location")
                        st.markdown(f"### {title}")
                        st.write(f"📍 {venue}")
                        st.write(f"🕒 Starts at: {start}")
                        st.markdown("---")

