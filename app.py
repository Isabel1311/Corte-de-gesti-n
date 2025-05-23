import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import pydeck as pdk

st.set_page_config(page_title="Corte de Gestión", layout="wide")  # <-- SIEMPRE PRIMERO

# ------- ESTILO GLOBAL Y FONDO INSTITUCIONAL + KPIs como tarjetas ---------
st.markdown("""
    <style>
    body, .main, .block-container {
        background-color: #F5F6FA !important;
    }
    .kpi-row {
        display: flex;
        gap: 1.4rem;
        justify-content: center;
        width: 99%;
        margin: 0 auto 1.5rem auto;
        max-width: 1200px;
    }
    .kpi-card {
        background: #fff;
        border-radius: 18px;
        box-shadow: 0 4px 20px 0 rgba(20, 33, 61, 0.10);
        border: 2px solid #FCA31122;
        padding: 1rem 0.5rem 0.7rem 0.5rem;
        flex: 1 1 0;
        display: flex;
        flex-direction: column;
        align-items: center;
        min-width: 140px;
        min-height: 115px;
    }
    .kpi-icon {
        font-size: 2.6rem;
        margin-bottom: 0.15rem;
    }
    .kpi-label {
        font-size: 1.12rem;
        font-weight: 500;
        color: #222c;
        margin-bottom: 0.07rem;
    }
    .kpi-value {
        font-size: 2.2rem;
        font-weight: 700;
        margin-top: 0.13rem;
        letter-spacing: -1px;
    }
    .separador {
        height: 28px;
        margin: 0.7rem 0 1.5rem 0;
        border: none;
        border-bottom: 3px solid #14213D11;
        width: 97%;
        max-width: 1200px;
        margin-left: auto;
        margin-right: auto;
    }
    </style>
""", unsafe_allow_html=True)

# -------- Frase institucional y logo ---------
st.markdown(
    '<div style="text-align:center; font-size:1.4rem; color:#14213D; font-weight:600; margin-top:1.5rem;">'
    'Gestión que transforma, datos que mandan.'
    '</div>',
    unsafe_allow_html=True
)

logo_svg = """
<svg width="370" height="74" viewBox="0 0 370 74" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect width="370" height="74" rx="24" fill="#14213D"/>
  <text x="185" y="50" text-anchor="middle" fill="#FCA311" font-size="38" font-family="Segoe UI,Arial,sans-serif" font-weight="bold">
    Corte de Gestión
  </text>
</svg>
"""
st.markdown(
    f'<div style="display:flex;justify-content:center;margin-bottom:0.7rem;">{logo_svg}</div>',
    unsafe_allow_html=True
)

