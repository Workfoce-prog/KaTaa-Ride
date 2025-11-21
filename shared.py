
import os
import json
from math import radians, sin, cos, asin, sqrt
from datetime import datetime

import pandas as pd
import requests
from google.cloud import firestore
from google.oauth2 import service_account
import streamlit as st

# ----------------------------
# GLOBAL CONFIG
# ----------------------------
ADMIN_CODE = "owner123"  # used in admin_app only (but imported from here)

USE_REAL_ROUTING = True  # set False to fall back to haversine
ROUTING_PROVIDER = "openrouteservice"  # or "google"

# API keys from environment
ORS_API_KEY = os.getenv("ORS_API_KEY")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# ----------------------------
# LANGUAGE LABELS
# ----------------------------
LANG_OPTIONS = ["English", "Français", "Bambara"]

labels = {
    "English": {
        "title_driver": "🚕 Mali Ride – Driver App",
        "title_passenger": "🚕 Mali Ride – Passenger App",
        "title_admin": "🚕 Mali Ride – Admin Dashboard",
        "title_mobile": "📱 Mali Ride – Mobile App (Driver & Passenger)",
        "subtitle": "Uber-style demo for Mali with distance-based pricing and nearest-driver matching.",
        "language_label": "Language / Langue / Kan",
        "driver_area": "Driver",
        "passenger_area": "Passenger",
        "admin_area": "Admin",
        "price_settings": "Price settings",
        "base_fare": "Base fare (XOF)",
        "per_mile": "Price per mile (XOF)",
        "commission_settings": "Commission settings",
        "platform_cut": "Platform commission (%)",
        "driver_share": "Driver share",
        "city_coords": "City coordinates (reference)",
        "driver_header": "👨‍✈️ Driver Area",
        "tab_register": "➕ Register new driver",
        "tab_login": "🔐 Login & update status/location",
        "register_header": "Register a new driver",
        "first_name": "First name",
        "last_name": "Last name",
        "age": "Age",
        "driver_id": "Driver ID (e.g., phone number)",
        "driver_id_help": "This is used to login later.",
        "transport_type": "Transportation type",
        "payment_methods": "Accepted payment methods",
        "pin": "Choose a 4-digit PIN",
        "pin_help": "Very simple demo security.",
        "location_header": "Driver location",
        "city": "Main city (approximate)",
        "lat": "Latitude",
        "lon": "Longitude",
        "register_btn": "Register driver",
        "missing_fields": "Please fill in first name, last name, Driver ID, and PIN.",
        "id_used": "This Driver ID is already used. Please choose another.",
        "reg_success": "Driver {name} registered successfully as ID {id}.",
        "login_header": "Login to update your status or location",
        "logged_as": "Currently logged in as Driver ID:",
        "login_id": "Driver ID",
        "login_pin": "PIN",
        "login_btn": "Login",
        "login_success": "Login successful. Welcome, {name}!",
        "login_error": "Invalid Driver ID or PIN.",
        "update_header": "Update info",
        "status": "Status",
        "status_options": ["Available", "Busy", "Offline"],
        "current_lat": "Current latitude",
        "current_lon": "Current longitude",
        "update_btn": "Save updates",
        "update_success": "Driver status/location updated.",
        "all_drivers": "All registered drivers",
        "no_drivers": "No drivers registered yet.",
        "drivers_map": "🗺️ Drivers map",
        "passenger_header": "🧍‍♂️ Passenger – Request a ride",
        "no_available": "No available drivers at the moment. Please check again later or ask drivers to set status to 'Available'.",
        "passenger_intro": "Choose a route mode: within one city, manual GPS, or city-to-city.",
        "route_mode": "Route mode",
        "within_city": "Within city (same city)",
        "within_city_city_label": "City for your ride",
        "use_neighborhoods": "Use Bamako neighborhoods (pickup & dropoff by area)",
        "pickup_neighborhood": "Pickup neighborhood (Bamako)",
        "dropoff_neighborhood": "Dropoff neighborhood (Bamako)",
        "manual_coords": "Manual coordinates (GPS)",
        "preset_route": "City-to-city preset",
        "from_city": "From city",
        "to_city": "To city",
        "pickup_header": "Pickup location",
        "dropoff_header": "Dropoff location",
        "pickup_lat": "Pickup latitude",
        "pickup_lon": "Pickup longitude",
        "drop_lat": "Dropoff latitude",
        "drop_lon": "Dropoff longitude",
        "trip_btn": "Find nearest drivers & estimate price",
        "price_header": "💰 Estimated ride price",
        "trip_distance": "Trip distance",
        "price_estimated": "Estimated price",
        "drivers_by_prox": "🚕 Available drivers ordered by proximity",
        "map_pickup": "🗺️ Map – Pickup & available drivers",
        "choose_driver": "✅ Choose a driver to book",
        "select_driver": "Select a driver:",
        "confirm_booking": "Confirm booking with selected driver",
        "booking_success": "Booking confirmed with driver {name} (ID: {id}).",
        "booking_warn": "Driver was not found in the main list (unexpected).",
        "current_trip_header": "📦 Current trip summary",
        "driver_id_label": "Driver ID",
        "distance_label": "Distance",
        "price_label": "Price",
        "pickup_label": "Pickup",
        "dropoff_label": "Dropoff",
        "admin_header": "📊 Admin dashboard",
        "admin_desc": "Simple overview of drivers and trips (demo only – in-memory or Firestore, not a full production system).",
        "metric_drivers": "Total drivers",
        "metric_available": "Available",
        "metric_busy": "Busy",
        "metric_offline": "Offline",
        "metric_trips": "Total trips",
        "metric_revenue": "Total trip value (XOF)",
        "metric_platform_revenue": "Platform commission (XOF)",
        "metric_driver_earnings": "Driver earnings (XOF)",
        "drivers_table_header": "Drivers table",
        "trips_table_header": "Trips table",
        "download_drivers": "Download drivers as CSV",
        "download_trips": "Download trips as CSV",
        "admin_auth": "Admin access",
        "admin_code_label": "Enter admin code",
        "admin_code_hint": "Owner / platform code to unlock dashboard.",
        "admin_locked": "Admin dashboard is locked. Enter the correct admin code.",
        "admin_code_wrong": "Incorrect admin code.",
        "no_drivers_in_city": "No available drivers in this city for now.",
        "mobile_mode_label": "Mode",
        "mobile_driver_tab": "Driver",
        "mobile_passenger_tab": "Passenger",
    },
    # (Français and Bambara omitted here for brevity in shared module – we keep them in the main app if needed)
}

