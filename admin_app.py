
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
# SIDEBAR – ADMIN AUTH with AUTO-EXPIRE DEMO MODE + LOGIN TRACKING
# ----------------------------
st.sidebar.markdown("### 🔑 " + L("admin_auth"))

# Re-use the same DEMO_END_DATE as above
DEMO_END_DATE = date(2026, 12, 31)
today = date.today()
is_demo_mode = today <= DEMO_END_DATE

# Capture who is using the dashboard (for audit/logging)
admin_email = st.sidebar.text_input("Admin email (for audit)", placeholder="you@example.com")
admin_phone = st.sidebar.text_input("Admin phone (optional)", placeholder="+223...")

if "admin_ok" not in st.session_state:
    st.session_state["admin_ok"] = False

def _log_admin_login(mode: str):
    """Internal helper to log admin login event."""
    from datetime import datetime
    info = {
        "email": admin_email.strip(),
        "phone": admin_phone.strip(),
        "mode": mode,  # "demo" or "password"
        "timestamp_iso": datetime.utcnow().isoformat(),
    }
    save_admin_login_to_db(info)

if is_demo_mode:
    # DEMO MODE: unlocked
    st.sidebar.success(
        f"✅ Demo mode active until {DEMO_END_DATE.isoformat()}. "
        "Admin dashboard is unlocked."
    )

    if st.sidebar.button("Log my admin session (demo mode)"):
        if not admin_email.strip():
            st.sidebar.warning("Please enter an email before logging your session.")
        else:
            _log_admin_login(mode="demo")
            st.sidebar.success("Admin session logged.")

    # Always allow access in demo mode
    st.session_state["admin_ok"] = True

else:
    # NORMAL MODE: require admin code
    st.sidebar.info(
        f"🔒 Demo period ended on {DEMO_END_DATE.isoformat()}. "
        "Admin code is now required."
    )

    code_input = st.sidebar.text_input(
        L("admin_code_label"),
        type="password",
        help=L("admin_code_hint")
    )
    admin_ok = st.sidebar.button("OK")

    if admin_ok:
        if code_input == ADMIN_CODE:
            if not admin_email.strip():
                st.sidebar.warning("Please enter an email before logging in.")
                st.session_state["admin_ok"] = False
            else:
                st.session_state["admin_ok"] = True
                st.sidebar.success("Admin access granted.")
                _log_admin_login(mode="password")
        else:
            st.session_state["admin_ok"] = False
            st.sidebar.error(L("admin_code_wrong"))

# FINAL GATE
if not st.session_state["admin_ok"]:
    st.warning(L("admin_locked"))
    st.stop()

