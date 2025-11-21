
import streamlit as st
import pandas as pd
from math import radians, sin, cos, asin, sqrt
import os
import requests
import json
from datetime import datetime
from google.cloud import firestore
from google.oauth2 import service_account

# -------------------------------------------------
# CONFIG
# -------------------------------------------------
st.set_page_config(page_title="Mali Ride App (Uber-style demo)", layout="wide")

# Simple admin code (change this for your deployment)
ADMIN_CODE = "owner123"

# Routing provider configs
USE_REAL_ROUTING = True  # set False to fall back to haversine
ROUTING_PROVIDER = "openrouteservice"  # or "google"

# API keys (set them as environment variables in Streamlit Cloud)
ORS_API_KEY = os.getenv("ORS_API_KEY")        # OpenRouteService
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")  # Google Maps

# -------------------------------------------------
# FIRESTORE HELPERS
# -------------------------------------------------
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

# -------------------------------------------------
# LANGUAGE SUPPORT
# -------------------------------------------------
LANG_OPTIONS = ["English", "Français", "Bambara"]

labels = {
    "English": {
        "title": "🚕 Mali Ride App – Uber-style Demo",
        "subtitle": "Drivers register, passengers request rides, nearest driver is matched, price by distance in miles.",
        "mode_label": "Select area:",
        "driver_area": "Driver area",
        "passenger_area": "Passenger area",
        "admin_area": "Admin dashboard",
        "price_settings": "Price settings",
        "base_fare": "Base fare (XOF)",
        "per_mile": "Price per mile (XOF)",
        "commission_settings": "Commission settings",
        "platform_cut": "Platform commission (%)",
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
        "admin_locked": "Admin dashboard is locked. Enter the correct admin code in the sidebar.",
        "admin_code_wrong": "Incorrect admin code.",
        "no_drivers_in_city": "No available drivers in this city for now."
    },
    "Français": {
        "title": "🚕 Mali Ride App – Démo type Uber",
        "subtitle": "Les chauffeurs s'enregistrent, les passagers demandent une course, le chauffeur le plus proche est sélectionné, prix basé sur la distance en miles.",
        "mode_label": "Choisir la zone :",
        "driver_area": "Espace chauffeur",
        "passenger_area": "Espace passager",
        "admin_area": "Tableau de bord admin",
        "price_settings": "Paramètres de prix",
        "base_fare": "Prix de base (XOF)",
        "per_mile": "Prix par mile (XOF)",
        "commission_settings": "Paramètres de commission",
        "platform_cut": "Commission plateforme (%)",
        "city_coords": "Coordonnées des villes (référence)",
        "driver_header": "👨‍✈️ Espace chauffeur",
        "tab_register": "➕ Enregistrer un nouveau chauffeur",
        "tab_login": "🔐 Connexion & mise à jour statut/localisation",
        "register_header": "Enregistrer un nouveau chauffeur",
        "first_name": "Prénom",
        "last_name": "Nom",
        "age": "Âge",
        "driver_id": "ID chauffeur (ex : numéro de téléphone)",
        "driver_id_help": "Utilisé pour se connecter.",
        "transport_type": "Type de transport",
        "payment_methods": "Méthodes de paiement acceptées",
        "pin": "Choisir un code PIN à 4 chiffres",
        "pin_help": "Sécurité très simple pour la démo.",
        "location_header": "Localisation du chauffeur",
        "city": "Ville principale (approx.)",
        "lat": "Latitude",
        "lon": "Longitude",
        "register_btn": "Enregistrer le chauffeur",
        "missing_fields": "Veuillez remplir prénom, nom, ID chauffeur et PIN.",
        "id_used": "Cet ID chauffeur est déjà utilisé. Choisissez un autre.",
        "reg_success": "Chauffeur {name} enregistré avec succès avec l'ID {id}.",
        "login_header": "Connexion pour mettre à jour le statut ou la localisation",
        "logged_as": "Connecté comme ID chauffeur :",
        "login_id": "ID chauffeur",
        "login_pin": "PIN",
        "login_btn": "Connexion",
        "login_success": "Connexion réussie. Bienvenue, {name} !",
        "login_error": "ID ou PIN invalide.",
        "update_header": "Mettre à jour les informations",
        "status": "Statut",
        "status_options": ["Disponible", "Occupé", "Hors ligne"],
        "current_lat": "Latitude actuelle",
        "current_lon": "Longitude actuelle",
        "update_btn": "Enregistrer les mises à jour",
        "update_success": "Statut/localisation du chauffeur mis à jour.",
        "all_drivers": "Tous les chauffeurs enregistrés",
        "no_drivers": "Aucun chauffeur enregistré pour le moment.",
        "drivers_map": "🗺️ Carte des chauffeurs",
        "passenger_header": "🧍‍♂️ Passager – Demander une course",
        "no_available": "Aucun chauffeur disponible pour le moment. Réessayez plus tard ou demandez aux chauffeurs de passer en 'Disponible'.",
        "passenger_intro": "Choisissez un mode : trajet dans la même ville, coordonnées GPS manuelles, ou trajet ville-à-ville.",
        "route_mode": "Mode de trajet",
        "within_city": "Trajet dans la même ville",
        "within_city_city_label": "Ville du trajet",
        "use_neighborhoods": "Utiliser les quartiers de Bamako (départ & arrivée par quartier)",
        "pickup_neighborhood": "Quartier de départ (Bamako)",
        "dropoff_neighborhood": "Quartier d’arrivée (Bamako)",
        "manual_coords": "Coordonnées manuelles (GPS)",
        "preset_route": "Trajet ville-à-ville",
        "from_city": "Ville de départ",
        "to_city": "Ville d’arrivée",
        "pickup_header": "Lieu de prise en charge",
        "dropoff_header": "Lieu de dépose",
        "pickup_lat": "Latitude de départ",
        "pickup_lon": "Longitude de départ",
        "drop_lat": "Latitude d’arrivée",
        "drop_lon": "Longitude d’arrivée",
        "trip_btn": "Trouver les chauffeurs les plus proches & estimer le prix",
        "price_header": "💰 Prix estimé",
        "trip_distance": "Distance du trajet",
        "price_estimated": "Prix estimé",
        "drivers_by_prox": "🚕 Chauffeurs disponibles classés par proximité",
        "map_pickup": "🗺️ Carte – Départ & chauffeurs disponibles",
        "choose_driver": "✅ Choisir un chauffeur",
        "select_driver": "Sélectionner un chauffeur :",
        "confirm_booking": "Confirmer la réservation avec ce chauffeur",
        "booking_success": "Réservation confirmée avec le chauffeur {name} (ID : {id}).",
        "booking_warn": "Chauffeur introuvable dans la liste principale (imprévu).",
        "current_trip_header": "📦 Résumé de la course en cours",
        "driver_id_label": "ID chauffeur",
        "distance_label": "Distance",
        "price_label": "Prix",
        "pickup_label": "Départ",
        "dropoff_label": "Arrivée",
        "admin_header": "📊 Tableau de bord admin",
        "admin_desc": "Vue simple sur les chauffeurs et courses (démo seulement – mémoire locale ou Firestore).",
        "metric_drivers": "Nombre de chauffeurs",
        "metric_available": "Disponibles",
        "metric_busy": "Occupés",
        "metric_offline": "Hors ligne",
        "metric_trips": "Nombre de courses",
        "metric_revenue": "Valeur totale des courses (XOF)",
        "metric_platform_revenue": "Commission plateforme (XOF)",
        "metric_driver_earnings": "Revenus chauffeurs (XOF)",
        "drivers_table_header": "Table des chauffeurs",
        "trips_table_header": "Table des courses",
        "download_drivers": "Télécharger les chauffeurs en CSV",
        "download_trips": "Télécharger les courses en CSV",
        "admin_auth": "Accès admin",
        "admin_code_label": "Code admin",
        "admin_code_hint": "Code du propriétaire / plateforme pour déverrouiller le tableau.",
        "admin_locked": "Le tableau de bord admin est verrouillé. Entrez le code admin dans la barre latérale.",
        "admin_code_wrong": "Code admin incorrect.",
        "no_drivers_in_city": "Aucun chauffeur disponible dans cette ville pour le moment."
    },
    "Bambara": {
        "title": "🚕 Mali Ride App – Uber demo Bambara kɔnɔ",
        "subtitle": "Sofɛra bɛ se ka sɔrɔ, pasaje bɛ kan ka ɲɛgɛ fɔ, sofɛra min bɛ segin ye bɛ nana fɔrɔ, jɛgɛya bɛ kɛ mili distance la.",
        "mode_label": "Dɔw ka fili:",
        "driver_area": "Sofɛra bolɔ",
        "passenger_area": "Pasaje bolɔ",
        "admin_area": "Admin tablo",
        "price_settings": "Jɛgɛya sigida",
        "base_fare": "Jɛgɛya fara (XOF)",
        "per_mile": "Jɛgɛya kelen mile kɔfɛ (XOF)",
        "commission_settings": "Komisi sigida",
        "platform_cut": "Platforma komisi (%)",
        "city_coords": "Duguw koodoni (reference)",
        "driver_header": "👨‍✈️ Sofɛra bolɔ",
        "tab_register": "➕ Sofɛra kura sɔrɔ",
        "tab_login": "🔐 Se ka don & statu / ladilan bɛ yen",
        "register_header": "Sofɛra kura sɔrɔ",
        "first_name": "Tɔgɔ fɔlɔ",
        "last_name": "Tɔgɔ kɔrɔ",
        "age": "Dɔgɔkun (age)",
        "driver_id": "Sofɛra ID (ex: sélɛfɔni numɛro)",
        "driver_id_help": "I bɛ a la se ka don kɔfɛ.",
        "transport_type": "Transport kala",
        "payment_methods": "Jɛgɛya hakɛ dɔw minnu bɛ se ka da",
        "pin": "PIN kelen kelen naani hakɛ dɔ tɔ",
        "pin_help": "Demo la hakɛ dɔ kɛrɛnkɛn.",
        "location_header": "Sofɛra ladilan",
        "city": "Dugu bɛɛ (approx.)",
        "lat": "Latitu",
        "lon": "Longitu",
        "register_btn": "Sofɛra sɔrɔ",
        "missing_fields": "I ka taa tɔgɔ fɔlɔ, tɔgɔ kɔrɔ, Sofɛra ID ani PIN na.",
        "id_used": "Sofɛra ID nin bɛ bɛ se fila. ID kɛlen wɛrɛ baara.",
        "reg_success": "Sofɛra {name} sɔrɔ don ID {id} la.",
        "login_header": "Se ka don ka statu walima ladilan bɛ yen",
        "logged_as": "Se don kɛra Sofɛra ID:",
        "login_id": "Sofɛra ID",
        "login_pin": "PIN",
        "login_btn": "Se ka don",
        "login_success": "Se don kɛra kelen kelen. I ni ce, {name}!",
        "login_error": "Sofɛra ID walima PIN tɛ kɛ se.",
        "update_header": "Mise à jour (lakana)",
        "status": "Statu",
        "status_options": ["Dɔnin", "Bara", "Offline"],
        "current_lat": "Latitu sisan",
        "current_lon": "Longitu sisan",
        "update_btn": "Mise à jour kɛ",
        "update_success": "Sofɛra statu / ladilan mise à jour kɛra.",
        "all_drivers": "Sofɛra bɛɛ minnu sɔrɔ",
        "no_drivers": "Sofɛra tɛna sɔrɔ ka taa sisan.",
        "drivers_map": "🗺️ Sofɛra kɔkɛ kan",
        "passenger_header": "🧍‍♂️ Pasaje – ɲɛgɛ dɔ kɛ",
        "no_available": "Sofɛra dɔnin tɛ yen sisan. K'an bɔ a la kɔfɛ oswa ka fɔ sofɛra ma ka statu 'Dɔnin' ye.",
        "passenger_intro": "I bɛ se ka mode filen: dugu kɔnɔ jɛgɛya, GPS manuwali, walima dugu-ka-dugu jɛgɛya.",
        "route_mode": "Jɛgɛya mode",
        "within_city": "Dugu kɔnɔ jɛgɛya",
        "within_city_city_label": "Dugu min na jɛgɛya kɛ",
        "use_neighborhoods": "Bamako quartierw bɛ kɛ (daminikan & benkan quartier la)",
        "pickup_neighborhood": "Daminikan quartier (Bamako)",
        "dropoff_neighborhood": "Benkan quartier (Bamako)",
        "manual_coords": "GPS koodoni manuwali",
        "preset_route": "Dugu ka dugu jɛgɛya",
        "from_city": "Dugu daminikan",
        "to_city": "Dugu benkan",
        "pickup_header": "Jɛgɛ daminikan fɛ",
        "dropoff_header": "Jɛgɛ benkan fɛ",
        "pickup_lat": "Daminikan latitu",
        "pickup_lon": "Daminikan longitu",
        "drop_lat": "Benkan latitu",
        "drop_lon": "Benkan longitu",
        "trip_btn": "Sofɛra minnu bɛ segin ye ka ɲini & jɛgɛya ɲini",
        "price_header": "💰 Jɛgɛya ɲini",
        "trip_distance": "Jɛgɛya distance",
        "price_estimated": "Jɛgɛya ɲini",
        "drivers_by_prox": "🚕 Sofɛra dɔnin minnu segin na, fila fila la",
        "map_pickup": "🗺️ Kɔkɛ – daminikan & sofɛra dɔnin",
        "choose_driver": "✅ Sofɛra kɛlen filen",
        "select_driver": "Sofɛra filen:",
        "confirm_booking": "Konfirme jɛgɛya ni sofɛra nin ye",
        "booking_success": "Jɛgɛya konfirme ka kɛ sofɛra {name} la (ID: {id}).",
        "booking_warn": "Sofɛra tɛ na lisitinin kɔnɔ (a tɛ na ɲininka la).",
        "current_trip_header": "📦 Jɛgɛya kɔnɔ fɔlɔ ɲɛfuru",
        "driver_id_label": "Sofɛra ID",
        "distance_label": "Distance",
        "price_label": "Jɛgɛya",
        "pickup_label": "Daminikan",
        "dropoff_label": "Benkan",
        "admin_header": "📊 Admin tablo",
        "admin_desc": "Sofɛra ani jɛgɛya ɲɛfuru (demo – data bɛ se ka taa memory kɔnɔ walima Firestore kɔnɔ).",
        "metric_drivers": "Sofɛra bɛɛ",
        "metric_available": "Dɔnin",
        "metric_busy": "Bara",
        "metric_offline": "Offline",
        "metric_trips": "Jɛgɛya bɛɛ",
        "metric_revenue": "Jɛgɛya wɛrɛw kɔrɔ (XOF)",
        "metric_platform_revenue": "Platforma komisi (XOF)",
        "metric_driver_earnings": "Sofɛra baro (XOF)",
        "drivers_table_header": "Sofɛra tablo",
        "trips_table_header": "Jɛgɛya tablo",
        "download_drivers": "Sofɛra CSV la don",
        "download_trips": "Jɛgɛya CSV la don",
        "admin_auth": "Admin don",
        "admin_code_label": "Admin kɔdi",
        "admin_code_hint": "Owner / platforma kɔdi ka tablo bɛ se ka bɔ.",
        "admin_locked": "Admin tablo bɛ sɔrɔ. Ka admin kɔdi jɔ si sidebar kɔnɔ.",
        "admin_code_wrong": "Admin kɔdi tɛ kɛ se.",
        "no_drivers_in_city": "Sofɛra dɔnin tɛ dugunin kɔnɔ sisan."
    }
}

