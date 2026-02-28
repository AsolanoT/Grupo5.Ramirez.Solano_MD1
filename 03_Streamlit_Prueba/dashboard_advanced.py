#!/usr/bin/env python3
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from sqlalchemy import func, desc
import sys
sys.path.insert(0, '.')

from scripts.database import SessionLocal
from scripts.models import Ciudad, RegistroClima, MetricasETL

st.set_page_config(
    page_title="Dashboard Avanzado clima",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌍 Dashboard Avanzado - Análisis de Clima")
st.markdown("---")

# Crear conexión a la base de datos
db = SessionLocal()

# Pestañas principales
tab1, tab2, tab3, tab4 = st.tabs(["📊 Vista General", "📈 Histórico", "🔍 Análisis", "📋 Métricas ETL"])

with tab1:
    st.subheader("Datos Actuales")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        ciudades_count = db.query(func.count(Ciudad.id)).scalar()
        st.metric("🏙️ Ciudades", ciudades_count)
    
    with col2:
        registros_count = db.query(func.count(RegistroClima.id)).scalar()
        st.metric("📊 Registros Totales", registros_count)
    
    with col3:
        ultima_fecha = db.query(func.max(RegistroClima.fecha_extraccion)).scalar()
        if ultima_fecha:
            st.metric("⏰ Última Actualización", ultima_fecha.strftime("%Y-%m-%d %H:%M"))
        else:
            st.metric("⏰ Última Actualización", "Sin datos")
    
    st.markdown("---")
    
    # CORRECCIÓN: Obtener datos actuales (último registro por ciudad)
    # Método 1: Usando subquery (más compatible con PostgreSQL)
    subquery = db.query(
        RegistroClima.ciudad_id,
        func.max(RegistroClima.fecha_extraccion).label('max_fecha')
    ).group_by(RegistroClima.ciudad_id).subquery()
    
    registros_actuales = db.query(
        Ciudad.nombre,
        RegistroClima.temperatura,
        RegistroClima.humedad,
        RegistroClima.velocidad_viento,
        RegistroClima.descripcion
    ).join(
        RegistroClima, 
        Ciudad.id == RegistroClima.ciudad_id
    ).join(
        subquery,
        (RegistroClima.ciudad_id == subquery.c.ciudad_id) & 
        (RegistroClima.fecha_extraccion == subquery.c.max_fecha)
    ).all()
    
    # Si no hay datos con el método anterior, intenta con el método alternativo
    if not registros_actuales:
        # Método 2: Obtener todos y filtrar en Python (menos eficiente pero funciona)
        st.info("Usando método alternativo para cargar datos...")
        todos_registros = db.query(
            Ciudad.nombre,
            RegistroClima.temperatura,
            RegistroClima.humedad,
            RegistroClima.velocidad_viento,
            RegistroClima.descripcion,
            RegistroClima.fecha_extraccion,
            RegistroClima.ciudad_id
        ).join(Ciudad).order_by(RegistroClima.fecha_extraccion.desc()).all()
        
        # Filtrar para obtener solo el último registro por ciudad
        ultimos_por_ciudad = {}
        for registro in todos_registros:
            if registro.ciudad_id not in ultimos_por_ciudad:
                ultimos_por_ciudad[registro.ciudad_id] = registro
        
        registros_actuales = [(r.nombre, r.temperatura, r.humedad, r.velocidad_viento, r.descripcion) 
                              for r in ultimos_por_ciudad.values()]
    
    if registros_actuales:
        df_actual = pd.DataFrame(registros_actuales, columns=[
            'Ciudad', 'Temperatura', 'Humedad', 'Viento', 'Descripción'
        ])
        
        # Gráficas lado a lado
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(df_actual, x='Ciudad', y='Temperatura',
                        title='Temperatura Actual', color='Temperatura',
                        color_continuous_scale='RdYlBu_r')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.pie(df_actual, values='Humedad', names='Ciudad',
                        title='Distribución de Humedad')
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        st.dataframe(df_actual, use_container_width=True)
    else:
        st.warning("No hay datos disponibles. Por favor, ejecuta primero el script populate_db.py")

with tab2:
    st.subheader("Análisis Histórico")
    
    # Rango de fechas
    col1, col2 = st.columns(2)
    
    with col1:
        fecha_inicio = st.date_input("Desde:", value=datetime.now() - timedelta(days=7))
    
    with col2:
        fecha_fin = st.date_input("Hasta:", value=datetime.now())
    
    # Convertir fechas a datetime
    fecha_inicio_dt = datetime.combine(fecha_inicio, datetime.min.time())
    fecha_fin_dt = datetime.combine(fecha_fin, datetime.max.time())
    
    # Filtra por fechas
    registros_historicos = db.query(
        RegistroClima,
        Ciudad.nombre
    ).join(Ciudad).filter(
        RegistroClima.fecha_extraccion >= fecha_inicio_dt,
        RegistroClima.fecha_extraccion <= fecha_fin_dt
    ).order_by(RegistroClima.fecha_extraccion).all()
    
    if registros_historicos:
        data = []
        for registro, ciudad_nombre in registros_historicos:
            data.append({
                'Fecha': registro.fecha_extraccion,
                'Ciudad': ciudad_nombre,
                'Temperatura': registro.temperatura,
                'Humedad': registro.humedad,
                'Viento': registro.velocidad_viento
            })
        
        df_historico = pd.DataFrame(data)
        
        # Gráfica de temperatura en el tiempo
        fig = px.line(df_historico, x='Fecha', y='Temperatura',
                     color='Ciudad', title='Temperatura en el Tiempo',
                     markers=True)
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        st.dataframe(df_historico, use_container_width=True)
    else:
        st.warning(f"No hay datos en el rango {fecha_inicio} a {fecha_fin}")

with tab3:
    st.subheader("Análisis Estadístico")
    
    # Estadísticas por ciudad
    ciudades = db.query(Ciudad).all()
    
    if ciudades:
        for ciudad in ciudades:
            with st.expander(f"📍 {ciudad.nombre}"):
                registros = db.query(RegistroClima).filter_by(ciudad_id=ciudad.id).all()
                
                if registros:
                    temps = [r.temperatura for r in registros]
                    humeds = [r.humedad for r in registros]
                    vientos = [r.velocidad_viento for r in registros]
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("🌡️ Temp Prom.", f"{sum(temps)/len(temps):.1f}°C")
                    with col2:
                        st.metric("💧 Humedad Prom.", f"{sum(humeds)/len(humeds):.1f}%")
                    with col3:
                        st.metric("💨 Viento Prom.", f"{sum(vientos)/len(vientos):.1f} km/h")
                    with col4:
                        st.metric("📊 Registros", len(registros))
                else:
                    st.info(f"No hay registros para {ciudad.nombre}")
    else:
        st.warning("No hay ciudades registradas en la base de datos")

with tab4:
    st.subheader("Métricas de Ejecución ETL")
    
    # Nota: Necesitarás crear la tabla MetricasETL primero
    # Por ahora, mostraremos un mensaje informativo
    st.info("""
    ⚠️ **Módulo de Métricas en desarrollo**
    
    Para habilitar esta sección, necesitas:
    1. Actualizar el modelo MetricasETL en models.py
    2. Ejecutar migrate para crear la tabla
    3. Modificar el extractor para guardar métricas
    
    Mientras tanto, puedes ver los registros históricos en las otras pestañas.
    """)
    
    # Opcional: Mostrar estadísticas simples de registros
    st.subheader("📊 Estadísticas de Registros por Ciudad")
    
    stats = db.query(
        Ciudad.nombre,
        func.count(RegistroClima.id).label('total_registros'),
        func.avg(RegistroClima.temperatura).label('temp_promedio'),
        func.max(RegistroClima.temperatura).label('temp_maxima'),
        func.min(RegistroClima.temperatura).label('temp_minima')
    ).join(RegistroClima).group_by(Ciudad.nombre).all()
    
    if stats:
        df_stats = pd.DataFrame(stats, columns=['Ciudad', 'Registros', 'Temp Prom', 'Temp Max', 'Temp Min'])
        st.dataframe(df_stats, use_container_width=True)
        
        fig = px.bar(df_stats, x='Ciudad', y='Registros', 
                    title='Distribución de Registros por Ciudad',
                    color='Ciudad')
        st.plotly_chart(fig, use_container_width=True)

# Cerrar conexión
db.close()