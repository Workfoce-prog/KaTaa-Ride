import json
import os
from datetime import datetime, date
from math import radians, sin, cos, asin, sqrt

# ---------------------------------
# BASIC LANGUAGE CONFIG
# ---------------------------------

LANG_OPTIONS = ["English", "French", "Bambara"]

labels = {
    "English": {
        "title_admin": "Mali Ride – Admin Dashboard",
        "subtitle": "Real-time view of drivers, trips, payments, promotions, and cancellations.",
        "admin_auth": "Admin access",
        "admin_code_label": "Admin code",
        "admin_code_hint": "Enter the admin code to unlock (not needed in demo mode).",
        "admin_code_wrong": "Incorrect admin code.",
        "admin_locked": "Admin area locked. Please provide a valid code.",
        "status_options": ["Available", "On trip", "Offline"],
        "metric_drivers": "Drivers",
        "metric_available": "Available",
        "metric_busy": "On trip",
        "metric_offline": "Offline",
        "metric_trips": "Trips",
        "metric_revenue": "Gross fares (XOF)",
        "metric_platform_revenue": "Platform revenue (XOF)",
        "metric_driver_earnings": "Driver earnings (XOF)",
        "drivers_table_header": "Drivers table",
        "trips_table_header": "Trips table",
        "no_drivers": "No drivers registered yet.",
    },
    "French": {
        "title_admin": "Mali Ride – Tableau de bord Admin",
        "subtitle": "Vue en temps réel des chauffeurs, trajets, paiements, promotions et annulations.",
        "admin_auth": "Accès administrateur",
        "admin_code_label": "Code admin",
        "admin_code_hint": "Entrez le code administrateur (pas nécessaire en mode démo).",
        "admin_code_wrong": "Code administrateur incorrect.",
        "admin_locked": "Zone admin verrouillée. Veuillez saisir un code valide.",
        "status_options": ["Disponible", "En course", "Hors ligne"],
        "metric_drivers": "Chauffeurs",
        "metric_available": "Disponibles",
        "metric_busy": "En course",
        "metric_offline": "Hors ligne",
        "metric_trips": "Courses",
        "metric_revenue": "Recettes brutes (XOF)",
        "metric_platform_revenue": "Revenus plateforme (XOF)",
        "metric_driver_earnings": "Gains chauffeurs (XOF)",
        "drivers_table_header": "Table des chauffeurs",
        "trips_table_header": "Table des courses",
        "no_drivers": "Aucun chauffeur enregistré pour le moment.",
    },
    "Bambara": {
        "title_admin": "Mali Ride – Kɔrɔba Kɛlasira",
        "subtitle": "Donni donni fɔlɔ kɔnɔ baro ye: sɔfɔw, sɔrɔ, ka bara, ni ka kɛlaɲɛw.",
        "admin_auth": "Kɛlasira nafalaw",
        "admin_code_label": "Kɛlasira kɔdɔ",
        "admin_code_hint": "I ka kɛlasira kɔdɔ na (demo mode la, tɛ se ka fɛ).",
        "admin_code_wrong": "Kɛlasira kɔdɔ ma fɔ ye.",
        "admin_locked": "Kɛlasira dugukolo da. Kɛ kɔdɔ bɛɛ fɛ ka fɛ.",
        "status_options": ["Sɔrɔbaga", "Ka sɔrɔ kɔrɔbɔ", "Tɛ sɔrɔ"],
        "metric_drivers": "Sɔfɔw",
        "metric_available": "Sɔrɔbaga",
        "metric_busy": "Ka sɔrɔ kɔrɔbɔ",
        "metric_offline": "Tɛ sɔrɔ",
        "metric_trips": "Sɔrɔw",
        "metric_revenue": "Ka baarakɛ min bɛ na (XOF)",
        "metric_platform_revenue": "Platform ka baarakɛ (XOF)",
        "metric_driver_earnings": "Sɔfɔ ka baarakɛ (XOF)",
        "drivers_table_header": "Sɔfɔw kan",
        "trips_table_header": "Sɔrɔw kan",
        "no_drivers": "Sɔfɔ si tɛ sɔrɔ yen.",
    },
}

# ---------------------------------
# FILE PATHS
# ---------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # this is the folder of shared.py
DATA_DIR = os.path.join(BASE_DIR, "data")

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)

DRIVERS_PATH = os.path.join(DATA_DIR, "drivers.json")
TRIPS_PATH = os.path.join(DATA_DIR, "trips.json")
ADMIN_LOGINS_PATH = os.path.join(DATA_DIR, "admin_logins.json")

# Some demo cities
MALI_CITIES = ["Bamako", "Kayes", "Koulikoro", "Sikasso", "Ségou", "Mopti", "Gao", "Tombouctou", "Kidal"]


# ---------------------------------
# JSON HELPERS
# ---------------------------------

def _read_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---------------------------------
# DRIVERS
# ---------------------------------

def load_drivers_from_db():
    """Return list of driver dicts."""
    return _read_json(DRIVERS_PATH, [])