st.sidebar.markdown("### 🌍 Language / Langue / Kan")
lang = st.sidebar.selectbox("", LANG_OPTIONS, index=0)

def L(key):
    return labels[lang].get(key, key)

st.title(L("title"))
st.caption(L("subtitle"))

# -------------------------------------------------
# ROUTING HELPERS
# -------------------------------------------------
def haversine_miles(lat1, lon1, lat2, lon2):
    """Great-circle distance between two points (in miles)."""
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    km = 6371 * c
    miles = km * 0.621371
    return miles


def get_distance_miles_openrouteservice(lat1, lon1, lat2, lon2):
    """Use OpenRouteService (OSM-based) to get driving distance in miles."""
    if not ORS_API_KEY:
        return haversine_miles(lat1, lon1, lat2, lon2)

    url = "https://api.openrouteservice.org/v2/directions/driving-car"
    headers = {"Authorization": ORS_API_KEY, "Content-Type": "application/json"}
    payload = {
        "coordinates": [
            [lon1, lat1],
            [lon2, lat2]
        ]
    }

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
    """Use Google Distance Matrix API to get driving distance in miles."""
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
    """Unified routing function."""
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


MALI_CITIES = {
    "Bamako": (12.6392, -8.0029),
    "Kayes": (14.4469, -11.4445),
    "Ségou": (13.4317, -6.2157),
    "Mopti": (14.4843, -4.1828),
    "Sikasso": (11.3170, -5.6665),
    "Gao": (16.2667, -0.0500),
    "Tombouctou": (16.7666, -3.0026),
}

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

