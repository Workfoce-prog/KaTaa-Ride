
import streamlit as st
import pandas as pd

from shared import (
    LANG_OPTIONS,
    labels,
    load_drivers_from_db,
    save_driver_to_db,
    update_driver_in_db,
    save_trip_to_db,
    get_trip_distance_miles,
    compute_fare,
    MALI_CITIES,
)

st.set_page_config(page_title="Mali Ride – Mobile App", layout="centered")

# ----------------------------
# LANGUAGE
# ----------------------------
lang = st.selectbox("🌍 Language / Langue / Kan", LANG_OPTIONS, index=0)

def L(key):
    return labels.get(lang, labels["English"]).get(key, key)

st.title(L("title_mobile"))
st.caption(L("subtitle"))

# ----------------------------
# SESSION STATE
# ----------------------------
if "drivers" not in st.session_state:
    st.session_state["drivers"] = load_drivers_from_db()
if "logged_driver" not in st.session_state:
    st.session_state["logged_driver"] = None
if "current_trip" not in st.session_state:
    st.session_state["current_trip"] = None
if "trips" not in st.session_state:
    st.session_state["trips"] = []

# ----------------------------
# SIMPLE MODE SWITCH (TOP)
# ----------------------------
mode = st.radio(
    L("mobile_mode_label"),
    [L("mobile_driver_tab"), L("mobile_passenger_tab")],
    horizontal=True
)

# ----------------------------
# COMMON PRICE CONTROLS (compact)
# ----------------------------
with st.expander("💰 " + L("price_settings"), expanded=False):
    base_fare = st.number_input(L("base_fare"), value=1000, min_value=0)
    per_mile = st.number_input(L("per_mile"), value=300, min_value=0)

with st.expander("💸 " + L("commission_settings"), expanded=False):
    platform_pct = st.number_input(L("platform_cut"), value=20, min_value=0, max_value=100)
    driver_pct = 100 - platform_pct
    st.write(f"{L('driver_share')}: **{driver_pct}%**")

# ----------------------------
# DRIVER MINI-APP
# ----------------------------
if mode == L("mobile_driver_tab"):
    st.subheader("👨‍✈️ " + L("driver_area"))

    with st.expander(L("tab_register"), expanded=False):
        with st.form("m_driver_reg_form"):
            first_name = st.text_input(L("first_name"))
            last_name = st.text_input(L("last_name"))
            username = st.text_input(L("driver_id"), help=L("driver_id_help"))
            pin = st.text_input(L("pin"), type="password", max_chars=4, help=L("pin_help"))
            age = st.number_input(L("age"), min_value=18, max_value=90, value=30)

            transport_type = st.selectbox(
                L("transport_type"),
                ["Car", "Moto", "Taxi", "Minibus", "Other"]
            )
            payment_method = st.multiselect(
                L("payment_methods"),
                ["Cash", "Orange Money", "Wave", "Moov Money", "Card"],
                default=["Cash", "Orange Money", "Wave"]
            )

            city = st.selectbox(L("city"), list(MALI_CITIES.keys()) + ["Other"])
            default_lat, default_lon = MALI_CITIES.get(city, (12.6392, -8.0029))
            lat = st.number_input(L("lat"), value=float(default_lat))
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

    with st.expander(L("tab_login"), expanded=True):
        if st.session_state["logged_driver"]:
            st.info(f"{L('logged_as')} {st.session_state['logged_driver']}")

        with st.form("m_driver_login_form"):
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
                status_options = L("status_options")
                new_status = st.selectbox(
                    L("status"),
                    status_options,
                    index=status_options.index(driver_obj["status"])
                )
                new_lat = st.number_input(L("current_lat"), value=float(driver_obj["lat"]))
                new_lon = st.number_input(L("current_lon"), value=float(driver_obj["lon"]))
                if st.button(L("update_btn")) and index_logged is not None:
                    updates = {
                        "status": new_status,
                        "lat": new_lat,
                        "lon": new_lon,
                    }
                    st.session_state["drivers"][index_logged].update(updates)
                    update_driver_in_db(username_logged, updates)
                    st.success(L("update_success"))

# ----------------------------
# PASSENGER MINI-APP
# ----------------------------
else:
    st.subheader("🧍‍♂️ " + L("passenger_area"))

    status_available = L("status_options")[0]
    status_busy = L("status_options")[1]

    available_drivers = [
        d for d in st.session_state["drivers"]
        if d.get("status") == status_available
    ]

    if not available_drivers:
        st.warning(L("no_available"))
    else:
        route_mode = st.radio(
            L("route_mode"),
            [L("within_city"), L("manual_coords")],
            horizontal=False
        )

        if route_mode == L("within_city"):
            city = st.selectbox(L("within_city_city_label"), list(MALI_CITIES.keys()), index=0)
            base_lat, base_lon = MALI_CITIES[city]
            pickup_lat = st.number_input(L("pickup_lat"), value=float(base_lat))
            pickup_lon = st.number_input(L("pickup_lon"), value=float(base_lon))
            drop_lat = st.number_input(L("drop_lat"), value=float(base_lat))
            drop_lon = st.number_input(L("drop_lon"), value=float(base_lon))
            trip_city = city
            origin_label = f"{city} (manual)"
            destination_label = f"{city} (manual)"
        else:
            pickup_lat = st.number_input(L("pickup_lat"), value=12.6392)
            pickup_lon = st.number_input(L("pickup_lon"), value=-8.0029)
            drop_lat = st.number_input(L("drop_lat"), value=12.6500)
            drop_lon = st.number_input(L("drop_lon"), value=-8.0000)
            trip_city = "Manual / Unknown"
            origin_label = "Manual pickup"
            destination_label = "Manual dropoff"

        if st.button(L("trip_btn")):
            df_avail = pd.DataFrame(available_drivers).copy()
            if route_mode == L("within_city"):
                df_avail = df_avail[df_avail["city"] == trip_city]

            if df_avail.empty:
                st.warning(L("no_drivers_in_city") if route_mode == L("within_city") else L("no_available"))
            else:
                dist_to_pickup = []
                for _, row in df_avail.iterrows():
                    d = get_trip_distance_miles(pickup_lat, pickup_lon, row["lat"], row["lon"])
                    dist_to_pickup.append(d)
                df_avail["distance_to_pickup_miles"] = dist_to_pickup
                df_avail = df_avail.sort_values("distance_to_pickup_miles")

                trip_distance = get_trip_distance_miles(pickup_lat, pickup_lon, drop_lat, drop_lon)
                price = compute_fare(trip_distance, base_fare=base_fare, per_mile=per_mile)
                platform_commission = round(price * platform_pct / 100)
                driver_earnings = price - platform_commission

                st.write(f"{L('trip_distance')}: **{trip_distance:.2f} miles**")
                st.write(f"{L('price_estimated')}: **{price:,.0f} XOF**")

                options = list(df_avail.index)
                option_labels = [
                    f"{row['first_name']} {row['last_name']} – {row['transport_type']} ({row['distance_to_pickup_miles']:.1f} mi)"
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

# ----------------------------
# CURRENT TRIP SUMMARY
# ----------------------------
if st.session_state["current_trip"] is not None:
    st.markdown("---")
    trip = st.session_state["current_trip"]
    st.subheader(L("current_trip_header"))
    st.write(f"{L('driver_id_label')}: **{trip['driver_username']}**")
    st.write(f"{L('distance_label')}: **{trip['distance_miles']:.2f} miles**")
    st.write(f"{L('price_label')}: **{trip['price_xof']:,.0f} XOF (CFA)**")
