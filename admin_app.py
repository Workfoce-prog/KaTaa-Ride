
import streamlit as st
import pandas as pd
from datetime import date

from shared import (
    LANG_OPTIONS,
    labels,
    load_drivers_from_db,
    load_trips_from_db,
    ADMIN_CODE,
)

st.set_page_config(page_title="Mali Ride – Admin Dashboard", layout="wide")

# ----------------------------
# LANGUAGE
# ----------------------------
st.sidebar.markdown("### 🌍 Language / Langue / Kan")
lang = st.sidebar.selectbox("", LANG_OPTIONS, index=0)

def L(key):
    return labels.get(lang, labels["English"]).get(key, key)

st.title(L("title_admin"))
st.caption(L("subtitle"))

# ----------------------------
# SIDEBAR – ADMIN AUTH
# ----------------------------
st.sidebar.markdown("### 🔑 " + L("admin_auth"))
code_input = st.sidebar.text_input(L("admin_code_label"), type="password", help=L("admin_code_hint"))
admin_ok = st.sidebar.button("OK")

if "admin_ok" not in st.session_state:
    st.session_state["admin_ok"] = False

if admin_ok:
    if code_input == ADMIN_CODE:
        st.session_state["admin_ok"] = True
    else:
        st.session_state["admin_ok"] = False
        st.sidebar.error(L("admin_code_wrong"))

if not st.session_state["admin_ok"]:
    st.warning(L("admin_locked"))
    st.stop()

# ----------------------------
# LOAD DATA
# ----------------------------
if "drivers" not in st.session_state:
    st.session_state["drivers"] = load_drivers_from_db()
if "trips" not in st.session_state:
    st.session_state["trips"] = load_trips_from_db()

drivers = st.session_state["drivers"]
trips = st.session_state["trips"]

df_trips = pd.DataFrame(trips) if trips else pd.DataFrame()

if not df_trips.empty and "created_at" in df_trips.columns:
    df_trips["created_at"] = pd.to_datetime(df_trips["created_at"], errors="coerce")

# ----------------------------
# FILTERS
# ----------------------------
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

# ----------------------------
# METRICS
# ----------------------------
st.header(L("admin_header"))
st.write(L("admin_desc"))

col_a, col_b, col_c, col_d, col_e, col_f, col_g, col_h = st.columns(8)

status_options = L("status_options")
status_available = status_options[0]
status_busy = status_options[1]
status_offline = status_options[2] if len(status_options) > 2 else "Offline"

n_available = sum(1 for d in drivers if d.get("status") == status_available)
n_busy = sum(1 for d in drivers if d.get("status") == status_busy)
n_offline = sum(1 for d in drivers if d.get("status") == status_offline)

if not df_trips_filtered.empty:
    total_gross = float(df_trips_filtered["price_xof"].sum())
    total_platform = float(df_trips_filtered["platform_commission_xof"].sum())
    total_driver = float(df_trips_filtered["driver_earnings_xof"].sum())
    n_trips = len(df_trips_filtered)
else:
    total_gross = total_platform = total_driver = 0.0
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

# ----------------------------
# DRIVERS TABLE
# ----------------------------
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

# ----------------------------
# TRIPS TABLE
# ----------------------------
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

# ----------------------------
# CITY SUMMARY
# ----------------------------
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

# ----------------------------
# ROUTING PROVIDER SUMMARY
# ----------------------------
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

# ----------------------------
# TOP DRIVERS
# ----------------------------
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
            import pandas as _pd
            df_drivers_info = _pd.DataFrame(drivers)
            df_drivers_info = df_drivers_info[
                ["username", "first_name", "last_name", "city", "transport_type"]
            ]
            agg = agg.merge(
                df_drivers_info,
                how="left",
                left_on="driver_username",
                right_on="username"
            )

            agg["driver_name"] = agg.apply(
                lambda r: f"{r.get('first_name', '')} {r.get('last_name', '')}".strip()
                if (pd.notna(r.get('first_name', '')) or pd.notna(r.get('last_name', '')))
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

# ----------------------------
# TOP ROUTES
# ----------------------------
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