# -------------------------------------------------
# SESSION STATE
# -------------------------------------------------
if "drivers" not in st.session_state:
    st.session_state["drivers"] = load_drivers_from_db()
if "logged_driver" not in st.session_state:
    st.session_state["logged_driver"] = None
if "current_trip" not in st.session_state:
    st.session_state["current_trip"] = None
if "trips" not in st.session_state:
    st.session_state["trips"] = load_trips_from_db()
if "admin_ok" not in st.session_state:
    st.session_state["admin_ok"] = False

# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------
st.sidebar.header(L("mode_label"))
mode = st.sidebar.radio(
    "",
    [L("driver_area"), L("passenger_area"), L("admin_area")]
)

st.sidebar.markdown("### ⚙️ " + L("price_settings"))
base_fare = st.sidebar.number_input(L("base_fare"), value=1000, min_value=0)
per_mile = st.sidebar.number_input(L("per_mile"), value=300, min_value=0)

st.sidebar.markdown("### 💸 " + L("commission_settings"))
platform_pct = st.sidebar.number_input(L("platform_cut"), value=20, min_value=0, max_value=100)
driver_pct = 100 - platform_pct
st.sidebar.write(f"Driver share: **{driver_pct}%**")

if mode == L("admin_area"):
    st.sidebar.markdown("### 🔑 " + L("admin_auth"))
    code_input = st.sidebar.text_input(L("admin_code_label"), type="password", help=L("admin_code_hint"))
    if st.sidebar.button("OK"):
        if code_input == ADMIN_CODE:
            st.session_state["admin_ok"] = True
        else:
            st.session_state["admin_ok"] = False
            st.sidebar.error(L("admin_code_wrong"))

