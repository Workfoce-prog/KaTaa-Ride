
import streamlit as st
import pandas as pd

from shared import (
    LANG_OPTIONS,
    labels,
    load_drivers_from_db,
    save_trip_to_db,
    get_trip_distance_miles,
    compute_fare,
    MALI_CITIES,
    BKO_NEIGHBORHOODS,
)

st.set_page_config(page_title="Mali Ride – Passenger App", layout="centered")

# ----------------------------
# LANGUAGE
# ----------------------------
st.sidebar.markdown("### 🌍 Language / Langue / Kan")
lang = st.sidebar.selectbox("", LANG_OPTIONS, index=0)

def L(key):
    return labels.get(lang, labels["English"]).get(key, key)

st.title(L("title_passenger"))
st.caption(L("subtitle"))

# ----------------------------
# SESSION STATE
# ----------------------------
if "drivers" not in st.session_state:
    st.session_state["drivers"] = load_drivers_from_db()
if "current_trip" not in st.session_state:
    st.session_state["current_trip"] = None
if "trips" not in st.session_state:
    st.session_state["trips"] = []

# ----------------------------
# SIDEBAR PRICING
# ----------------------------
st.sidebar.markdown("### ⚙️ " + L("price_settings"))
base_fare = st.sidebar.number_input(L("base_fare"), value=1000, min_value=0)
per_mile = st.sidebar.number_input(L("per_mile"), value=300, min_value=0)

st.sidebar.markdown("### 💸 " + L("commission_settings"))
platform_pct = st.sidebar.number_input(L("platform_cut"), value=20, min_value=0, max_value=100)
driver_pct = 100 - platform_pct
st.sidebar.write(f"{L('driver_share')}: **{driver_pct}%**")

st.sidebar.markdown("---")
st.sidebar.markdown("### ℹ️ " + L("city_coords"))
for city, (clat, clon) in MALI_CITIES.items():
    st.sidebar.write(f"- **{city}** ≈ {clat:.4f}, {clon:.4f}")

# ----------------------------
# PASSENGER AREA
# ----------------------------
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
            try:
                st.map(map_df[["lat", "lon"]])
            except Exception:
                st.info("Map could not be displayed.")

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
                    "routing_provider": "openrouteservice",
                    "created_at": pd.Timestamp.utcnow().isoformat(),
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
