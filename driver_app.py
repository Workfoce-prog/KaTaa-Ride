
import streamlit as st
import pandas as pd

from shared import (
    LANG_OPTIONS,
    labels,
    load_drivers_from_db,
    save_driver_to_db,
    update_driver_in_db,
    MALI_CITIES,
)

st.set_page_config(page_title="Mali Ride – Driver App", layout="centered")

# ----------------------------
# LANGUAGE
# ----------------------------
st.sidebar.markdown("### 🌍 Language / Langue / Kan")
lang = st.sidebar.selectbox("", LANG_OPTIONS, index=0)

def L(key):
    return labels.get(lang, labels["English"]).get(key, key)

st.title(L("title_driver"))
st.caption(L("subtitle"))

# ----------------------------
# SESSION STATE
# ----------------------------
if "drivers" not in st.session_state:
    st.session_state["drivers"] = load_drivers_from_db()
if "logged_driver" not in st.session_state:
    st.session_state["logged_driver"] = None

# ----------------------------
# DRIVER AREA
# ----------------------------
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
    try:
        st.map(df_drivers_all[["lat", "lon"]])
    except Exception:
        st.info("Map could not be displayed.")
else:
    st.info(L("no_drivers"))