st.sidebar.markdown("---")
st.sidebar.markdown("### ℹ️ " + L("city_coords"))
for city, (clat, clon) in MALI_CITIES.items():
    st.sidebar.write(f"- **{city}** ≈ {clat:.4f}, {clon:.4f}")

# -------------------------------------------------
# DRIVER AREA
# -------------------------------------------------
if mode == L("driver_area"):
    st.header(L("driver_header"))

    tab_reg, tab_login = st.tabs([L("tab_register"), L("tab_login")])

    with tab_reg:
        st.subheader(L("register_header"))
        with st.form("driver_register_form"):
            col1, col2 = st.columns(2)
            with col1:
                first_name = st.text_input(L("first_name"))
                last_name = st.text_input(L("last_name"))
                age = st.number_input(L("age"), min_value=18, max_value=90, value=30)
                username = st.text_input(L("driver_id"), help=L("driver_id_help"))
            with col2:
                transport_type = st.selectbox(
                    L("transport_type"),
                    ["Car", "Moto", "Taxi", "Minibus", "Other"]
                )
                payment_method = st.multiselect(
                    L("payment_methods"),
                    ["Cash", "Orange Money", "Wave", "Moov Money", "Card"],
                    default=["Cash", "Orange Money", "Wave"]
                )
                pin = st.text_input(L("pin"), type="password", max_chars=4, help=L("pin_help"))

            st.markdown("#### 📍 " + L("location_header"))
            city = st.selectbox(L("city"), list(MALI_CITIES.keys()) + ["Other"])
            default_lat, default_lon = MALI_CITIES.get(city, (12.6392, -8.0029))

            col3, col4 = st.columns(2)
            with col3:
                lat = st.number_input(L("lat"), value=float(default_lat))
            with col4:
                lon = st.number_input(L("lon"), value=float(default_lon))

            submit_reg = st.form_submit_button(L("register_btn"))

        if submit_reg:
            if not first_name or not last_name or not username or not pin:
                st.error(L("missing_fields"))
            else:
                existing = [d for d in st.session_state["drivers"] if d["username"] == username]
                if existing:
                    st.error(L("id_used"))
                else:
                    driver = {
                        "username": username,
                        "pin": pin,
                        "first_name": first_name,
                        "last_name": last_name,
                        "age": age,
                        "transport_type": transport_type,
                        "payment_method": ", ".join(payment_method),
                        "lat": lat,
                        "lon": lon,
                        "city": city,
                        "status": L("status_options")[0],
                    }
                    save_driver_to_db(driver)
                    st.session_state["drivers"].append(driver)
                    st.success(
                        L("reg_success").format(
                            name=f"{first_name} {last_name}",
                            id=username
                        )
                    )

    with tab_login:
        st.subheader(L("login_header"))

        if st.session_state["logged_driver"]:
            st.info(f"{L('logged_as')} {st.session_state['logged_driver']}")

        with st.form("driver_login_form"):
            login_user = st.text_input(L("login_id"))
            login_pin = st.text_input(L("login_pin"), type="password")
            submit_login = st.form_submit_button(L("login_btn"))

        driver_obj = None
        if submit_login:
            for d in st.session_state["drivers"]:
                if d["username"] == login_user and d["pin"] == login_pin:
                    driver_obj = d
                    st.session_state["logged_driver"] = login_user
                    break
            if driver_obj:
                st.success(L("login_success").format(name=driver_obj["first_name"]))
            else:
                st.error(L("login_error"))

        if st.session_state["logged_driver"]:
            username_logged = st.session_state["logged_driver"]
            index_logged = None
            for idx, d in enumerate(st.session_state["drivers"]):
                if d["username"] == username_logged:
                    index_logged = idx
                    driver_obj = d
                    break

            if driver_obj is not None:
                st.markdown("---")
                st.markdown(f"### {L('update_header')} – {driver_obj['first_name']} {driver_obj['last_name']}")

                with st.form("driver_update_form"):
                    status_options = L("status_options")
                    new_status = st.selectbox(
                        L("status"),
                        status_options,
                        index=status_options.index(driver_obj["status"])
                    )
                    colu1, colu2 = st.columns(2)
                    with colu1:
                        new_lat = st.number_input(L("current_lat"), value=float(driver_obj["lat"]))
                    with colu2:
                        new_lon = st.number_input(L("current_lon"), value=float(driver_obj["lon"]))
                    update_btn = st.form_submit_button(L("update_btn"))

                if update_btn and index_logged is not None:
                    updates = {
                        "status": new_status,
                        "lat": new_lat,
                        "lon": new_lon,
                    }
                    st.session_state["drivers"][index_logged].update(updates)
                    update_driver_in_db(username_logged, updates)
                    st.success(L("update_success"))

    st.markdown("---")
    st.subheader(L("all_drivers"))
    if st.session_state["drivers"]:
        df_drivers_all = pd.DataFrame(st.session_state["drivers"])
        display_cols = [
            "username", "first_name", "last_name", "age",
            "transport_type", "payment_method", "city", "status", "lat", "lon"
        ]
        st.dataframe(df_drivers_all[display_cols])
        st.subheader(L("drivers_map"))
        st.map(df_drivers_all[["lat", "lon"]])
    else:
        st.info(L("no_drivers"))

