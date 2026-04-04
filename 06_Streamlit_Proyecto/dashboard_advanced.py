#!/usr/bin/env python3
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from sqlalchemy import func, desc, and_
import sys
sys.path.insert(0, '.')

from scripts.database import SessionLocal
from scripts.models import Heroe, MetricasHeroe, MetricasETL

st.set_page_config(
    page_title="Dashboard Avanzado de Superhéroes",
    page_icon="🦸",
    layout="wide"
)

st.title("🦸 Dashboard Avanzado - Análisis de Superhéroes")
st.markdown("---")

# Crear conexión a la base de datos
db = SessionLocal()

# Pestañas principales
tab1, tab2, tab3, tab4 = st.tabs(["📊 Vista General", "📈 Análisis de Poder", "🔍 Estadísticas por Editorial", "📋 Métricas ETL"])

with tab1:
    st.subheader("Datos Generales de Superhéroes")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        heroes_count = db.query(func.count(Heroe.id)).scalar()
        st.metric("🦸 Total Héroes", heroes_count)
    
    with col2:
        editoriales_count = db.query(func.count(func.distinct(Heroe.editorial))).scalar()
        st.metric("🏢 Editoriales", editoriales_count)
    
    with col3:
        # Promedio de poder general
        poder_promedio = db.query(func.avg(Heroe.poder)).scalar()
        if poder_promedio:
            st.metric("⚡ Poder Promedio", f"{poder_promedio:.1f}")
        else:
            st.metric("⚡ Poder Promedio", "N/A")
    
    with col4:
        ultima_actualizacion = db.query(func.max(Heroe.fecha_actualizacion)).scalar()
        if ultima_actualizacion:
            st.metric("⏰ Última Actualización", ultima_actualizacion.strftime("%Y-%m-%d"))
        else:
            st.metric("⏰ Última Actualización", "Sin datos")
    
    st.markdown("---")
    
    # Obtener todos los héroes para visualización
    heroes = db.query(Heroe).all()
    
    if heroes:
        data = []
        for heroe in heroes:
            data.append({
                'Nombre': heroe.nombre,
                'Editorial': heroe.editorial or 'Desconocida',
                'Inteligencia': heroe.inteligencia or 0,
                'Fuerza': heroe.fuerza or 0,
                'Velocidad': heroe.velocidad or 0,
                'Durabilidad': heroe.durabilidad or 0,
                'Poder': heroe.poder or 0,
                'Combate': heroe.combate or 0,
                'Alineación': heroe.alineacion or 'Desconocida',
                'Género': heroe.genero or 'Desconocido'
            })
        
        df = pd.DataFrame(data)
        
        # Filtros en sidebar
        st.sidebar.title("🔧 Filtros")
        
        editoriales = ['Todas'] + sorted(df['Editorial'].unique().tolist())
        editorial_seleccionada = st.sidebar.selectbox("Editorial:", editoriales)
        
        if editorial_seleccionada != 'Todas':
            df_filtrado = df[df['Editorial'] == editorial_seleccionada]
        else:
            df_filtrado = df
        
        # Gráficas lado a lado
        col1, col2 = st.columns(2)
        
        with col1:
            # Top 10 héroes por poder
            top_10_poder = df_filtrado.nlargest(10, 'Poder')[['Nombre', 'Poder', 'Editorial']]
            fig = px.bar(top_10_poder, x='Nombre', y='Poder', color='Editorial',
                        title='Top 10 Héroes por Nivel de Poder',
                        labels={'Poder': 'Nivel de Poder'})
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Distribución por editorial
            editorial_counts = df_filtrado['Editorial'].value_counts().reset_index()
            editorial_counts.columns = ['Editorial', 'Cantidad']
            fig = px.pie(editorial_counts, values='Cantidad', names='Editorial',
                        title='Distribución por Editorial')
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Gráfica de radar de powerstats promedio
        st.subheader("📊 Powerstats Promedio por Editorial")
        
        powerstats = ['Inteligencia', 'Fuerza', 'Velocidad', 'Durabilidad', 'Poder', 'Combate']
        df_stats = df_filtrado.groupby('Editorial')[powerstats].mean().reset_index()
        
        fig = go.Figure()
        for _, row in df_stats.iterrows():
            fig.add_trace(go.Scatterpolar(
                r=[row[stat] for stat in powerstats],
                theta=powerstats,
                fill='toself',
                name=row['Editorial']
            ))
        
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=True,
            title="Comparación de Powerstats por Editorial"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        st.dataframe(df_filtrado, use_container_width=True)
    else:
        st.warning("No hay datos disponibles. Por favor, ejecuta primero el script populate_db.py")