st.sidebar.title("Filtros y Configuración")
uploaded_file = st.sidebar.file_uploader("Carga tu archivo Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, sheet_name=0)
    df.columns = df.columns.str.strip().str.upper()
    df["FE.ENTRADA"] = pd.to_datetime(df["FE.ENTRADA"], errors='coerce')
    df["FECHA DE ATENCION"] = pd.to_datetime(df["FECHA DE ATENCION"], errors='coerce')

    proveedor = st.sidebar.multiselect("Proveedor", sorted(df["PROVEEDOR"].dropna().unique()))
    supervisor = st.sidebar.multiselect("Supervisor", sorted(df["SUPERVISOR"].dropna().unique()))
    estatus = st.sidebar.multiselect("Estatus", sorted(df["ESTATUS 2"].dropna().unique()))
    dz_filter = st.sidebar.multiselect("DZ", sorted(df["DZ"].dropna().unique()))
    fecha_inicio = st.sidebar.date_input("Fecha de entrada (inicio)", df["FE.ENTRADA"].min())
    fecha_fin = st.sidebar.date_input("Fecha de entrada (fin)", df["FE.ENTRADA"].max())

    df_filt = df.copy()
    if proveedor:
        df_filt = df_filt[df_filt["PROVEEDOR"].isin(proveedor)]
    if supervisor:
        df_filt = df_filt[df_filt["SUPERVISOR"].isin(supervisor)]
    if estatus:
        df_filt = df_filt[df_filt["ESTATUS 2"].isin(estatus)]
    if dz_filter:
        df_filt = df_filt[df_filt["DZ"].isin(dz_filter)]
    df_filt = df_filt[(df_filt["FE.ENTRADA"] >= pd.to_datetime(fecha_inicio)) & (df_filt["FE.ENTRADA"] <= pd.to_datetime(fecha_fin))]

    # KPIs individuales como cards
    st.markdown('<div class="kpi-row">', unsafe_allow_html=True)
    total_ordenes = len(df_filt)
    en_tiempo = df_filt["ESTATUS 2"].str.contains("EN TIEMPO", na=False, case=False).sum()
    fuera_tiempo = df_filt["ESTATUS 2"].str.contains("FUERA", na=False, case=False).sum()
    sabatina = df_filt["SABATINA?"].str.upper().eq("SI").sum()
    tiene_sucursal = "SUCURSAL" in df_filt.columns
    sucursales = df_filt["SUCURSAL"].nunique() if tiene_sucursal else None
    kpi_cols = st.columns(5 if tiene_sucursal else 4)

    with kpi_cols[0]:
        st.markdown(f"""
            <div class='kpi-card'>
                <div class='kpi-icon'>📋</div>
                <div class='kpi-label'>Total de Órdenes</div>
                <div class='kpi-value'>{total_ordenes:,}</div>
            </div>
        """, unsafe_allow_html=True)

    with kpi_cols[1]:
        st.markdown(f"""
            <div class='kpi-card'>
                <div class='kpi-icon'>⏱️</div>
                <div class='kpi-label'>En Tiempo</div>
                <div class='kpi-value' style='color: #188038'>{en_tiempo:,}</div>
            </div>
        """, unsafe_allow_html=True)

    with kpi_cols[2]:
        st.markdown(f"""
            <div class='kpi-card'>
                <div class='kpi-icon'>⚠️</div>
                <div class='kpi-label'>Fuera de Tiempo</div>
                <div class='kpi-value' style='color: #b88b20'>{fuera_tiempo:,}</div>
            </div>
        """, unsafe_allow_html=True)

    with kpi_cols[3]:
        st.markdown(f"""
            <div class='kpi-card'>
                <div class='kpi-icon'>📅</div>
                <div class='kpi-label'>Sabatinas</div>
                <div class='kpi-value' style='color: #a03131'>{sabatina:,}</div>
            </div>
        """, unsafe_allow_html=True)

    if tiene_sucursal:
        with kpi_cols[4]:
            st.markdown(f"""
                <div class='kpi-card'>
                    <div class='kpi-icon'>🏢</div>
                    <div class='kpi-label'>Sucursales</div>
                    <div class='kpi-value' style='color: #3053a0'>{sucursales:,}</div>
                </div>
            """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # --------- Separador visual entre KPIs y Tabs ---------
    st.markdown('<hr class="separador">', unsafe_allow_html=True)

    # ---- Tabs principales (incluye Sucursales) ----
    tabs = st.tabs([
        "👷🏼 Proveedores", 
        "DZ", 
        "📍 Zonas (CR)", 
        "🏢 Sucursales",
        "🧑🏻‍💻 Supervisores", 
        "🟢🟡🔴 Estatus", 
        "⚠️ Tabla General"
    ])

    ## --------- PROVEEDORES ----------
    with tabs[0]:
        st.header("Panel Comparativo de Proveedores")
        prov_grp = df_filt.groupby("PROVEEDOR").agg(
            Ordenes=("ORDEN", "count"),
            En_Tiempo=("ESTATUS 2", lambda x: (x.str.contains("EN TIEMPO", na=False, case=False)).sum()),
            Fuera_Tiempo=("ESTATUS 2", lambda x: (x.str.contains("FUERA", na=False, case=False)).sum())
        )
        prov_grp["% En Tiempo"] = (prov_grp["En_Tiempo"] / prov_grp["Ordenes"] * 100).round(1)
        prov_grp["% Fuera Tiempo"] = (prov_grp["Fuera_Tiempo"] / prov_grp["Ordenes"] * 100).round(1)
        prov_grp = prov_grp.sort_values("Ordenes", ascending=False).head(30)
        st.dataframe(prov_grp)

        fig_prov = px.bar(prov_grp, x=prov_grp.index, y=["% En Tiempo", "% Fuera Tiempo"],
                          barmode='group', title="Proveedores: % En Tiempo vs % Fuera de Tiempo",
                          labels={"value": "Porcentaje", "PROVEEDOR": "Proveedor"})
        fig_prov.update_traces(texttemplate='%{y}%', textposition='outside')
        fig_prov.update_layout(xaxis_tickangle=-30, legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig_prov, use_container_width=True)

    ## --------- DZ ----------
    with tabs[1]:
        st.header("Análisis por DZ")
        dz_grp = df_filt["DZ"].value_counts().reset_index()
        dz_grp.columns = ["DZ", "Ordenes"]
        st.dataframe(dz_grp)
        figdz = px.bar(dz_grp.head(15), x="DZ", y="Ordenes", text="Ordenes",
                       title="Órdenes por DZ (Top 15)", labels={"Ordenes": "Órdenes"})
        figdz.update_traces(textposition='outside')
        figdz.update_layout(xaxis_tickangle=-30)
        st.plotly_chart(figdz, use_container_width=True)

        # Mapa por DZ (coordenadas simuladas)
        dz_mapa = dz_grp.copy()
        dz_mapa["lat"] = 25.5 + np.random.rand(len(dz_mapa)) * 0.5
        dz_mapa["lon"] = -100.3 + np.random.rand(len(dz_mapa)) * 0.5
        st.subheader("Mapa de Calor por DZ (simulado)")
        st.pydeck_chart(pdk.Deck(
            initial_view_state=pdk.ViewState(
                latitude=dz_mapa["lat"].mean(), longitude=dz_mapa["lon"].mean(), zoom=9, pitch=0,
            ),
            layers=[
                pdk.Layer(
                    "ScatterplotLayer",
                    data=dz_mapa,
                    get_position='[lon, lat]',
                    get_fill_color='[30, 100, 200, 160]',
                    get_radius='Ordenes * 35',
                    pickable=True,
                ),
            ],
            tooltip={"text": "DZ: {DZ}\nÓrdenes: {Ordenes}"}
        ))

    ## --------- ZONAS (CR) ----------
    with tabs[2]:
        st.header("Mapa de Zonas con Más Órdenes (por CR)")
        zonas = df_filt["CR"].value_counts().reset_index()
        zonas.columns = ["CR", "Ordenes"]
        zonas["lat"] = 25.5 + np.random.rand(len(zonas)) * 0.5
        zonas["lon"] = -100.3 + np.random.rand(len(zonas)) * 0.5
        st.dataframe(zonas[["CR", "Ordenes"]])

        st.pydeck_chart(pdk.Deck(
            initial_view_state=pdk.ViewState(
                latitude=zonas["lat"].mean(), longitude=zonas["lon"].mean(), zoom=9, pitch=0,
            ),
            layers=[
                pdk.Layer(
                    "ScatterplotLayer",
                    data=zonas,
                    get_position='[lon, lat]',
                    get_fill_color='[200, 30, 0, 160]',
                    get_radius='Ordenes * 30',
                    pickable=True,
                ),
            ],
            tooltip={"text": "CR: {CR}\nÓrdenes: {Ordenes}"}
        ))

    ## --------- SUCURSALES ----------
    with tabs[3]:
        st.header("Órdenes por Sucursal")
        if tiene_sucursal:
            suc_grp = df_filt["SUCURSAL"].value_counts().reset_index()
            suc_grp.columns = ["SUCURSAL", "ÓRDENES"]
            st.dataframe(suc_grp)
            fig_suc = px.bar(suc_grp.head(15), x="SUCURSAL", y="ÓRDENES", text="ÓRDENES",
                             title="Órdenes por Sucursal (Top 15)")
            fig_suc.update_traces(textposition='outside')
            fig_suc.update_layout(xaxis_tickangle=-30)
            st.plotly_chart(fig_suc, use_container_width=True)
        else:
            st.info("No se encontró la columna 'SUCURSAL' en tus datos.")

    ## --------- SUPERVISORES ----------
    with tabs[4]:
        st.header("Órdenes por Supervisor")
        ordenes_sup = df_filt["SUPERVISOR"].value_counts().reset_index()
        ordenes_sup.columns = ["SUPERVISOR", "ÓRDENES"]
        st.dataframe(ordenes_sup)
        fig_sup = px.bar(ordenes_sup.head(15), x="SUPERVISOR", y="ÓRDENES", text="ÓRDENES",
                         title="Órdenes por Supervisor (Top 15)")
        fig_sup.update_traces(textposition='outside')
        fig_sup.update_layout(xaxis_tickangle=-30)
        st.plotly_chart(fig_sup, use_container_width=True)

    ## --------- ESTATUS ----------
    with tabs[5]:
        st.header("Distribución por Estatus")
        estatus_dist = df_filt["ESTATUS 2"].value_counts().reset_index()
        estatus_dist.columns = ["ESTATUS", "ÓRDENES"]
        fig_est = px.pie(estatus_dist, values="ÓRDENES", names="ESTATUS", title="Distribución de Órdenes por Estatus",
                         hole=0.4)
        fig_est.update_traces(textinfo='percent+label', pull=[0.05]*len(estatus_dist))
        st.plotly_chart(fig_est, use_container_width=True)

    ## --------- TABLA GENERAL + EXPORTACIÓN ----------
    with tabs[6]:
        st.header("Tabla Detallada Filtrada")
        st.dataframe(df_filt)

        def to_excel(df):
            import io
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Filtrado')
            return output.getvalue()

        st.download_button(
            label="📤 Descargar tabla filtrada en Excel",
            data=to_excel(df_filt),
            file_name="tabla_filtrada.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

else:
    st.info("Por favor, sube tu archivo Excel para comenzar.")
