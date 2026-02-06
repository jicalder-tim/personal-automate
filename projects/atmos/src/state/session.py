import streamlit as st

def init_session():
    if "formula_input" not in st.session_state:
        st.session_state.formula_input = ""
    if "plot_key" not in st.session_state:
        st.session_state.plot_key = 0
    if 'df_master' not in st.session_state:
        st.session_state.df_master = None
    if 'roles' not in st.session_state:
        st.session_state.roles = None
    if 'last_file' not in st.session_state:
        st.session_state.last_file = None

def append_token(val, is_variable=False):
    val = str(val)
    token = f"`{val}`" if is_variable else val
    current = st.session_state.formula_input
    if current and not current.endswith(" ") and val not in [")", "/", "*", "**"]:
        st.session_state.formula_input += " "
    st.session_state.formula_input += token

def clear_console():
    st.session_state.formula_input = ""

def reset_selection():
    st.session_state.plot_key += 1
