import streamlit as st
from datetime import timedelta
import pandas as pd
from ..core.data import load_data_fast, detect_roles_fast

def render_sidebar():
    with st.sidebar:
        st.header("🗂️ Proyecto")
        uploaded_file = st.file_uploader("Datos", type=["csv", "xlsx"], key="upl_main")

        if uploaded_file:
            if st.session_state.get('last_file') != uploaded_file.name:
                with st.spinner("Procesando..."):
                    res = load_data_fast(uploaded_file.getvalue(), uploaded_file.name)
                    if isinstance(res, pd.DataFrame):
                        st.session_state.df_master = res
                        st.session_state.roles = detect_roles_fast(res)
                        st.session_state.last_file = uploaded_file.name
                        st.session_state.formula_input = ""
                        st.rerun()
                    else:
                        st.error(f"Error: {res}")

        if st.session_state.df_master is None:
            st.info("Carga un archivo para comenzar.")
            st.stop()

        df = st.session_state.df_master.copy()
        roles = st.session_state.roles

        st.markdown("---")
        st.subheader("✂️ Filtros Base")

        if roles["entity"]:
            uniques = sorted(df[roles["entity"]].astype(str).unique())
            ents = st.multiselect(f"{roles['entity']}", uniques, default=uniques)
            df = df[df[roles["entity"]].isin(ents)]

        if roles["time"]:
            tmin, tmax = df[roles["time"]].min(), df[roles["time"]].max()
            if pd.notnull(tmin) and pd.notnull(tmax):
                min_v, max_v = tmin.to_pydatetime(), tmax.to_pydatetime()
                if min_v != max_v:
                    trange = st.slider("Rango Temporal", min_value=min_v, max_value=max_v, value=(min_v, max_v),
                                       format="DD/MM/YY HH:mm", step=timedelta(minutes=1))
                    df = df[(df[roles["time"]] >= trange[0]) & (df[roles["time"]] <= trange[1])]
        
        return df
