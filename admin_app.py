
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
# ----------------------------
# ----------------------------
# SIDEBAR – ADMIN (FULLY UNLOCKED FOR REAL-TIME DEMO)
# ----------------------------
st.sidebar.markdown("### 🔑 " + L("admin_auth"))

st.sidebar.success(
    "✅ Admin dashboard is currently **UNLOCKED** for real-time demo.\n"
    "Anyone with the link can view metrics."
)

# Always treat admin as authenticated
st.session_state["admin_ok"] = True
