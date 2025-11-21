# Mali Ride App (Uber-style demo for Mali, Streamlit)

This is a demo ride-hailing app for Mali built with Streamlit.

## Features

- Driver area
  - Driver registration (name, age, transport type, city, GPS, payment methods).
  - Driver login + update status (Available/Busy/Offline) and location.
  - Drivers stored in Firestore (if configured) or in-memory.

- Passenger area
  - Trip request within a city, manual GPS, or city-to-city.
  - Optional Bamako neighborhood pickup/dropoff.
  - Pricing algorithm: base fare + XOF per mile.
  - Distance from real routing APIs:
    - OpenRouteService (default, using OpenStreetMap)
    - Google Distance Matrix (optional)
  - Nearest available driver is selected by distance to pickup.
  - Trip stored for analytics with:
    - city
    - routing_provider
    - distance_miles
    - price_xof
    - platform_commission_xof
    - driver_earnings_xof
    - origin_label / destination_label
    - route_summary

- Admin dashboard
  - Protected by simple ADMIN_CODE in `app.py`.
  - Filters by city, date range, routing provider.
  - Metrics: total trips, revenue, platform commission, driver earnings, distance.
  - City summary and routing provider summary.
  - Top drivers leaderboard (by revenue, trips, distance).
  - Top routes leaderboard (most common flows).
  - CSV downloads for drivers, trips, city summary, routing summary, top drivers, top routes.

- Language support
  - English
  - French
  - Bambara

## Running locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Environment variables

For routing APIs (optional but recommended):

- `ORS_API_KEY` – OpenRouteService API key
- `GOOGLE_MAPS_API_KEY` – Google Maps API key (if you switch ROUTING_PROVIDER to `"google"`)

If these are not set, the app falls back to haversine distance.

## Firestore configuration (optional)

In Streamlit Cloud or local `.streamlit/secrets.toml`, add:

```toml
[gcp]
firestore_project = "YOUR_GCP_PROJECT_ID"
credentials_json = "FULL_JSON_STRING_OF_SERVICE_ACCOUNT"
```

If this is not configured, the app will show a warning and use in-memory lists for drivers and trips.

## Deploying to Streamlit Cloud

1. Push this folder to a new GitHub repo.
2. In Streamlit Cloud, create a new app pointing to `app.py`.
3. Set environment variables:
   - `ORS_API_KEY`
   - optionally `GOOGLE_MAPS_API_KEY`
4. Set secrets for Firestore if you want persistent storage.

Enjoy building your Mali ride platform demo! 🇲🇱


---

## Multi-App Setup (Driver / Passenger / Admin / Mobile)

In addition to the combined `app.py`, this project also includes **separate apps**:

- `driver_app.py` – Driver-only app (registration, login, status & location update, driver map).
- `passenger_app.py` – Passenger-only app (request ride, pricing, nearest-driver selection).
- `admin_app.py` – Admin dashboard only (filters, analytics, top drivers, top routes).
- `mobile_app.py` – Condensed, mobile-friendly UI with a simple switch between Driver and Passenger modes.

### Run a specific app locally

```bash
# Driver-only app
streamlit run driver_app.py

# Passenger-only app
streamlit run passenger_app.py

# Admin-only dashboard
streamlit run admin_app.py

# Mobile-friendly combined app
streamlit run mobile_app.py
```

On Streamlit Cloud, you can create **separate deployed apps** for each of these entry points
(e.g., one URL for drivers, one for passengers, one internal URL for admin).
