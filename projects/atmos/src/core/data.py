import pandas as pd
from io import BytesIO
import streamlit as st

@st.cache_data(show_spinner=False)
def load_data_fast(file_bytes, filename):
    try:
        data = BytesIO(file_bytes)
        if filename.endswith('.csv'):
            try:
                preview = pd.read_csv(data, nrows=5)
                data.seek(0)
                date_cols = []
                for col in preview.columns:
                    cl = col.lower()
                    if cl == 't' or any(x in cl for x in ['timestamp', 'date', 'time', 'fecha']):
                        date_cols.append(col)
                if date_cols:
                    df = pd.read_csv(data, parse_dates=date_cols)
                else:
                    df = pd.read_csv(data)
            except:
                data.seek(0)
                df = pd.read_csv(data)
        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(data)
        else:
            try:
                df = pd.read_csv(data)
            except:
                data.seek(0)
                df = pd.read_csv(data, sep=None, engine='python')

        df.columns = df.columns.str.strip()

        for c in df.columns:
            is_potential_date = False
            if df[c].dtype == object or pd.api.types.is_numeric_dtype(df[c]):
                if c.lower() == 't' or any(x in c.lower() for x in ['timestamp', 'date', 'time']):
                    is_potential_date = True

            if is_potential_date or pd.api.types.is_datetime64_any_dtype(df[c]):
                try:
                    df[c] = pd.to_datetime(df[c], utc=True, errors='coerce')
                    if df[c].dt.tz is not None:
                        df[c] = df[c].dt.tz_localize(None)
                    continue
                except:
                    pass

            if df[c].dtype == object:
                sample = df[c].dropna().head(50)
                if not sample.empty and sample.astype(str).str.match(r'^-?\d+(\.\d+)?$').all():
                    df[c] = pd.to_numeric(df[c], errors='coerce')
        return df
    except Exception as e:
        return str(e)


def detect_roles_fast(df):
    roles = {"time": None, "entity": None, "spatial": {"x": None, "y": None, "z": None}, "numeric": []}

    for c in df.select_dtypes(include=['datetime']).columns:
        if c.lower() in ['t', 'timestamp', 'time', 'fecha', 'date']:
            roles["time"] = c
            break
    if roles["time"] is None:
        for c in df.select_dtypes(include=['datetime']).columns:
            roles["time"] = c
            break

    for c in df.select_dtypes(include=['number']).columns:
        cl = c.lower()
        if cl in ["x", "easting", "lon", "longitude"]:
            roles["spatial"]["x"] = c
        elif cl in ["y", "northing", "lat", "latitude"]:
            roles["spatial"]["y"] = c
        elif cl in ["z", "alt", "altura", "elevation", "cota"]:
            roles["spatial"]["z"] = c
        else:
            roles["numeric"].append(c)

    for c in df.select_dtypes(include=['object', 'category']).columns:
        if roles["entity"] is None and df[c].nunique() < 400:
            roles["entity"] = c
    return roles