with tab2:
    st.subheader("Análisis Detallado de Powerstats")
    
    heroes = db.query(Heroe).all()
    
    if heroes:
        data = []
        for heroe in heroes:
            data.append({
                'Nombre': heroe.nombre,
                'Editorial': heroe.editorial or 'Desconocida',
                'Inteligencia': heroe.inteligencia or 0,
                'Fuerza': heroe.fuerza or 0,
                'Velocidad': heroe.velocidad or 0,
                'Durabilidad': heroe.durabilidad or 0,
                'Poder': heroe.poder or 0,
                'Combate': heroe.combate or 0
            })
        
        df = pd.DataFrame(data)
        
        # Selector de powerstat
        powerstat_seleccionado = st.selectbox(
            "Selecciona Powerstat a analizar:",
            ['Inteligencia', 'Fuerza', 'Velocidad', 'Durabilidad', 'Poder', 'Combate']
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Distribución del powerstat seleccionado
            fig = px.histogram(df, x=powerstat_seleccionado, color='Editorial',
                              title=f'Distribución de {powerstat_seleccionado}',
                              nbins=20)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Top 10 en el powerstat seleccionado
            top_10 = df.nlargest(10, powerstat_seleccionado)[['Nombre', 'Editorial', powerstat_seleccionado]]
            fig = px.bar(top_10, x='Nombre', y=powerstat_seleccionado, color='Editorial',
                        title=f'Top 10 en {powerstat_seleccionado}')
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Matriz de correlación
        st.subheader("📈 Matriz de Correlación entre Powerstats")
        corr_matrix = df[powerstats].corr()
        
        fig = px.imshow(corr_matrix, 
                       text_auto=True,
                       aspect="auto",
                       color_continuous_scale='RdBu_r',
                       title="Correlación entre Powerstats")
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Scatter plot comparativo
        st.subheader("🔍 Comparación entre Powerstats")
        col1, col2 = st.columns(2)
        
        with col1:
            x_axis = st.selectbox("Eje X:", powerstats, index=0)
        with col2:
            y_axis = st.selectbox("Eje Y:", powerstats, index=4)
        
        fig = px.scatter(df, x=x_axis, y=y_axis, color='Editorial',
                        hover_data=['Nombre'], size='Poder',
                        title=f'{x_axis} vs {y_axis}')
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("Estadísticas por Editorial")
    
    # Obtener editoriales únicas
    editoriales = db.query(Heroe.editorial).distinct().all()
    editoriales = [e[0] for e in editoriales if e[0]]
    
    if editoriales:
        for editorial in editoriales:
            with st.expander(f"🏢 {editorial}"):
                # Estadísticas para esta editorial
                stats = db.query(
                    func.count(Heroe.id).label('total'),
                    func.avg(Heroe.inteligencia).label('int_prom'),
                    func.avg(Heroe.fuerza).label('fue_prom'),
                    func.avg(Heroe.velocidad).label('vel_prom'),
                    func.avg(Heroe.durabilidad).label('dur_prom'),
                    func.avg(Heroe.poder).label('pod_prom'),
                    func.avg(Heroe.combate).label('com_prom'),
                    func.max(Heroe.poder).label('pod_max'),
                    func.min(Heroe.poder).label('pod_min')
                ).filter(Heroe.editorial == editorial).first()
                
                if stats:
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("📊 Total Héroes", stats.total)
                    with col2:
                        st.metric("⚡ Poder Promedio", f"{stats.pod_prom:.1f}" if stats.pod_prom else "N/A")
                    with col3:
                        st.metric("⬆️ Poder Máximo", f"{stats.pod_max}" if stats.pod_max else "N/A")
                    with col4:
                        st.metric("⬇️ Poder Mínimo", f"{stats.pod_min}" if stats.pod_min else "N/A")
                    
                    # Gráfica de powerstats promedio
                    powerstats_prom = {
                        'Inteligencia': stats.int_prom or 0,
                        'Fuerza': stats.fue_prom or 0,
                        'Velocidad': stats.vel_prom or 0,
                        'Durabilidad': stats.dur_prom or 0,
                        'Poder': stats.pod_prom or 0,
                        'Combate': stats.com_prom or 0
                    }
                    
                    df_prom = pd.DataFrame({
                        'Powerstat': list(powerstats_prom.keys()),
                        'Valor': list(powerstats_prom.values())
                    })
                    
                    fig = px.bar(df_prom, x='Powerstat', y='Valor',
                                title=f'Powerstats Promedio - {editorial}',
                                color='Valor', color_continuous_scale='Viridis')
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Lista de héroes de esta editorial
                    heroes_editorial = db.query(Heroe.nombre, Heroe.poder).filter(
                        Heroe.editorial == editorial
                    ).order_by(Heroe.poder.desc()).all()
                    
                    if heroes_editorial:
                        df_heroes = pd.DataFrame(heroes_editorial, columns=['Nombre', 'Poder'])
                        st.dataframe(df_heroes, use_container_width=True)
    else:
        st.warning("No hay editoriales registradas en la base de datos")

with tab4:
    st.subheader("Métricas de Ejecución ETL")
    
    # Verificar si existe la tabla MetricasETL
    try:
        metricas = db.query(MetricasETL).order_by(
            MetricasETL.fecha_ejecucion.desc()
        ).limit(20).all()
        
        if metricas:
            data = []
            for m in metricas:
                data.append({
                    'Fecha': m.fecha_ejecucion.strftime('%Y-%m-%d %H:%M'),
                    'Estado': m.estado,
                    'Extraídos': m.registros_extraidos,
                    'Guardados': m.registros_guardados,
                    'Fallidos': m.registros_fallidos,
                    'Tiempo (s)': f"{m.tiempo_ejecucion_segundos:.2f}"
                })
            
            df_metricas = pd.DataFrame(data)
            st.dataframe(df_metricas, use_container_width=True)
            
            # Gráficas de métricas
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.bar(df_metricas, x='Fecha', y='Guardados',
                            title='Registros Guardados por Ejecución',
                            color='Estado')
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.scatter(df_metricas, x='Fecha', y='Tiempo (s)',
                               size='Guardados', title='Duración de Ejecuciones',
                               color='Estado')
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("""
            ⚠️ **Módulo de Métricas en desarrollo**
            
            Para habilitar esta sección, necesitas:
            1. Actualizar el extractor para guardar métricas
            2. Modificar el script de extracción para registrar:
               - Tiempo de ejecución
               - Registros exitosos/fallidos
               - Estado del proceso
            
            Mientras tanto, puedes explorar los datos de superhéroes en las otras pestañas.
            """)
            
    except Exception as e:
        st.info("""
        ⚠️ **Módulo de Métricas no disponible**
        
        La tabla de métricas ETL aún no está configurada. 
        Disfruta del análisis de superhéroes en las otras pestañas.
        """)
    
    # Estadísticas adicionales
    st.subheader("📊 Estadísticas Generales de la Base de Datos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Distribución de héroes por alineación
        alineacion_counts = db.query(
            Heroe.alineacion, 
            func.count(Heroe.id).label('count')
        ).group_by(Heroe.alineacion).all()
        
        if alineacion_counts:
            df_alineacion = pd.DataFrame(alineacion_counts, columns=['Alineación', 'Cantidad'])
            fig = px.pie(df_alineacion, values='Cantidad', names='Alineación',
                        title='Distribución por Alineación')
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Distribución por género
        genero_counts = db.query(
            Heroe.genero, 
            func.count(Heroe.id).label('count')
        ).group_by(Heroe.genero).all()
        
        if genero_counts:
            df_genero = pd.DataFrame(genero_counts, columns=['Género', 'Cantidad'])
            fig = px.bar(df_genero, x='Género', y='Cantidad',
                        title='Distribución por Género',
                        color='Cantidad', color_continuous_scale='Viridis')
            st.plotly_chart(fig, use_container_width=True)

# Cerrar conexión
db.close()

# Footer
st.markdown("---")
st.markdown("🦸 Dashboard Avanzado de Superhéroes - Desarrollado con Streamlit y SQLAlchemy")