def save_driver_to_db(driver_dict):
    """Append a driver to the local JSON store."""
    drivers = load_drivers_from_db()
    # simple overwrite by username if exists
    username = driver_dict.get("username")
    existing_idx = None
    for i, d in enumerate(drivers):
        if d.get("username") == username:
            existing_idx = i
            break
    if existing_idx is not None:
        drivers[existing_idx] = driver_dict
    else:
        drivers.append(driver_dict)
    _write_json(DRIVERS_PATH, drivers)


def update_driver_in_db(username, new_data):
    """Update a driver with username using new_data dict."""
    drivers = load_drivers_from_db()
    updated = False
    for i, d in enumerate(drivers):
        if d.get("username") == username:
            drivers[i] = new_data
            updated = True
            break
    if not updated:
        drivers.append(new_data)
    _write_json(DRIVERS_PATH, drivers)


# ---------------------------------
# TRIPS
# ---------------------------------

def load_trips_from_db():
    """Return list of trip dicts."""
    return _read_json(TRIPS_PATH, [])


def save_trip_to_db(trip_dict):
    trips = load_trips_from_db()
    trips.append(trip_dict)
    _write_json(TRIPS_PATH, trips)


# ---------------------------------
# ADMIN LOGIN LOGGING
# ---------------------------------

def save_admin_login_to_db(info):
    """Append an admin login event."""
    logs = _read_json(ADMIN_LOGINS_PATH, [])
    logs.append(info)
    _write_json(ADMIN_LOGINS_PATH, logs)


# ---------------------------------
# DISTANCE & PRICING
# ---------------------------------

def haversine_miles(lat1, lon1, lat2, lon2):
    """Compute distance in miles between two lat/lon pairs."""
    if None in (lat1, lon1, lat2, lon2):
        return 0.0
    R_km = 6371.0
    lat1_r, lon1_r, lat2_r, lon2_r = map(radians, [lat1, lon1, lat2, lon2])
    dlon = lon2_r - lon1_r
    dlat = lat2_r - lat1_r
    a = sin(dlat / 2) ** 2 + cos(lat1_r) * cos(lat2_r) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    km = R_km * c
    miles = km * 0.621371
    return miles


BASE_FARE_XOF = 700  # example base fare
PER_MILE_XOF = 300   # per mile


def compute_price_xof(distance_miles):
    """Simple distance-based pricing."""
    if distance_miles is None:
        distance_miles = 0.0
    fare = BASE_FARE_XOF + PER_MILE_XOF * distance_miles
    return max(int(round(fare)), BASE_FARE_XOF)


# ---------------------------------
# COMMISSION TIERS (Heetch-beating)
# ---------------------------------

def get_commission_pct(weekly_trips: int) -> int:
    """
    Heetch-beating tiers, lower commission for hard-working drivers.

    60+ trips / week  -> 8%
    40–59             -> 10%
    20–39             -> 12%
    0–19              -> 14%
    """
    if weekly_trips >= 60:
        return 8
    elif weekly_trips >= 40:
        return 10
    elif weekly_trips >= 20:
        return 12
    else:
        return 14


def split_fare(price_xof, commission_pct):
    """Return (platform_commission_xof, driver_earnings_xof)."""
    if price_xof is None:
        price_xof = 0
    commission = int(round(price_xof * commission_pct / 100.0))
    driver_amount = price_xof - commission
    if driver_amount < 0:
        driver_amount = 0
    return commission, driver_amount


# ---------------------------------
# CANCELLATION RULES
# ---------------------------------

PASSENGER_LATE_CANCEL_FEE_PCT = 75  # % of fare
DRIVER_CANCEL_PENALTY_PCT = 35      # % of fare
DRIVER_RATING_PENALTY_STEP = 0.2    # rating drop per cancellation
DRIVER_MIN_RATING = 1.0


def apply_passenger_cancellation(trip):
    """
    Apply passenger cancellation logic to a trip dict.

    Assumes `trip` has:
      - price_xof
      - scheduled_time_iso (optional for real scheduling)
    """
    price = trip.get("price_xof", 0)
    fee = int(round(price * PASSENGER_LATE_CANCEL_FEE_PCT / 100.0))
    trip["status"] = "cancelled_by_passenger"
    trip["cancellation_fee_xof"] = fee
    trip["platform_commission_xof"] = fee
    trip["driver_earnings_xof"] = 0
    return trip


def apply_driver_cancellation(trip):
    """
    Apply driver cancellation logic to a trip dict.
    35% penalty goes to platform, driver earns 0.
    """
    price = trip.get("price_xof", 0)
    fee = int(round(price * DRIVER_CANCEL_PENALTY_PCT / 100.0))
    trip["status"] = "cancelled_by_driver"
    trip["cancellation_fee_xof"] = fee
    trip["platform_commission_xof"] = fee
    trip["driver_earnings_xof"] = 0
    return trip


def penalize_driver_rating(driver_dict):
    """
    Reduce driver rating when they cancel a trip.
    """
    rating = float(driver_dict.get("rating", 5.0))
    cancel_count = int(driver_dict.get("cancel_count", 0))

    rating = max(DRIVER_MIN_RATING, rating - DRIVER_RATING_PENALTY_STEP)
    cancel_count += 1

    driver_dict["rating"] = rating
    driver_dict["cancel_count"] = cancel_count
    return driver_dict


