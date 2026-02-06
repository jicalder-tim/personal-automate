import pandas as pd
import streamlit as st

from state.session import append_token, clear_console


def render_calculator():
    st.markdown("### 🧮 Variables Derivadas")

    with st.expander("Abrir Calculadora", expanded=True):
        col_vars, col_ops, col_term = st.columns([1.5, 1, 2])

        with col_vars:
            st.caption("Variables")
            with st.container(height=250):
                if len(st.session_state.df_master.columns) > 30:
                    var_sel = st.selectbox(
                        "Seleccionar", st.session_state.df_master.columns
                    )
                    st.button(
                        f"Insertar {var_sel}",
                        on_click=append_token,
                        args=(var_sel, True),
                    )
                else:
                    for col in st.session_state.df_master.columns:
                        st.button(
                            f"📄 {col}",
                            key=f"btn_{col}",
                            on_click=append_token,
                            args=(col, True),
                            use_container_width=True,
                        )

        with col_ops:
            st.caption("Operadores")
            st.markdown('<div class="op-btn">', unsafe_allow_html=True)
            ops = ["+", "-", "*", "/", "(", ")", "**2", "sqrt", "log", "mean"]
            cols_ops = st.columns(2)
            for i, op in enumerate(ops):
                cols_ops[i % 2].button(
                    op,
                    key=f"op_{i}",
                    on_click=append_token,
                    args=(op, False),
                    use_container_width=True,
                )
            st.markdown("</div>", unsafe_allow_html=True)

        with col_term:
            st.caption("Fórmula")
            st.text_area(
                "Input",
                key="formula_input",
                height=100,
                label_visibility="collapsed",
                placeholder="...",
            )

            st.markdown("**Guardar Resultado**")
            c_name, c_type = st.columns([1.5, 1])
            new_name = c_name.text_input("Nombre Variable", placeholder="resultado")
            var_type = c_type.selectbox(
                "Tipo", ["Numérica (Continua)", "Categórica (Discreta)"]
            )

            st.write("")
            c_act1, c_act2 = st.columns([2, 1])

            if c_act1.button("⚡ Calcular", type="primary", use_container_width=True):
                if st.session_state.formula_input and new_name:
                    try:
                        res = st.session_state.df_master.eval(
                            st.session_state.formula_input
                        )
                        if var_type == "Categórica (Discreta)":
                            res = res.astype(str)
                            if new_name in st.session_state.roles["numeric"]:
                                st.session_state.roles["numeric"].remove(new_name)
                        else:
                            res = pd.to_numeric(res, errors="coerce")
                            if pd.api.types.is_numeric_dtype(res):
                                if new_name not in st.session_state.roles["numeric"]:
                                    st.session_state.roles["numeric"].append(new_name)

                        st.session_state.df_master[new_name] = res
                        st.success(f"Creada: {new_name}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

            if c_act2.button(
                "Borrar", on_click=clear_console, use_container_width=True
            ):
                pass
