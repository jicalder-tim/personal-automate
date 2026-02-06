import pandas as pd
import plotly.express as px
import streamlit as st

from state.session import reset_selection


def get_idx(opts, targets, default=0):
    for t in targets:
        if t in opts:
            return opts.index(t)
    return default


def generate_metrics(data_slice, name, x_axis, y_axis, color_var, size_var):
    metrics = {"Scope": name, "Count": len(data_slice), "Channels": {}}
    if data_slice.empty:
        return metrics
    active_vars = [
        v
        for v in [x_axis, y_axis, color_var, size_var]
        if v and v in data_slice.columns
    ]

    for v in active_vars:
        if pd.api.types.is_numeric_dtype(data_slice[v]):
            metrics["Channels"][v] = {
                "Type": "Numeric",
                "Min": float(data_slice[v].min()),
                "Max": float(data_slice[v].max()),
                "Avg": float(data_slice[v].mean()),
                "Std": float(data_slice[v].std()),
            }
        elif pd.api.types.is_datetime64_any_dtype(data_slice[v]):
            metrics["Channels"][v] = {
                "Type": "DateTime",
                "Start": str(data_slice[v].min()),
                "End": str(data_slice[v].max()),
            }
        else:
            metrics["Channels"][v] = {
                "Type": "Categorical",
                "Unique": int(data_slice[v].nunique()),
                "Top": str(data_slice[v].mode().iloc[0])
                if not data_slice[v].empty
                else "-",
            }
    return metrics


def render_visuals(df, roles):
    st.markdown("### 👁️ Visualización")
    available_cols = list(df.columns)

    c1, c2, c3, c4 = st.columns(4)

    ix = get_idx(available_cols, [roles["time"], roles["spatial"]["x"]], 0)
    iy = get_idx(
        available_cols, [roles["spatial"]["y"]], 1 if len(available_cols) > 1 else 0
    )

    x_axis = c1.selectbox("Eje X", available_cols, index=ix)
    y_axis = c2.selectbox("Eje Y", available_cols, index=iy)

    col_idx = 0
    color_var = c3.selectbox("Color", [None] + available_cols, index=col_idx)

    size_opts = [None] + [
        c for c in available_cols if pd.api.types.is_numeric_dtype(df[c])
    ]
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
    # RENDER (PERSISTENCIA DE VISTA)
    # =============================================================================
    st.divider()

    c_tool, c_reset = st.columns([4, 1])
    with c_tool:
        drag_mode = st.radio(
            "Herramienta:", ["lasso", "box", "pan", "zoom"], index=0, horizontal=True
        )
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
        plot_df["_color_numeric"] = plot_df[color_var].astype("int64") // 10**9
        color_col_for_plot = "_color_numeric"

    fig = px.scatter(
        plot_df,
        x=x_axis,
        y=y_axis,
        color=color_col_for_plot,
        size=size_var,
        color_continuous_scale=palette if (is_num or is_dt) else None,
        color_discrete_sequence=getattr(px.colors.qualitative, palette)
        if not (is_num or is_dt) and palette in dir(px.colors.qualitative)
        else None,
        opacity=0.7,
        hover_data={color_col_for_plot: False, color_var: True, roles["entity"]: True}
        if roles["entity"] and color_var
        else None,
        title=f"{y_axis} vs {x_axis}",
    )

    if is_dt and color_var:
        fig.update_layout(coloraxis_colorbar=dict(title=color_var))

    if pd.api.types.is_datetime64_any_dtype(df[x_axis]):
        fig.update_xaxes(tickformat="%H:%M\n%d-%b")

    if x_axis == roles["spatial"]["x"] and y_axis == roles["spatial"]["y"]:
        fig.update_yaxes(scaleanchor="x", scaleratio=1)
        st.caption("🔒 Escala Espacial 1:1")

    # --- MAGIA DE PERSISTENCIA ---
    ui_rev = f"{x_axis}_{y_axis}"

    fig.update_layout(
        height=600,
        margin=dict(l=20, r=20, t=40, b=20),
        template="plotly_white",
        dragmode=drag_mode,
        clickmode="event+select",
        uirevision=ui_rev,
    )

    selection = st.plotly_chart(
        fig,
        use_container_width=True,
        on_select="rerun",
        selection_mode=("box", "lasso"),
        key=f"main_{st.session_state.plot_key}",
    )

    # =============================================================================
    # TELEMETRÍA
    # =============================================================================
    st.markdown("### 📊 Telemetría Comparativa")

    global_metrics = generate_metrics(df, "GLOBAL", x_axis, y_axis, color_var, size_var)

    if selection and len(selection["selection"]["point_indices"]) > 0:
        indices = selection["selection"]["point_indices"]
        selected_df = plot_df.iloc[indices]
        selection_metrics = generate_metrics(
            selected_df, "SELECCIÓN", x_axis, y_axis, color_var, size_var
        )
        st.success(f"📍 {len(selected_df)} puntos.")
    else:
        selection_metrics = {"Status": "Esperando selección..."}
        selected_df = pd.DataFrame()

    col_global, col_select = st.columns(2)
    with col_global:
        st.subheader("🌍 Global")
        st.json(global_metrics, expanded=True)
        st.download_button(
            "💾 Global CSV", df.to_csv(index=False).encode("utf-8"), "global.csv"
        )

    with col_select:
        st.subheader("🎯 Selección")
        st.json(selection_metrics, expanded=True)
        if not selected_df.empty:
            if "_color_numeric" in selected_df.columns:
                selected_df = selected_df.drop(columns=["_color_numeric"])
            st.download_button(
                "💾 Selección CSV",
                selected_df.to_csv(index=False).encode("utf-8"),
                "select.csv",
            )
