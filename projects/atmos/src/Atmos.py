import streamlit as st
from state.session import init_session
from ui.calculator import render_calculator
from ui.sidebar import render_sidebar
from ui.styles import CSS
from ui.visuals import render_visuals

# =============================================================================
# 0. CONFIGURACIÓN
# =============================================================================
st.set_page_config(page_title="Atmos Studio — Persistent", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)

# =============================================================================
# 1. INIT SESSION
# =============================================================================
init_session()

# =============================================================================
# 2. SIDEBAR & DATA LOADING
# =============================================================================
df = render_sidebar()

# =============================================================================
# 3. MAIN APP
# =============================================================================
if df is not None:
    render_calculator()
    render_visuals(df, st.session_state.roles)