# -------------------------------------------------
# PASSENGER AREA
# -------------------------------------------------
elif mode == L("passenger_area"):
    st.header(L("passenger_header"))

    status_available = L("status_options")[0]
    status_busy = L("status_options")[1]

    available_drivers = [
        d for d in st.session_state["drivers"]
        if d["status"] == status_available
    ]

    if not available_drivers:
        st.warning(L("no_available"))
    else:
        st.write(L("passenger_intro"))

        with st.form("passenger_trip_form"):
            selected_city_for_within = None
            route_mode = st.radio(
                L("route_mode"),
                [L("within_city"), L("manual_coords"), L("preset_route")],
                horizontal=False
            )

            pickup_nb = drop_nb = None
            use_neigh = False

            if route_mode == L("within_city"):
                st.markdown("#### 🏙️ " + L("within_city"))
                selected_city_for_within = st.selectbox(
                    L("within_city_city_label"),
                    list(MALI_CITIES.keys()),
                    index=0
                )
                base_lat, base_lon = MALI_CITIES[selected_city_for_within]

                if selected_city_for_within == "Bamako":
                    use_neigh = st.checkbox(L("use_neighborhoods"), value=True)

                if use_neigh and selected_city_for_within == "Bamako":
                    st.markdown("##### 📍 " + L("pickup_neighborhood"))
                    pickup_nb = st.selectbox(L("pickup_neighborhood"), list(BKO_NEIGHBORHOODS.keys()), index=0)
                    st.markdown("##### 🎯 " + L("dropoff_neighborhood"))
                    drop_nb = st.selectbox(L("dropoff_neighborhood"), list(BKO_NEIGHBORHOODS.keys()), index=1)

                    pickup_lat, pickup_lon = BKO_NEIGHBORHOODS[pickup_nb]
                    drop_lat, drop_lon = BKO_NEIGHBORHOODS[drop_nb]
                else:
                    st.markdown("#### 📍 " + L("pickup_header"))
                    col1, col2 = st.columns(2)
                    with col1:
                        pickup_lat = st.number_input(L("pickup_lat"), value=float(base_lat))
                    with col2:
                        pickup_lon = st.number_input(L("pickup_lon"), value=float(base_lon))

                    st.markdown("#### 🎯 " + L("dropoff_header"))
                    col3, col4 = st.columns(2)
                    with col3:
                        drop_lat = st.number_input(L("drop_lat"), value=float(base_lat))
                    with col4:
                        drop_lon = st.number_input(L("drop_lon"), value=float(base_lon))

            elif route_mode == L("manual_coords"):
                st.markdown("#### 📍 " + L("pickup_header"))
                col1, col2 = st.columns(2)
                with col1:
                    pickup_lat = st.number_input(L("pickup_lat"), value=12.6392)
                with col2:
                    pickup_lon = st.number_input(L("pickup_lon"), value=-8.0029)

                st.markdown("#### 🎯 " + L("dropoff_header"))
                col3, col4 = st.columns(2)
                with col3:
                    drop_lat = st.number_input(L("drop_lat"), value=12.6500)
                with col4:
                    drop_lon = st.number_input(L("drop_lon"), value=-8.0000)

            else:
                st.markdown("#### 🚐 " + L("preset_route"))
                colc1, colc2 = st.columns(2)
                with colc1:
                    from_city = st.selectbox(L("from_city"), list(MALI_CITIES.keys()), index=0)
                with colc2:
                    to_city = st.selectbox(L("to_city"), list(MALI_CITIES.keys()), index=1)

                pickup_lat, pickup_lon = MALI_CITIES[from_city]
                drop_lat, drop_lon = MALI_CITIES[to_city]

                st.write(f"{L('pickup_header')}: **{from_city}**  →  {pickup_lat:.4f}, {pickup_lon:.4f}")
                st.write(f"{L('dropoff_header')}: **{to_city}**  →  {drop_lat:.4f}, {drop_lon:.4f}")

            submit_trip = st.form_submit_button(L("trip_btn"))

        if submit_trip:
            df_avail = pd.DataFrame(available_drivers).copy()

            trip_city = None
            if route_mode == L("within_city"):
                trip_city = selected_city_for_within
            elif route_mode == L("preset_route"):
                trip_city = from_city
            else:
                trip_city = "Manual / Unknown"

            origin_label = "Unknown pickup"
            destination_label = "Unknown dropoff"

            if route_mode == L("within_city"):
                if selected_city_for_within:
                    if (
                        selected_city_for_within == "Bamako"
                        and pickup_nb
                        and drop_nb
                        and use_neigh
                    ):
                        origin_label = f"Bamako – {pickup_nb}"
                        destination_label = f"Bamako – {drop_nb}"
                    else:
                        origin_label = f"{selected_city_for_within} (manual coords)"
                        destination_label = f"{selected_city_for_within} (manual coords)"
            elif route_mode == L("preset_route"):
                origin_label = from_city
                destination_label = to_city
            else:
                origin_label = "Manual GPS pickup"
                destination_label = "Manual GPS dropoff"

            if route_mode == L("within_city") and selected_city_for_within is not None:
                df_avail = df_avail[df_avail["city"] == selected_city_for_within]

            if df_avail.empty:
                st.warning(L("no_drivers_in_city") if route_mode == L("within_city") else L("no_available"))
            else:
                dist_to_pickup_list = []
                for _, row in df_avail.iterrows():
                    d = get_trip_distance_miles(pickup_lat, pickup_lon, row["lat"], row["lon"])
                    dist_to_pickup_list.append(d)
                df_avail["distance_to_pickup_miles"] = dist_to_pickup_list
                df_avail = df_avail.sort_values("distance_to_pickup_miles")

                trip_distance = get_trip_distance_miles(pickup_lat, pickup_lon, drop_lat, drop_lon)
                price = compute_fare(trip_distance, base_fare=base_fare, per_mile=per_mile)

                platform_commission = round(price * platform_pct / 100)
                driver_earnings = price - platform_commission

                st.subheader(L("price_header"))
                st.write(f"{L('trip_distance')}: **{trip_distance:.2f} miles**")
                st.write(f"{L('price_estimated')}: **{price:,.0f} XOF (CFA)**")
                st.write(f"{L('metric_platform_revenue')}: **{platform_commission:,.0f} XOF**")
                st.write(f"{L('metric_driver_earnings')}: **{driver_earnings:,.0f} XOF**")

                st.subheader(L("drivers_by_prox"))
                df_display = df_avail[[
                    "username", "first_name", "last_name",
                    "transport_type", "payment_method", "city", "distance_to_pickup_miles", "lat", "lon"
                ]].copy()
                df_display["distance_to_pickup_miles"] = df_display["distance_to_pickup_miles"].round(2)
                df_display = df_display.rename(columns={"distance_to_pickup_miles": "distance_to_pickup (miles)"})
                st.dataframe(df_display)

                st.subheader(L("map_pickup"))
                map_df = df_avail[["lat", "lon"]].copy()
                pickup_point = pd.DataFrame({"lat": [pickup_lat], "lon": [pickup_lon]})
                map_df = pd.concat([map_df, pickup_point], ignore_index=True)
                st.map(map_df[["lat", "lon"]])

                st.markdown("### " + L("choose_driver"))
                options = list(df_avail.index)
                option_labels = [
                    f"{row['first_name']} {row['last_name']} ({row['transport_type']} – {row['distance_to_pickup_miles']:.2f} miles)"
                    for _, row in df_avail.iterrows()
                ]

                selected_idx = st.selectbox(
                    L("select_driver"),
                    options=options,
                    format_func=lambda x: option_labels[options.index(x)]
                )

                if st.button(L("confirm_booking")):
                    selected_driver_username = df_avail.loc[selected_idx, "username"]

                    chosen_driver = None
                    for d in st.session_state["drivers"]:
                        if d["username"] == selected_driver_username:
                            d["status"] = status_busy
                            update_driver_in_db(d["username"], {"status": status_busy})
                            chosen_driver = d
                            break

                    trip_data = {
                        "driver_username": selected_driver_username,
                        "driver_name": None if chosen_driver is None else f"{chosen_driver['first_name']} {chosen_driver['last_name']}",
                        "pickup_lat": pickup_lat,
                        "pickup_lon": pickup_lon,
                        "drop_lat": drop_lat,
                        "drop_lon": drop_lon,
                        "distance_miles": trip_distance,
                        "price_xof": price,
                        "platform_commission_xof": platform_commission,
                        "driver_earnings_xof": driver_earnings,
                        "platform_pct": platform_pct,
                        "driver_pct": driver_pct,
                        "route_mode": route_mode,
                        "city": trip_city,
                        "routing_provider": ROUTING_PROVIDER if USE_REAL_ROUTING else "haversine",
                        "created_at": datetime.utcnow().isoformat(),
                        "origin_label": origin_label,
                        "destination_label": destination_label,
                        "route_summary": f"{origin_label} → {destination_label}",
                    }
                    st.session_state["current_trip"] = trip_data
                    st.session_state["trips"].append(trip_data)
                    save_trip_to_db(trip_data)

                    if chosen_driver:
                        st.success(
                            L("booking_success").format(
                                name=f"{chosen_driver['first_name']} {chosen_driver['last_name']}",
                                id=chosen_driver["username"]
                            )
                        )
                    else:
                        st.warning(L("booking_warn"))

    if st.session_state["current_trip"] is not None:
        st.markdown("---")
        trip = st.session_state["current_trip"]
        st.subheader(L("current_trip_header"))
        st.write(f"{L('driver_id_label')}: **{trip['driver_username']}**")
        st.write(f"{L('distance_label')}: **{trip['distance_miles']:.2f} miles**")
        st.write(f"{L('price_label')}: **{trip['price_xof']:,.0f} XOF (CFA)**")
        st.write(f"{L('metric_platform_revenue')}: **{trip['platform_commission_xof']:,.0f} XOF**")
        st.write(f"{L('metric_driver_earnings')}: **{trip['driver_earnings_xof']:,.0f} XOF**")
        st.write(f"{L('pickup_label')}: `{(trip['pickup_lat'], trip['pickup_lon'])}`")
        st.write(f"{L('dropoff_label')}: `{(trip['drop_lat'], trip['drop_lon'])}`")
        if "route_summary" in trip:
            st.write(f"Route: **{trip['route_summary']}**")

