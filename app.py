
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import pydeck as pdk
import numpy as np

st.set_page_config(page_title="Dashboard de Gestión", layout="wide")

st.sidebar.title("Filtros y Configuración")
uploaded_file = st.sidebar.file_uploader("Carga tu archivo Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, sheet_name=0)
    df.columns = df.columns.str.strip().str.upper()
    df["FE.ENTRADA"] = pd.to_datetime(df["FE.ENTRADA"], errors='coerce')
    df["FECHA DE ATENCION"] = pd.to_datetime(df["FECHA DE ATENCION"], errors='coerce')

    proveedor = st.sidebar.multiselect("Proveedor", options=sorted(df["PROVEEDOR"].dropna().unique()), default=None)
    supervisor = st.sidebar.multiselect("Supervisor", options=sorted(df["SUPERVISOR"].dropna().unique()), default=None)
    estatus = st.sidebar.multiselect("Estatus", options=sorted(df["ESTATUS 2"].dropna().unique()), default=None)
    dz_filter = st.sidebar.multiselect("DZ", options=sorted(df["DZ"].dropna().unique()), default=None)
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

    # --- KPIs principales ---
    total_ordenes = len(df_filt)
    en_tiempo = df_filt["ESTATUS 2"].str.contains("EN TIEMPO", na=False, case=False).sum()
    fuera_tiempo = df_filt["ESTATUS 2"].str.contains("FUERA", na=False, case=False).sum()
    sabatina = df_filt["SABATINA?"].str.upper().eq("SI").sum()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📋 Total de Órdenes", total_ordenes)
    col2.metric("⏱️ En Tiempo", en_tiempo)
    col3.metric("⚠️ Fuera de Tiempo", fuera_tiempo)
    col4.metric("🗓️ Sabatinas", sabatina)

    st.markdown("## Panel Comparativo de Proveedores")
    st.markdown("Comparativo de desempeño de proveedores con KPIs clave")

    # --- Panel comparativo de proveedores ---
    prov_grp = df_filt.groupby("PROVEEDOR").agg(
        Ordenes=("ORDEN", "count"),
        En_Tiempo=("ESTATUS 2", lambda x: (x.str.contains("EN TIEMPO", na=False, case=False)).sum()),
        Fuera_Tiempo=("ESTATUS 2", lambda x: (x.str.contains("FUERA", na=False, case=False)).sum())
    )
    prov_grp["% En Tiempo"] = (prov_grp["En_Tiempo"] / prov_grp["Ordenes"]).round(2) * 100
    prov_grp["% Fuera Tiempo"] = (prov_grp["Fuera_Tiempo"] / prov_grp["Ordenes"]).round(2) * 100
    prov_grp = prov_grp.sort_values("Ordenes", ascending=False).head(10)

    st.dataframe(prov_grp)

    fig, ax = plt.subplots(figsize=(8,4))
    prov_grp[["% En Tiempo", "% Fuera Tiempo"]].plot.bar(stacked=False, ax=ax)
    ax.set_ylabel("% Órdenes")
    ax.set_title("Comparativo % En Tiempo vs % Fuera de Tiempo (Top 10 Proveedores)")
    plt.xticks(rotation=45, ha="right")
    st.pyplot(fig)

    # --- Análisis por DZ ---
    st.markdown("## Análisis por DZ")
    dz_grp = df_filt["DZ"].value_counts().reset_index()
    dz_grp.columns = ["DZ", "Ordenes"]
    st.dataframe(dz_grp)

    figdz, axdz = plt.subplots(figsize=(8,4))
    dz_grp.set_index("DZ").head(10).plot(kind="bar", ax=axdz)
    axdz.set_ylabel("Órdenes")
    axdz.set_title("Órdenes por DZ (Top 10)")
    plt.xticks(rotation=45, ha="right")
    st.pyplot(figdz)

    # --- Mapa de zonas con más órdenes (por CR) ---
    st.markdown("## Mapa de Zonas con Más Órdenes (por CR)")
    zonas = df_filt["CR"].value_counts().reset_index()
    zonas.columns = ["CR", "Ordenes"]
    np.random.seed(42)
    zonas["lat"] = 25.5 + np.random.rand(len(zonas)) * 0.5  # Monterrey aprox
    zonas["lon"] = -100.3 + np.random.rand(len(zonas)) * 0.5

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

    st.markdown("#### Detalle por zona (CR)")
    st.dataframe(zonas[["CR", "Ordenes"]])

    # --- Mapa de calor por DZ (simulado) ---
    st.markdown("## Mapa de Calor por DZ (simulado)")
    dz_mapa = dz_grp.copy()
    dz_mapa["lat"] = 25.5 + np.random.rand(len(dz_mapa)) * 0.5
    dz_mapa["lon"] = -100.3 + np.random.rand(len(dz_mapa)) * 0.5
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

    # --- Otras gráficas y tabla general ---
    st.markdown("### Órdenes por Supervisor")
    ordenes_sup = df_filt["SUPERVISOR"].value_counts().head(10)
    fig3, ax3 = plt.subplots()
    ordenes_sup.plot(kind="barh", ax=ax3, color="gray")
    ax3.set_xlabel("Órdenes")
    ax3.set_ylabel("Supervisor")
    st.pyplot(fig3)

    st.markdown("### Distribución por Estatus")
    fig2, ax2 = plt.subplots()
    df_filt["ESTATUS 2"].value_counts().plot.pie(autopct='%1.1f%%', ax=ax2)
    ax2.set_ylabel("")
    st.pyplot(fig2)

    st.markdown("### Tabla Detallada Filtrada")
    st.dataframe(df_filt)

    @st.cache_data
    def to_excel(df):
        import io
        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine='openpyxl')
        df.to_excel(writer, index=False, sheet_name='Filtrado')
        writer.save()
        return output.getvalue()

    st.download_button(
        label="Descargar tabla filtrada en Excel",
        data=to_excel(df_filt),
        file_name="tabla_filtrada.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.markdown("---")
    st.caption("Dashboard generado con Streamlit | Innovación y gestión inteligente ✨")

else:
    st.info("Por favor, sube tu archivo Excel para comenzar.")
