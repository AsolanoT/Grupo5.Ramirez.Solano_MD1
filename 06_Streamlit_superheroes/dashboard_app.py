# 👉 Sí, ese dashboard de Streamlit lee los datos ya almacenados en la base de datos (PostgreSQL en Linux)
# 👉 NO consume la API
# 👉 NO hace ETL
# 👉 Solo transforma y visualiza los datos para el usuario

#!/usr/bin/env python3
import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import func
import sys
sys.path.insert(0, ".")

from scripts.database import SessionLocal
from scripts.models import Superhero, PowerStats, Apariencia, MetricasETL

# =========================================================
# CONFIGURACIÓN DE LA PÁGINA
# =========================================================
st.set_page_config(
    page_title="Dashboard Superheroes ETL",
    page_icon="🦸‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🦸‍♂️ Dashboard de Superheroes - ETL SuperheroAPI")
st.markdown("---")

# =========================================================
# CONEXIÓN A BASE DE DATOS
# =========================================================
db = SessionLocal()

try:
    # =====================================================
    # CARGA DE DATOS
    # =====================================================
    registros = db.query(
        Superhero.nombre,
        Superhero.editorial,
        PowerStats.inteligencia,
        PowerStats.fuerza,
        PowerStats.velocidad,
        PowerStats.durabilidad,
        PowerStats.poder,
        PowerStats.combate,
        PowerStats.fecha_extraccion
    ).join(PowerStats).all()

    data = []
    for r in registros:
        poder_total = sum([
            r.inteligencia or 0,
            r.fuerza or 0,
            r.velocidad or 0,
            r.durabilidad or 0,
            r.poder or 0,
            r.combate or 0
        ]) / 6

        data.append({
            "Superhéroe": r.nombre,
            "Editorial": r.editorial,
            "Inteligencia": r.inteligencia,
            "Fuerza": r.fuerza,
            "Velocidad": r.velocidad,
            "Durabilidad": r.durabilidad,
            "Poder": r.poder,
            "Combate": r.combate,
            "Poder Promedio": round(poder_total, 2),
            "Fecha": r.fecha_extraccion
        })

    df = pd.DataFrame(data)

    # =====================================================
    # SIDEBAR - FILTROS
    # =====================================================
    st.sidebar.title("🔧 Filtros")

    editoriales = df["Editorial"].dropna().unique()
    editorial_filtro = st.sidebar.multiselect(
        "Selecciona Editorial:",
        options=editoriales,
        default=editoriales
    )

    df_filtrado = df[df["Editorial"].isin(editorial_filtro)]

    # =====================================================
    # MÉTRICAS PRINCIPALES
    # =====================================================
    st.subheader("📊 Métricas Principales")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("🦸‍♂️ Total Superhéroes", df_filtrado["Superhéroe"].nunique())

    with col2:
        st.metric("⚡ Poder Promedio", f"{df_filtrado['Poder Promedio'].mean():.1f}")

    with col3:
        max_poder = df_filtrado.loc[df_filtrado["Poder Promedio"].idxmax()]
        st.metric("🏆 Más Poderoso", max_poder["Superhéroe"])

    with col4:
        st.metric("📄 Total Registros", len(df_filtrado))

    st.markdown("---")

    # =====================================================
    # VISUALIZACIONES
    # =====================================================
    st.subheader("📈 Visualizaciones")

    col1, col2 = st.columns(2)

    # Ranking de poder
    with col1:
        fig_rank = px.bar(
            df_filtrado.sort_values("Poder Promedio", ascending=False).head(15),
            x="Superhéroe",
            y="Poder Promedio",
            color="Editorial",
            title="🏆 Top 15 Superhéroes por Poder Promedio"
        )
        st.plotly_chart(fig_rank, use_container_width=True)

    # Poder por editorial
    with col2:
        fig_editorial = px.box(
            df_filtrado,
            x="Editorial",
            y="Poder Promedio",
            title="📦 Distribución de Poder por Editorial"
        )
        st.plotly_chart(fig_editorial, use_container_width=True)

    col1, col2 = st.columns(2)

    # Scatter Fuerza vs Inteligencia
    with col1:
        fig_scatter = px.scatter(
            df_filtrado,
            x="Fuerza",
            y="Inteligencia",
            size="Poder Promedio",
            color="Editorial",
            hover_name="Superhéroe",
            title="💥 Fuerza vs Inteligencia"
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    # Radar de stats
    with col2:
        hero_select = st.selectbox(
            "Selecciona un Superhéroe:",
            df_filtrado["Superhéroe"].unique()
        )

        hero_data = df_filtrado[df_filtrado["Superhéroe"] == hero_select].iloc[0]

        fig_radar = px.line_polar(
            r=[
                hero_data["Inteligencia"],
                hero_data["Fuerza"],
                hero_data["Velocidad"],
                hero_data["Durabilidad"],
                hero_data["Poder"],
                hero_data["Combate"]
            ],
            theta=["Inteligencia", "Fuerza", "Velocidad", "Durabilidad", "Poder", "Combate"],
            line_close=True,
            title=f"📊 Perfil de Poder - {hero_select}"
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    st.markdown("---")

    # =====================================================
    # TABLA DETALLADA
    # =====================================================
    st.subheader("📋 Datos Detallados")
    st.dataframe(
        df_filtrado.sort_values("Poder Promedio", ascending=False),
        use_container_width=True,
        height=450
    )

    # =====================================================
    # MÉTRICAS ETL
    # =====================================================
    st.subheader("⚙️ Métricas del ETL")
    metricas = db.query(MetricasETL).order_by(
        MetricasETL.fecha_ejecucion.desc()
    ).limit(5).all()

    for m in metricas:
        st.markdown(
            f"- 🕒 **{m.fecha_ejecucion}** | "
            f"Estado: **{m.estado}** | "
            f"Guardados: **{m.registros_guardados}** | "
            f"Tiempo: **{m.tiempo_ejecucion_segundos:.2f}s**"
        )

finally:
    db.close()