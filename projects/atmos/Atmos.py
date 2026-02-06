import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import BytesIO
from datetime import timedelta

# =============================================================================
# 0. CONFIGURACIÓN
# =============================================================================
st.set_page_config(page_title="Atmos Studio — Persistent", layout="wide")

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    div[data-testid="column"] button[kind="secondary"] {
        background-color: #f0f2f6; border: 1px solid #dce1e6; color: #31333F;
        border-radius: 4px; font-family: 'Consolas', monospace; font-size: 0.85rem;
        padding: 4px 8px; width: 100%; text-align: left; white-space: nowrap;
        overflow: hidden; text-overflow: ellipsis;
    }
    div[data-testid="column"] button[kind="secondary"]:hover {
        border-color: #ff4b4b; color: #ff4b4b; background-color: #fff;
    }
    .op-btn button { background-color: #e0e0e0 !important; font-weight: bold !important; text-align: center !important; }
    .stTextArea textarea { font-family: 'Consolas', monospace; background-color: #1e1e1e; color: #d4d4d4; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 1. CORE: GESTIÓN DE ESTADO
# =============================================================================

if "formula_input" not in st.session_state:
    st.session_state.formula_input = ""
if "plot_key" not in st.session_state:
    st.session_state.plot_key = 0


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


# =============================================================================
# 2. CARGA DE DATOS
# =============================================================================
if 'df_master' not in st.session_state:
    st.session_state.df_master = None
if 'roles' not in st.session_state:
    st.session_state.roles = None

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

# =============================================================================
# 3. CALCULADORA
# =============================================================================
st.markdown("### 🧮 Variables Derivadas")

with st.expander("Abrir Calculadora", expanded=True):
    col_vars, col_ops, col_term = st.columns([1.5, 1, 2])

    with col_vars:
        st.caption("Variables")
        with st.container(height=250):
            if len(st.session_state.df_master.columns) > 30:
                var_sel = st.selectbox("Seleccionar", st.session_state.df_master.columns)
                st.button(f"Insertar {var_sel}", on_click=append_token, args=(var_sel, True))
            else:
                for col in st.session_state.df_master.columns:
                    st.button(f"📄 {col}", key=f"btn_{col}", on_click=append_token, args=(col, True),
                              use_container_width=True)

    with col_ops:
        st.caption("Operadores")
        st.markdown('<div class="op-btn">', unsafe_allow_html=True)
        ops = ["+", "-", "*", "/", "(", ")", "**2", "sqrt", "log", "mean"]
        cols_ops = st.columns(2)
        for i, op in enumerate(ops):
            cols_ops[i % 2].button(op, key=f"op_{i}", on_click=append_token, args=(op, False), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_term:
        st.caption("Fórmula")
        st.text_area("Input", key="formula_input", height=100, label_visibility="collapsed", placeholder="...")

        st.markdown("**Guardar Resultado**")
        c_name, c_type = st.columns([1.5, 1])
        new_name = c_name.text_input("Nombre Variable", placeholder="resultado")
        var_type = c_type.selectbox("Tipo", ["Numérica (Continua)", "Categórica (Discreta)"])

        st.write("")
        c_act1, c_act2 = st.columns([2, 1])

        if c_act1.button("⚡ Calcular", type="primary", use_container_width=True):
            if st.session_state.formula_input and new_name:
                try:
                    res = st.session_state.df_master.eval(st.session_state.formula_input)
                    if var_type == "Categórica (Discreta)":
                        res = res.astype(str)
                        if new_name in st.session_state.roles["numeric"]: st.session_state.roles["numeric"].remove(
                            new_name)
                    else:
                        res = pd.to_numeric(res, errors='coerce')
                        if pd.api.types.is_numeric_dtype(res):
                            if new_name not in st.session_state.roles["numeric"]: st.session_state.roles[
                                "numeric"].append(new_name)

                    st.session_state.df_master[new_name] = res
                    st.success(f"Creada: {new_name}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

        if c_act2.button("Borrar", on_click=clear_console, use_container_width=True): pass

# =============================================================================
# 4. VISUALIZACIÓN
# =============================================================================
st.markdown("### 👁️ Visualización")
available_cols = list(df.columns)

c1, c2, c3, c4 = st.columns(4)


def get_idx(opts, targets, default=0):
    for t in targets:
        if t in opts: return opts.index(t)
    return default


ix = get_idx(available_cols, [roles["time"], roles["spatial"]["x"]], 0)
iy = get_idx(available_cols, [roles["spatial"]["y"]], 1 if len(available_cols) > 1 else 0)

x_axis = c1.selectbox("Eje X", available_cols, index=ix)
y_axis = c2.selectbox("Eje Y", available_cols, index=iy)

col_idx = 0
color_var = c3.selectbox("Color", [None] + available_cols, index=col_idx)

size_opts = [None] + [c for c in available_cols if pd.api.types.is_numeric_dtype(df[c])]
size_var = c4.selectbox("Tamaño", size_opts)

# Lógica de Paleta
is_num = color_var and pd.api.types.is_numeric_dtype(df[color_var])
is_dt = color_var and pd.api.types.is_datetime64_any_dtype(df[color_var])

if is_num or is_dt:
    pal_opts = ["Viridis", "Plasma", "Turbo", "RdBu", "Jet"]
    pal_label = "Paleta (Gradiente)"
else:
    pal_opts = ["Set1", "Set2", "Set3", "Dark2", "Pastel"]
    pal_label = "Paleta (Categoría)"

palette = st.selectbox(pal_label, pal_opts)

# =============================================================================
# 5. RENDER (PERSISTENCIA DE VISTA)
# =============================================================================
st.divider()

c_tool, c_reset = st.columns([4, 1])
with c_tool:
    drag_mode = st.radio("Herramienta:", ["lasso", "box", "pan", "zoom"], index=0, horizontal=True)
with c_reset:
    st.write("")
    st.button("🧹 Limpiar", on_click=reset_selection, use_container_width=True)

plot_df = df.copy()

if len(plot_df) > 50000:
    plot_df = plot_df.sample(50000, random_state=42)
    st.caption(f"⚠️ Muestreo visual (50k / {len(df):,})")

# Truco para Gradiente de Tiempo
color_col_for_plot = color_var
if is_dt and color_var:
    plot_df["_color_numeric"] = plot_df[color_var].astype('int64') // 10 ** 9
    color_col_for_plot = "_color_numeric"

fig = px.scatter(
    plot_df, x=x_axis, y=y_axis,
    color=color_col_for_plot,
    size=size_var,
    color_continuous_scale=palette if (is_num or is_dt) else None,
    color_discrete_sequence=getattr(px.colors.qualitative, palette) if not (is_num or is_dt) and palette in dir(
        px.colors.qualitative) else None,
    opacity=0.7,
    hover_data={color_col_for_plot: False, color_var: True, roles["entity"]: True} if roles[
                                                                                          "entity"] and color_var else None,
    title=f"{y_axis} vs {x_axis}"
)

if is_dt and color_var:
    fig.update_layout(coloraxis_colorbar=dict(title=color_var))

if pd.api.types.is_datetime64_any_dtype(df[x_axis]):
    fig.update_xaxes(tickformat="%H:%M\n%d-%b")

if x_axis == roles["spatial"]["x"] and y_axis == roles["spatial"]["y"]:
    fig.update_yaxes(scaleanchor="x", scaleratio=1)
    st.caption("🔒 Escala Espacial 1:1")

# --- MAGIA DE PERSISTENCIA ---
# Usamos las columnas de los ejes como ID de revisión.
# Si cambian las columnas, la vista se resetea.
# Si solo cambia el color (pero las columnas X/Y son las mismas), la vista se mantiene.
ui_rev = f"{x_axis}_{y_axis}"

fig.update_layout(
    height=600,
    margin=dict(l=20, r=20, t=40, b=20),
    template="plotly_white",
    dragmode=drag_mode,
    clickmode='event+select',
    uirevision=ui_rev  # <--- Esto mantiene el zoom al cambiar colores
)

selection = st.plotly_chart(fig, use_container_width=True, on_select="rerun", selection_mode=("box", "lasso"),
                            key=f"main_{st.session_state.plot_key}")

# =============================================================================
# 6. TELEMETRÍA
# =============================================================================
st.markdown("### 📊 Telemetría Comparativa")


def generate_metrics(data_slice, name):
    metrics = {"Scope": name, "Count": len(data_slice), "Channels": {}}
    if data_slice.empty: return metrics
    active_vars = [v for v in [x_axis, y_axis, color_var, size_var] if v and v in data_slice.columns]

    for v in active_vars:
        if pd.api.types.is_numeric_dtype(data_slice[v]):
            metrics["Channels"][v] = {"Type": "Numeric", "Min": float(data_slice[v].min()),
                                      "Max": float(data_slice[v].max()), "Avg": float(data_slice[v].mean()),
                                      "Std": float(data_slice[v].std())}
        elif pd.api.types.is_datetime64_any_dtype(data_slice[v]):
            metrics["Channels"][v] = {"Type": "DateTime", "Start": str(data_slice[v].min()),
                                      "End": str(data_slice[v].max())}
        else:
            metrics["Channels"][v] = {"Type": "Categorical", "Unique": int(data_slice[v].nunique()),
                                      "Top": str(data_slice[v].mode().iloc[0]) if not data_slice[v].empty else "-"}
    return metrics


global_metrics = generate_metrics(df, "GLOBAL")

if selection and len(selection["selection"]["point_indices"]) > 0:
    indices = selection["selection"]["point_indices"]
    selected_df = plot_df.iloc[indices]
    selection_metrics = generate_metrics(selected_df, "SELECCIÓN")
    st.success(f"📍 {len(selected_df)} puntos.")
else:
    selection_metrics = {"Status": "Esperando selección..."}
    selected_df = pd.DataFrame()

col_global, col_select = st.columns(2)
with col_global:
    st.subheader("🌍 Global")
    st.json(global_metrics, expanded=True)
    st.download_button("💾 Global CSV", df.to_csv(index=False).encode('utf-8'), "global.csv")

with col_select:
    st.subheader("🎯 Selección")
    st.json(selection_metrics, expanded=True)
    if not selected_df.empty:
        if "_color_numeric" in selected_df.columns:
            selected_df = selected_df.drop(columns=["_color_numeric"])
        st.download_button("💾 Selección CSV", selected_df.to_csv(index=False).encode('utf-8'), "select.csv")