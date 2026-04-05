#!/usr/bin/env python3
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from sqlalchemy import func, and_
import sys
sys.path.insert(0, ".")

from scripts.database import SessionLocal
from scripts.models import Superhero, PowerStats

# =========================================================
# CONFIGURACIÓN DE LA PÁGINA
# =========================================================
st.set_page_config(
    page_title="Dashboard Interactivo Superheroes",
    page_icon="🎛️",
    layout="wide"
)

# CSS personalizado
st.markdown("""
<style>
.metric-box {
    background-color: #f0f2f6;
    padding: 20px;
    border-radius: 10px;
    margin: 10px 0;
}
</style>
""", unsafe_allow_html=True)

st.title("🎛️ Dashboard Interactivo - Exploración de Superhéroes")

# =========================================================
# CONEXIÓN A BD
# =========================================================
db = SessionLocal()

# =========================================================
# SIDEBAR - CONTROLES
# =========================================================
st.sidebar.markdown("## 🔧 Controles")

# Editoriales disponibles
editoriales = [
    e[0] for e in db.query(Superhero.editorial)
    .filter(Superhero.editorial.isnot(None))
    .distinct()
    .all()
]

editoriales_sel = st.sidebar.multiselect(
    "📚 Editorial",
    options=editoriales,
    default=editoriales
)

# Rango de fechas
col1, col2 = st.sidebar.columns(2)
with col1:
    fecha_inicio = st.sidebar.date_input(
        "📅 Desde:",
        value=datetime.now() - timedelta(days=30)
    )
with col2:
    fecha_fin = st.sidebar.date_input(
        "📅 Hasta:",
        value=datetime.now()
    )

# Filtros de poder
col1, col2 = st.sidebar.columns(2)
with col1:
    poder_min = st.sidebar.slider(
        "⚡ Poder mínimo",
        0, 100, value=0
    )
with col2:
    poder_max = st.sidebar.slider(
        "⚡ Poder máximo",
        0, 100, value=100
    )

# =========================================================
# CONSULTA FILTRADA
# =========================================================
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
).join(PowerStats).filter(
    and_(
        Superhero.editorial.in_(editoriales_sel),
        PowerStats.fecha_extraccion >= fecha_inicio,
        PowerStats.fecha_extraccion <= fecha_fin,
        PowerStats.poder >= poder_min,
        PowerStats.poder <= poder_max
    )
).all()

# =========================================================
# DATAFRAME
# =========================================================
data = []
for r in registros:
    poder_prom = sum([
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
        "Poder Promedio": round(poder_prom, 2),
        "Fecha": r.fecha_extraccion
    })

df = pd.DataFrame(data)

# =========================================================
# CONTENIDO PRINCIPAL
# =========================================================
if not df.empty:
    # -----------------------------------------------------
    # KPIs
    # -----------------------------------------------------
    st.markdown("### 📊 Indicadores Clave")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("🦸‍♂️ Superhéroes", df["Superhéroe"].nunique())
    with col2:
        st.metric("⚡ Poder Máximo", f"{df['Poder Promedio'].max():.1f}")
    with col3:
        st.metric("⚡ Poder Mínimo", f"{df['Poder Promedio'].min():.1f}")
    with col4:
        st.metric("⚡ Poder Promedio", f"{df['Poder Promedio'].mean():.1f}")
    with col5:
        st.metric("📊 Registros", len(df))

    st.markdown("---")

    # -----------------------------------------------------
    # GRÁFICAS
    # -----------------------------------------------------
    col1, col2 = st.columns(2)

    with col1:
        fig = px.box(
            df,
            x="Editorial",
            y="Poder Promedio",
            color="Editorial",
            title="📦 Distribución de Poder por Editorial"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.scatter(
            df,
            x="Fuerza",
            y="Inteligencia",
            size="Poder Promedio",
            color="Editorial",
            hover_name="Superhéroe",
            title="💥 Fuerza vs Inteligencia"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Evolución temporal
    st.markdown("### 📈 Evolución Temporal del Poder")

    df_time = (
        df.groupby(["Fecha", "Superhéroe"])["Poder Promedio"]
        .mean()
        .reset_index()
    )

    fig = px.line(
        df_time,
        x="Fecha",
        y="Poder Promedio",
        color="Superhéroe",
        markers=True
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # -----------------------------------------------------
    # TABLA INTERACTIVA
    # -----------------------------------------------------
    st.markdown("### 📋 Datos Detallados")

    col1, col2 = st.columns(2)
    with col1:
        mostrar_todos = st.checkbox("Mostrar todos los registros", value=False)
    with col2:
        columnas = st.multiselect(
            "Columnas a mostrar",
            df.columns.tolist(),
            default=[
                "Superhéroe", "Editorial",
                "Poder", "Poder Promedio",
                "Fecha"
            ]
        )

    if mostrar_todos:
        st.dataframe(df[columnas], use_container_width=True, height=600)
    else:
        st.dataframe(df[columnas].head(20), use_container_width=True)

    # -----------------------------------------------------
    # DESCARGA
    # -----------------------------------------------------
    st.markdown("---")
    csv = df.to_csv(index=False)
    st.download_button(
        label="⬇️ Descargar datos como CSV",
        data=csv,
        file_name=f"superheroes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

else:
    st.warning("⚠️ No hay datos que coincidan con los filtros seleccionados")

db.close()