# ----------------------------
# FIRESTORE HELPERS
# ----------------------------
def get_firestore_client():
    try:
        gcp_section = st.secrets["gcp"]
        project_id = gcp_section["firestore_project"]
        cred_info = json.loads(gcp_section["credentials_json"])
        credentials = service_account.Credentials.from_service_account_info(cred_info)
        client = firestore.Client(project=project_id, credentials=credentials)
        return client
    except Exception:
        st.warning("Firestore not configured correctly. Using in-memory session only.")
        return None


def load_drivers_from_db():
    client = get_firestore_client()
    if client is None:
        return st.session_state.get("drivers", [])

    docs = client.collection("drivers").stream()
    drivers = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        drivers.append(data)
    return drivers


def save_driver_to_db(driver):
    client = get_firestore_client()
    if client is None:
        st.session_state["drivers"].append(driver)
        return

    doc_ref = client.collection("drivers").document(driver["username"])
    doc_ref.set(driver)


def update_driver_in_db(username, updates):
    client = get_firestore_client()
    if client is None:
        for d in st.session_state["drivers"]:
            if d["username"] == username:
                d.update(updates)
        return

    doc_ref = client.collection("drivers").document(username)
    doc_ref.set(updates, merge=True)


def load_trips_from_db():
    client = get_firestore_client()
    if client is None:
        return st.session_state.get("trips", [])

    docs = client.collection("trips").order_by("created_at", direction=firestore.Query.DESCENDING).stream()
    trips = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        trips.append(data)
    return trips


