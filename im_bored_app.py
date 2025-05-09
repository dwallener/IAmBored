import streamlit as st
import streamlit.components.v1 as components
import requests
from datetime import datetime, timedelta
from math import radians, cos, sin, asin, sqrt

# App setup
st.set_page_config(page_title="I'm Bored", page_icon="🎯")
st.title("🎯 I'm Bored")
st.subheader("Find real events near you, right now.")

# Debug: Confirm PredictHQ token loaded
st.write("Token preview:", st.secrets.get("PREDICTHQ_TOKEN", "Not found")[:10] + "...")

# --- Geolocation Support ---
def get_geolocation():
    geolocation_js = """
    <script>
    function sendLocation() {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const coords = position.coords.latitude + "," + position.coords.longitude;
                const streamlitEvent = new CustomEvent("streamlit:location", { detail: coords });
                window.dispatchEvent(streamlitEvent);
            },
            (error) => {
                const streamlitEvent = new CustomEvent("streamlit:location", { detail: "denied" });
                window.dispatchEvent(streamlitEvent);
            }
        );
    }
    sendLocation();
    </script>
    """
    components.html(geolocation_js, height=0)
    location_data = st.query_params.get("geolocation", [""])[0]
    return location_data

user_location = get_geolocation()

# Try to get lat/lon from browser first
lat = lon = None
location_info = ""

if user_location and user_location != "denied":
    try:
        lat, lon = map(float, user_location.split(","))
        st.success(f"📍 Using your current location: {lat}, {lon}")
    except:
        st.warning("📍 Unable to parse detected location. Please enter your city manually.")
else:
    city = st.text_input("📍 Enter your city manually", "New York")
    if city:
        geo_url = "https://nominatim.openstreetmap.org/search"
        geo_params = {"q": city, "format": "json", "limit": 1}
        headers = {"User-Agent": "I'm Bored MVP/1.0 (contact@yourdomain.com)"}
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
        st.info("Enter a city or enable location sharing to get started.")

# --- Travel Time Estimation ---
def estimate_travel_time(user_lat, user_lon, event_lat, event_lon):
    if None in (user_lat, user_lon, event_lat, event_lon):
        return "Unknown travel time"

    R = 6371  # Earth radius in km
    dlat = radians(event_lat - user_lat)
    dlon = radians(event_lon - user_lon)
    a = sin(dlat / 2) ** 2 + cos(radians(user_lat)) * cos(radians(event_lat)) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    distance_km = R * c

    if distance_km <= 2:
        time_minutes = int((distance_km / 5) * 60)  # Walking speed: 5 km/h
        return f"~{time_minutes} min walk" if time_minutes > 0 else "<1 min walk"
    else:
        driving_distance = distance_km * 0.9
        walking_distance = distance_km * 0.1
        driving_time = (driving_distance / 40) * 60  # 40 km/h driving speed
        walking_time = (walking_distance / 5) * 60   # 5 km/h walking speed
        total_time = int(driving_time + walking_time)
        return f"~{total_time} min (mostly driving)"

# --- Time Selection and Event Search ---
if lat and lon:
    now_local = datetime.now()
    leave_time = st.time_input("🕑 When will you leave?", value=now_local.time())
    return_time = st.time_input("⏰ When do you need to be back?", value=(now_local + timedelta(hours=4)).time())

    if leave_time and return_time:
        leave_dt = datetime.combine(now_local.date(), leave_time)
        return_dt = datetime.combine(now_local.date(), return_time)

        # Handle overnight return time
        if return_time <= leave_time:
            return_dt += timedelta(days=1)

        st.info(f"🗓️ Looking for events between **{leave_dt.strftime('%H:%M')}** and **{return_dt.strftime('%H:%M')}**.")

        if st.button("🎯 Find Events"):
            with st.spinner("Searching for events..."):
                PREDICTHQ_TOKEN = st.secrets["PREDICTHQ_TOKEN"]
                phq_url = "https://api.predicthq.com/v1/events/"
                phq_params = {
                    "within": f"10km@{lat},{lon}",
                    "start.gte": leave_dt.isoformat() + "Z",
                    "start.lte": return_dt.isoformat() + "Z",
                    "limit": 10,
                    "sort": "start"
                }
                phq_headers = {
                    "Authorization": f"Bearer {PREDICTHQ_TOKEN}",
                    "Accept": "application/json"
                }

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
                            venue_lat = venue_lon = None

                            for entity in entities:
                                if entity.get("type") == "venue":
                                    venue = entity.get("name", "Unknown location")
                                    geo = entity.get("geo")
                                    if geo and "lat" in geo and "lon" in geo:
                                        venue_lat = geo.get("lat")
                                        venue_lon = geo.get("lon")
                                    break  # Stop after the first venue found

                            if venue_lat is not None and venue_lon is not None:
                                travel_time_estimate = estimate_travel_time(lat, lon, venue_lat, venue_lon)
                            else:
                                travel_time_estimate = "Unknown travel time"

                            st.markdown(f"### 🎉 {title}")
                            st.write(f"📍 {venue}")
                            st.write(f"🗂️ Category: {category}")
                            st.write(f"🕒 Starts at: {start}")
                            st.write(f"🚗 Estimated Travel Time: {travel_time_estimate}")
                            st.markdown("---")
    else:
        st.warning("⚠️ Please set both 'Leave at' and 'Be back by' times.")