# -------------------------------------------------
# ADMIN DASHBOARD
# -------------------------------------------------
else:
    st.header(L("admin_header"))
    if not st.session_state["admin_ok"]:
        st.warning(L("admin_locked"))
        st.stop()

    st.write(L("admin_desc"))

    drivers = st.session_state["drivers"]
    trips = st.session_state["trips"]

    df_trips = pd.DataFrame(trips) if trips else pd.DataFrame()

    if not df_trips.empty and "created_at" in df_trips.columns:
        df_trips["created_at"] = pd.to_datetime(df_trips["created_at"], errors="coerce")

    if not df_trips.empty:
        st.markdown("### 🔎 Filters (trips)")

        colf1, colf2, colf3 = st.columns(3)

        with colf1:
            if "city" in df_trips.columns:
                city_options = sorted([c for c in df_trips["city"].dropna().unique()])
            else:
                city_options = []
            city_filter = st.multiselect(
                "City (from trips)",
                city_options,
                default=city_options if city_options else None,
            )

        with colf2:
            if "created_at" in df_trips.columns and df_trips["created_at"].notna().any():
                dates = df_trips["created_at"].dropna()
                min_date = dates.min().date()
                max_date = dates.max().date()
            else:
                from datetime import date
                today = date.today()
                min_date = max_date = today

            start_date, end_date = st.date_input(
                "Date range (created_at)",
                value=(min_date, max_date),
            )

        with colf3:
            if "routing_provider" in df_trips.columns:
                provider_options = sorted([p for p in df_trips["routing_provider"].dropna().unique()])
            else:
                provider_options = []
            provider_filter = st.multiselect(
                "Routing provider",
                provider_options,
                default=provider_options if provider_options else None,
            )

        df_trips_filtered = df_trips.copy()

        if city_options and city_filter:
            df_trips_filtered = df_trips_filtered[df_trips_filtered["city"].isin(city_filter)]

        if "created_at" in df_trips_filtered.columns and df_trips_filtered["created_at"].notna().any():
            df_trips_filtered = df_trips_filtered[
                (df_trips_filtered["created_at"].dt.date >= start_date)
                & (df_trips_filtered["created_at"].dt.date <= end_date)
            ]

        if provider_options and provider_filter and "routing_provider" in df_trips_filtered.columns:
            df_trips_filtered = df_trips_filtered[df_trips_filtered["routing_provider"].isin(provider_filter)]

    else:
        df_trips_filtered = df_trips

    col_a, col_b, col_c, col_d, col_e, col_f, col_g, col_h = st.columns(8)

    status_options = L("status_options")
    status_available = status_options[0]
    status_busy = status_options[1]
    status_offline = status_options[2]

    n_available = sum(1 for d in drivers if d["status"] == status_available)
    n_busy = sum(1 for d in drivers if d["status"] == status_busy)
    n_offline = sum(1 for d in drivers if d["status"] == status_offline)

    if not df_trips_filtered.empty:
        total_gross = float(df_trips_filtered["price_xof"].sum())
        total_platform = float(df_trips_filtered["platform_commission_xof"].sum())
        total_driver = float(df_trips_filtered["driver_earnings_xof"].sum())
        n_trips = len(df_trips_filtered)
        total_distance = float(df_trips_filtered["distance_miles"].sum()) if "distance_miles" in df_trips_filtered.columns else 0.0
    else:
        total_gross = total_platform = total_driver = total_distance = 0.0
        n_trips = 0

    with col_a:
        st.metric(L("metric_drivers"), len(drivers))
    with col_b:
        st.metric(L("metric_available"), n_available)
    with col_c:
        st.metric(L("metric_busy"), n_busy)
    with col_d:
        st.metric(L("metric_offline"), n_offline)
    with col_e:
        st.metric(L("metric_trips") + " (filtered)", n_trips)
    with col_f:
        st.metric(L("metric_revenue") + " (filtered)", f"{total_gross:,.0f}")
    with col_g:
        st.metric(L("metric_platform_revenue") + " (filtered)", f"{total_platform:,.0f}")
    with col_h:
        st.metric(L("metric_driver_earnings") + " (filtered)", f"{total_driver:,.0f}")

    st.markdown("---")
    st.subheader(L("drivers_table_header"))
    if drivers:
        df_drivers = pd.DataFrame(drivers)
        st.dataframe(df_drivers)
        csv_drivers = df_drivers.to_csv(index=False).encode("utf-8")
        st.download_button(
            label=L("download_drivers"),
            data=csv_drivers,
            file_name="drivers_mali_ride.csv",
            mime="text/csv"
        )
    else:
        st.info(L("no_drivers"))

    st.markdown("---")
    st.subheader(L("trips_table_header") + " (filtered)")
    if not df_trips_filtered.empty:
        st.dataframe(df_trips_filtered)
        csv_trips = df_trips_filtered.to_csv(index=False).encode("utf-8")
        st.download_button(
            label=L("download_trips"),
            data=csv_trips,
            file_name="trips_mali_ride_filtered.csv",
            mime="text/csv"
        )
    else:
        st.info("No trips (for current filters).")

    st.markdown("---")
    st.subheader("📍 City-level summary (filtered trips)")
    if not df_trips_filtered.empty and "city" in df_trips_filtered.columns:
        df_city = df_trips_filtered.copy()
        df_city = df_city.dropna(subset=["city"])
        if not df_city.empty:
            city_group = df_city.groupby("city").agg(
                trips_count=("price_xof", "count"),
                total_distance_miles=("distance_miles", "sum"),
                avg_distance_miles=("distance_miles", "mean"),
                total_revenue_xof=("price_xof", "sum"),
                total_platform_xof=("platform_commission_xof", "sum"),
                total_driver_xof=("driver_earnings_xof", "sum"),
            ).reset_index()

            city_group["total_distance_miles"] = city_group["total_distance_miles"].round(2)
            city_group["avg_distance_miles"] = city_group["avg_distance_miles"].round(2)

            st.dataframe(city_group)

            csv_city = city_group.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Download city summary as CSV",
                data=csv_city,
                file_name="city_summary_mali_ride.csv",
                mime="text/csv"
            )

            st.markdown("#### Trips by city (count)")
            st.bar_chart(city_group.set_index("city")["trips_count"])
        else:
            st.info("No city information for current filters.")
    else:
        st.info("No city information available.")

    st.markdown("---")
    st.subheader("🛰️ Routing provider comparison (filtered trips)")
    if not df_trips_filtered.empty and "routing_provider" in df_trips_filtered.columns:
        df_rp = df_trips_filtered.copy()
        df_rp = df_rp.dropna(subset=["routing_provider"])
        if not df_rp.empty:
            rp_group = df_rp.groupby("routing_provider").agg(
                trips_count=("price_xof", "count"),
                total_distance_miles=("distance_miles", "sum"),
                avg_distance_miles=("distance_miles", "mean"),
                total_revenue_xof=("price_xof", "sum"),
            ).reset_index()

            rp_group["total_distance_miles"] = rp_group["total_distance_miles"].round(2)
            rp_group["avg_distance_miles"] = rp_group["avg_distance_miles"].round(2)

            st.dataframe(rp_group)

            csv_rp = rp_group.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Download routing provider summary as CSV",
                data=csv_rp,
                file_name="routing_provider_summary_mali_ride.csv",
                mime="text/csv"
            )

            st.markdown("#### Trips by routing provider (count)")
            st.bar_chart(rp_group.set_index("routing_provider")["trips_count"])
        else:
            st.info("No routing provider info for current filters.")
    else:
        st.info("No routing provider info available.")

    st.markdown("---")
    st.subheader("🏆 Top drivers (filtered trips)")

    if not df_trips_filtered.empty and "driver_username" in df_trips_filtered.columns:
        df_td = df_trips_filtered.copy()
        df_td = df_td.dropna(subset=["driver_username"])

        if not df_td.empty:
            agg = df_td.groupby("driver_username").agg(
                trips_count=("price_xof", "count"),
                total_distance_miles=("distance_miles", "sum"),
                avg_distance_miles=("distance_miles", "mean"),
                total_revenue_xof=("price_xof", "sum"),
                total_platform_xof=("platform_commission_xof", "sum"),
                total_driver_xof=("driver_earnings_xof", "sum"),
            ).reset_index()

            agg["total_distance_miles"] = agg["total_distance_miles"].round(2)
            agg["avg_distance_miles"] = agg["avg_distance_miles"].round(2)

            if drivers:
                df_drivers_info = pd.DataFrame(drivers)
                df_drivers_info = df_drivers_info[[
                    "username", "first_name", "last_name", "city", "transport_type"
                ]]
                agg = agg.merge(
                    df_drivers_info,
                    how="left",
                    left_on="driver_username",
                    right_on="username"
                )

                agg["driver_name"] = agg.apply(
                    lambda r: f"{r.get('first_name', '')} {r.get('last_name', '')}".strip()
                    if (pd.notna(r.get("first_name", "")) or pd.notna(r.get("last_name", "")))
                    else r["driver_username"],
                    axis=1
                )
            else:
                agg["driver_name"] = agg["driver_username"]

            cols_order = [
                "driver_username", "driver_name", "city", "transport_type",
                "trips_count", "total_distance_miles", "avg_distance_miles",
                "total_revenue_xof", "total_platform_xof", "total_driver_xof"
            ]
            agg = agg[[c for c in cols_order if c in agg.columns]]

            agg = agg.sort_values("total_revenue_xof", ascending=False)

            top_n = st.slider("Number of top drivers to display", 3, 50, 10)
            agg_top = agg.head(top_n)

            st.dataframe(agg_top)

            csv_top = agg_top.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Download top drivers as CSV",
                data=csv_top,
                file_name="top_drivers_mali_ride.csv",
                mime="text/csv"
            )

            st.markdown("#### Revenue by driver (XOF)")
            chart_data = agg_top.set_index("driver_name")["total_revenue_xof"]
            st.bar_chart(chart_data)
        else:
            st.info("No driver data for current filters.")
    else:
        st.info("No driver username info available in trips.")

    st.markdown("---")
    st.subheader("🛣️ Top routes (filtered trips)")

    if not df_trips_filtered.empty and "route_summary" in df_trips_filtered.columns:
        df_routes = df_trips_filtered.copy()
        df_routes = df_routes.dropna(subset=["route_summary"])

        if not df_routes.empty:
            route_group = df_routes.groupby("route_summary").agg(
                trips_count=("price_xof", "count"),
                total_distance_miles=("distance_miles", "sum"),
                avg_distance_miles=("distance_miles", "mean"),
                total_revenue_xof=("price_xof", "sum"),
                total_platform_xof=("platform_commission_xof", "sum"),
                total_driver_xof=("driver_earnings_xof", "sum"),
            ).reset_index()

            route_group["total_distance_miles"] = route_group["total_distance_miles"].round(2)
            route_group["avg_distance_miles"] = route_group["avg_distance_miles"].round(2)

            route_group = route_group.sort_values("trips_count", ascending=False)

            top_r = st.slider("Number of top routes to display", 3, 50, 10)
            route_top = route_group.head(top_r)

            st.dataframe(route_top)

            csv_routes = route_top.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Download top routes as CSV",
                data=csv_routes,
                file_name="top_routes_mali_ride.csv",
                mime="text/csv"
            )

            st.markdown("#### Trips by route (count)")
            chart_routes = route_top.set_index("route_summary")["trips_count"]
            st.bar_chart(chart_routes)
        else:
            st.info("No route summary data for current filters.")
    else:
        st.info("No route summary information available in trips.")