def save_trip_to_db(trip):
    client = get_firestore_client()
    if client is None:
        st.session_state["trips"].append(trip)
        return

    client.collection("trips").add(trip)

# ----------------------------
# ROUTING HELPERS
# ----------------------------
def haversine_miles(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    km = 6371 * c
    miles = km * 0.621371
    return miles


def get_distance_miles_openrouteservice(lat1, lon1, lat2, lon2):
    if not ORS_API_KEY:
        return haversine_miles(lat1, lon1, lat2, lon2)

    url = "https://api.openrouteservice.org/v2/directions/driving-car"
    headers = {"Authorization": ORS_API_KEY, "Content-Type": "application/json"}
    payload = {"coordinates": [[lon1, lat1], [lon2, lat2]]}

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        meters = data["features"][0]["properties"]["segments"][0]["distance"]
        miles = meters * 0.000621371
        return miles
    except Exception:
        return haversine_miles(lat1, lon1, lat2, lon2)


def get_distance_miles_google(lat1, lon1, lat2, lon2):
    if not GOOGLE_MAPS_API_KEY:
        return haversine_miles(lat1, lon1, lat2, lon2)

    base_url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "origins": f"{lat1},{lon1}",
        "destinations": f"{lat2},{lon2}",
        "mode": "driving",
        "units": "imperial",
        "key": GOOGLE_MAPS_API_KEY,
    }

    try:
        resp = requests.get(base_url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        element = data["rows"][0]["elements"][0]
        if element.get("status") != "OK":
            return haversine_miles(lat1, lon1, lat2, lon2)
        meters = element["distance"]["value"]
        miles = meters * 0.000621371
        return miles
    except Exception:
        return haversine_miles(lat1, lon1, lat2, lon2)


def get_trip_distance_miles(lat1, lon1, lat2, lon2):
    if not USE_REAL_ROUTING:
        return haversine_miles(lat1, lon1, lat2, lon2)

    if ROUTING_PROVIDER == "openrouteservice":
        return get_distance_miles_openrouteservice(lat1, lon1, lat2, lon2)
    elif ROUTING_PROVIDER == "google":
        return get_distance_miles_google(lat1, lon1, lat2, lon2)
    else:
        return haversine_miles(lat1, lon1, lat2, lon2)


def compute_fare(distance_miles, base_fare=1000, per_mile=300):
    return round(base_fare + per_mile * distance_miles, 0)


# Approximate city centers in Mali
MALI_CITIES = {
    "Bamako": (12.6392, -8.0029),
    "Kayes": (14.4469, -11.4445),
    "Ségou": (13.4317, -6.2157),
    "Mopti": (14.4843, -4.1828),
    "Sikasso": (11.3170, -5.6665),
    "Gao": (16.2667, -0.0500),
    "Tombouctou": (16.7666, -3.0026),
}

# Approximate Bamako neighborhoods (center points)
BKO_NEIGHBORHOODS = {
    "ACI 2000": (12.6475, -7.9835),
    "Kalaban-Coura": (12.6100, -7.9660),
    "Badalabougou": (12.6290, -7.9900),
    "Hamdallaye": (12.6540, -7.9810),
    "Lafiabougou": (12.6520, -8.0100),
    "Magnambougou": (12.6250, -7.9500),
    "Sogoniko": (12.6100, -7.9500),
    "Baco-Djicoroni": (12.6040, -8.0400),
    "Djélibougou": (12.6400, -7.9400),
}


# ----------------------------
# COMMISSION TIERS - BAMAKO LAUNCH PROMO (3–6 months)
# ----------------------------
def get_commission_pct(weekly_trips):
    # Launch promo: extremely competitive vs. Heetch
    if weekly_trips >= 60:
        return 8
    elif weekly_trips >= 40:
        return 10
    elif weekly_trips >= 20:
        return 12
    else:
        return 14

