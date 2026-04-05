# ✔ Dashboard multitab
# ✔ Análisis histórico
# ✔ Estadísticas por héroe
# ✔ Métricas del ETL
# ✔ Uso de SQLAlchemy
# ✔ Separación clara ETL vs Dashboard

#!/usr/bin/env python3
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from sqlalchemy import func
import sys
sys.path.insert(0, ".")

from scripts.database import SessionLocal
from scripts.models import Superhero, PowerStats, MetricasETL

# =========================================================
# CONFIGURACIÓN DE LA PÁGINA
# =========================================================
st.set_page_config(
    page_title="Dashboard Avanzado Superheroes",
    page_icon="🦸‍♂️",
    layout="wide"
)

st.title("🦸‍♂️ Dashboard Avanzado - Análisis de Superhéroes")
st.markdown("---")

db = SessionLocal()

# =========================================================
# PESTAÑAS PRINCIPALES
# =========================================================
tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 Vista General", "📈 Histórico", "🔍 Análisis", "📋 Métricas ETL"]
)

# =========================================================
# TAB 1: VISTA GENERAL
# =========================================================
with tab1:
    st.subheader("📊 Estado General del Sistema")

    col1, col2, col3 = st.columns(3)

    with col1:
        total_heroes = db.query(func.count(Superhero.id)).scalar()
        st.metric("🦸‍♂️ Total Superhéroes", total_heroes)

    with col2:
        total_stats = db.query(func.count(PowerStats.id)).scalar()
        st.metric("📊 Total PowerStats", total_stats)

    with col3:
        ultima_fecha = db.query(func.max(PowerStats.fecha_extraccion)).scalar()
        if ultima_fecha:
            st.metric(
                "⏰ Última Extracción",
                ultima_fecha.strftime("%Y-%m-%d %H:%M")
            )
        else:
            st.metric("⏰ Última Extracción", "N/A")

    st.markdown("---")

    # Último registro por superhéroe
    subq = (
        db.query(
            PowerStats.superhero_id,
            func.max(PowerStats.fecha_extraccion).label("max_fecha")
        )
        .group_by(PowerStats.superhero_id)
        .subquery()
    )

    registros_actuales = (
        db.query(
            Superhero.nombre,
            Superhero.editorial,
            PowerStats.inteligencia,
            PowerStats.fuerza,
            PowerStats.velocidad,
            PowerStats.durabilidad,
            PowerStats.poder,
            PowerStats.combate
        )
        .join(subq, PowerStats.superhero_id == subq.c.superhero_id)
        .join(Superhero, Superhero.id == PowerStats.superhero_id)
        .filter(PowerStats.fecha_extraccion == subq.c.max_fecha)
        .all()
    )

    df_actual = pd.DataFrame(
        registros_actuales,
        columns=[
            "Superhéroe", "Editorial", "Inteligencia",
            "Fuerza", "Velocidad", "Durabilidad",
            "Poder", "Combate"
        ]
    )

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(
            df_actual,
            x="Superhéroe",
            y="Fuerza",
            title="💪 Fuerza Actual por Superhéroe",
            color="Fuerza",
            color_continuous_scale="Reds"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.pie(
            df_actual,
            values="Poder",
            names="Superhéroe",
            title="⚡ Distribución de Poder"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.dataframe(df_actual, use_container_width=True)

# =========================================================
# TAB 2: HISTÓRICO
# =========================================================
with tab2:
    st.subheader("📈 Análisis Histórico")

    col1, col2 = st.columns(2)

    with col1:
        fecha_inicio = st.date_input(
            "Desde:", value=datetime.now() - timedelta(days=7)
        )

    with col2:
        fecha_fin = st.date_input("Hasta:", value=datetime.now())

    registros_hist = (
        db.query(
            PowerStats.fecha_extraccion,
            Superhero.nombre,
            PowerStats.poder
        )
        .join(Superhero)
        .filter(
            PowerStats.fecha_extraccion >= fecha_inicio,
            PowerStats.fecha_extraccion <= fecha_fin
        )
        .all()
    )

    if registros_hist:
        df_hist = pd.DataFrame(
            registros_hist,
            columns=["Fecha", "Superhéroe", "Poder"]
        )

        fig = px.line(
            df_hist,
            x="Fecha",
            y="Poder",
            color="Superhéroe",
            title="⚡ Poder en el Tiempo",
            markers=True
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        st.dataframe(df_hist, use_container_width=True)
    else:
        st.warning("No hay datos en ese rango de fechas")

# =========================================================
# TAB 3: ANÁLISIS ESTADÍSTICO (✅ CORREGIDO)
# =========================================================
with tab3:
    st.subheader("🔍 Análisis Estadístico por Superhéroe")

    heroes = db.query(Superhero).all()

    for hero in heroes:
        with st.expander(f"🦸‍♂️ {hero.nombre}"):
            stats = db.query(PowerStats).filter_by(
                superhero_id=hero.id
            ).all()

            if stats:
                fuerzas = [s.fuerza for s in stats if s.fuerza is not None]
                inteligencias = [s.inteligencia for s in stats if s.inteligencia is not None]
                poderes = [s.poder for s in stats if s.poder is not None]

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    if fuerzas:
                        st.metric("💪 Fuerza Prom.", f"{sum(fuerzas)/len(fuerzas):.1f}")
                    else:
                        st.metric("💪 Fuerza Prom.", "N/A")

                with col2:
                    if inteligencias:
                        st.metric("🧠 Inteligencia Prom.", f"{sum(inteligencias)/len(inteligencias):.1f}")
                    else:
                        st.metric("🧠 Inteligencia Prom.", "N/A")

                with col3:
                    if poderes:
                        st.metric("⚡ Poder Prom.", f"{sum(poderes)/len(poderes):.1f}")
                    else:
                        st.metric("⚡ Poder Prom.", "N/A")

                with col4:
                    st.metric("📊 Registros", len(stats))
            else:
                st.info("No hay registros para este superhéroe")

# =========================================================
# TAB 4: MÉTRICAS ETL
# =========================================================
with tab4:
    st.subheader("📋 Métricas de Ejecución ETL")

    metricas = db.query(MetricasETL).order_by(
        MetricasETL.fecha_ejecucion.desc()
    ).limit(20).all()

    if metricas:
        data = []
        for m in metricas:
            data.append({
                "Fecha": m.fecha_ejecucion,
                "Estado": m.estado,
                "Extraídos": m.registros_extraidos,
                "Guardados": m.registros_guardados,
                "Fallidos": m.registros_fallidos,
                "Tiempo (s)": round(m.tiempo_ejecucion_segundos, 2)
            })

        df_metricas = pd.DataFrame(data)
        st.dataframe(df_metricas, use_container_width=True)

        col1, col2 = st.columns(2)

        with col1:
            fig = px.bar(
                df_metricas,
                x="Fecha",
                y="Guardados",
                color="Estado",
                title="Registros Guardados por Ejecución"
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.scatter(
                df_metricas,
                x="Fecha",
                y="Tiempo (s)",
                size="Guardados",
                color="Estado",
                title="Duración de las Ejecuciones ETL"
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay métricas ETL registradas")

db.close()