#!/usr/bin/env python3
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
import sys
sys.path.insert(0, '.')

from scripts.database import SessionLocal
from scripts.models import Heroe, MetricasHeroe

st.set_page_config(
    page_title="Dashboard Interactivo Superhéroes",
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
        text-align: center;
    }
    .heroe-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🎛️ Dashboard Interactivo - Control Total de Superhéroes")
st.markdown("### Explora y analiza el universo de superhéroes con filtros dinámicos")

# Conectar a la base de datos
db = SessionLocal()

# Obtener datos para filtros
heroes = db.query(Heroe).all()

if heroes:
    # Preparar DataFrame base
    data = []
    for heroe in heroes:
        data.append({
            'ID': heroe.id,
            'Nombre': heroe.nombre,
            'Nombre Real': heroe.nombre_real or 'Desconocido',
            'Editorial': heroe.editorial or 'Desconocida',
            'Género': heroe.genero or 'Desconocido',
            'Raza': heroe.raza or 'Desconocida',
            'Alineación': heroe.alineacion or 'Desconocida',
            'Inteligencia': heroe.inteligencia or 0,
            'Fuerza': heroe.fuerza or 0,
            'Velocidad': heroe.velocidad or 0,
            'Durabilidad': heroe.durabilidad or 0,
            'Poder': heroe.poder or 0,
            'Combate': heroe.combate or 0,
            'Poder Total': sum([
                heroe.inteligencia or 0,
                heroe.fuerza or 0,
                heroe.velocidad or 0,
                heroe.durabilidad or 0,
                heroe.poder or 0,
                heroe.combate or 0
            ]),
            'Lugar Nacimiento': heroe.lugar_nacimiento or 'Desconocido',
            'Primera Aparición': heroe.primera_aparicion or 'Desconocida'
        })
    
    df = pd.DataFrame(data)
    
    # ============================================
    # SIDEBAR - CONTROLES INTERACTIVOS
    # ============================================
    st.sidebar.markdown("## 🔧 Controles Interactivos")
    st.sidebar.markdown("---")
    
    # Filtro 1: Búsqueda por nombre
    st.sidebar.markdown("### 🔍 Búsqueda")
    busqueda = st.sidebar.text_input("Buscar héroe por nombre:", "")
    
    # Filtro 2: Editorial
    st.sidebar.markdown("### 🏢 Editorial")
    editoriales = ['Todas'] + sorted(df['Editorial'].unique().tolist())
    editorial_seleccionada = st.sidebar.selectbox("Seleccionar editorial:", editoriales)
    
    # Filtro 3: Alineación
    st.sidebar.markdown("### ⚖️ Alineación")
    alineaciones = ['Todas'] + sorted(df['Alineación'].unique().tolist())
    alineacion_seleccionada = st.sidebar.selectbox("Seleccionar alineación:", alineaciones)
    
    # Filtro 4: Género
    st.sidebar.markdown("### ⚥ Género")
    generos = ['Todos'] + sorted(df['Género'].unique().tolist())
    genero_seleccionado = st.sidebar.selectbox("Seleccionar género:", generos)
    
    # Filtro 5: Rango de poder
    st.sidebar.markdown("### ⚡ Rango de Poder")
    poder_min = st.sidebar.slider(
        "Poder mínimo:",
        min_value=int(df['Poder'].min()),
        max_value=int(df['Poder'].max()),
        value=int(df['Poder'].min())
    )
    poder_max = st.sidebar.slider(
        "Poder máximo:",
        min_value=int(df['Poder'].min()),
        max_value=int(df['Poder'].max()),
        value=int(df['Poder'].max())
    )
    
    # Filtro 6: Powerstats específicos
    st.sidebar.markdown("### 📊 Powerstats Mínimos")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        min_inteligencia = st.number_input("Inteligencia mín:", 0, 100, 0)
        min_fuerza = st.number_input("Fuerza mín:", 0, 100, 0)
        min_velocidad = st.number_input("Velocidad mín:", 0, 100, 0)
    with col2:
        min_durabilidad = st.number_input("Durabilidad mín:", 0, 100, 0)
        min_poder = st.number_input("Poder mín:", 0, 100, 0)
        min_combate = st.number_input("Combate mín:", 0, 100, 0)
    
    # Botón para aplicar filtros
    st.sidebar.markdown("---")
    aplicar_filtros = st.sidebar.button("🎯 Aplicar Filtros", type="primary")
    
    # ============================================
    # APLICAR FILTROS
    # ============================================
    df_filtrado = df.copy()
    
    # Aplicar filtro de búsqueda
    if busqueda:
        df_filtrado = df_filtrado[
            df_filtrado['Nombre'].str.contains(busqueda, case=False) |
            df_filtrado['Nombre Real'].str.contains(busqueda, case=False)
        ]
    
    # Aplicar filtro de editorial
    if editorial_seleccionada != 'Todas':
        df_filtrado = df_filtrado[df_filtrado['Editorial'] == editorial_seleccionada]
    
    # Aplicar filtro de alineación
    if alineacion_seleccionada != 'Todas':
        df_filtrado = df_filtrado[df_filtrado['Alineación'] == alineacion_seleccionada]
    
    # Aplicar filtro de género
    if genero_seleccionado != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['Género'] == genero_seleccionado]
    
    # Aplicar filtro de rango de poder
    df_filtrado = df_filtrado[
        (df_filtrado['Poder'] >= poder_min) & 
        (df_filtrado['Poder'] <= poder_max)
    ]
    
    # Aplicar filtros de powerstats mínimos
    df_filtrado = df_filtrado[
        (df_filtrado['Inteligencia'] >= min_inteligencia) &
        (df_filtrado['Fuerza'] >= min_fuerza) &
        (df_filtrado['Velocidad'] >= min_velocidad) &
        (df_filtrado['Durabilidad'] >= min_durabilidad) &
        (df_filtrado['Poder'] >= min_poder) &
        (df_filtrado['Combate'] >= min_combate)
    ]
    
    # ============================================
    # MÉTRICAS PRINCIPALES
    # ============================================
    st.markdown("## 📊 Panel de Control")
    
    # KPIs en columnas
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown('<div class="metric-box">', unsafe_allow_html=True)
        st.metric(
            "🦸 Total Héroes",
            f"{len(df_filtrado)}",
            delta=f"{len(df_filtrado) - len(df)} vs total"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-box">', unsafe_allow_html=True)
        poder_promedio = df_filtrado['Poder'].mean()
        st.metric(
            "⚡ Poder Promedio",
            f"{poder_promedio:.1f}"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-box">', unsafe_allow_html=True)
        heroe_top = df_filtrado.loc[df_filtrado['Poder'].idxmax()]['Nombre']
        poder_top = df_filtrado['Poder'].max()
        st.metric(
            "🏆 Héroe más poderoso",
            heroe_top,
            delta=f"Poder: {poder_top}"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="metric-box">', unsafe_allow_html=True)
        editoriales_unicas = df_filtrado['Editorial'].nunique()
        st.metric(
            "🏢 Editoriales",
            editoriales_unicas
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col5:
        st.markdown('<div class="metric-box">', unsafe_allow_html=True)
        poder_total = df_filtrado['Poder Total'].sum()
        st.metric(
            "💪 Poder Total",
            f"{poder_total:,.0f}"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ============================================
    # VISUALIZACIONES INTERACTIVAS
    # ============================================
    
    # PRIMERA FILA: Gráficas comparativas
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📈 Distribución de Poder por Editorial")
        fig = px.box(
            df_filtrado,
            x='Editorial',
            y='Poder',
            color='Editorial',
            title='Rango de Poder por Editorial',
            points="all"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 🎯 Top Powerstats Promedio")
        powerstats_prom = {
            'Inteligencia': df_filtrado['Inteligencia'].mean(),
            'Fuerza': df_filtrado['Fuerza'].mean(),
            'Velocidad': df_filtrado['Velocidad'].mean(),
            'Durabilidad': df_filtrado['Durabilidad'].mean(),
            'Poder': df_filtrado['Poder'].mean(),
            'Combate': df_filtrado['Combate'].mean()
        }
        df_prom = pd.DataFrame(list(powerstats_prom.items()), columns=['Powerstat', 'Valor'])
        
        fig = px.bar(
            df_prom,
            x='Powerstat',
            y='Valor',
            color='Valor',
            color_continuous_scale='Viridis',
            title='Promedio de Powerstats'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # SEGUNDA FILA: Gráficas de composición
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🥧 Composición por Alineación")
        alineacion_counts = df_filtrado['Alineación'].value_counts().reset_index()
        alineacion_counts.columns = ['Alineación', 'Cantidad']
        
        fig = px.pie(
            alineacion_counts,
            values='Cantidad',
            names='Alineación',
            title='Distribución de Héroes por Alineación',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 📊 Heatmap de Powerstats")
        # Seleccionar solo columnas numéricas para el heatmap
        powerstats_cols = ['Inteligencia', 'Fuerza', 'Velocidad', 'Durabilidad', 'Poder', 'Combate']
        df_heatmap = df_filtrado[powerstats_cols].corr()
        
        fig = px.imshow(
            df_heatmap,
            text_auto=True,
            aspect="auto",
            color_continuous_scale='RdBu_r',
            title='Correlación entre Powerstats'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # TERCERA FILA: Análisis detallado
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Top 10 Héroes más Poderosos")
        top_10 = df_filtrado.nlargest(10, 'Poder')[['Nombre', 'Editorial', 'Poder', 'Poder Total']]
        
        fig = px.bar(
            top_10,
            x='Nombre',
            y='Poder',
            color='Editorial',
            title='Top 10 por Nivel de Poder',
            text='Poder'
        )
        fig.update_traces(texttemplate='%{text}', textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 📊 Comparativa Interactiva")
        
        # Selectores para ejes
        eje_x = st.selectbox("Eje X:", powerstats_cols, index=0)
        eje_y = st.selectbox("Eje Y:", powerstats_cols, index=4)
        
        fig = px.scatter(
            df_filtrado,
            x=eje_x,
            y=eje_y,
            color='Editorial',
            size='Poder',
            hover_data=['Nombre', 'Alineación'],
            title=f'{eje_x} vs {eje_y}'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # ============================================
    # TABLA INTERACTIVA Y DESCARGA
    # ============================================
    st.markdown("## 📋 Explorador de Datos")
    
    # Opciones de visualización
    col1, col2, col3 = st.columns(3)
    
    with col1:
        mostrar_todos = st.checkbox("Mostrar todos los registros", value=False)
    
    with col2:
        columnas_mostrar = st.multiselect(
            "Columnas a mostrar:",
            df_filtrado.columns.tolist(),
            default=['Nombre', 'Editorial', 'Alineación', 'Poder', 'Fuerza', 'Velocidad']
        )
    
    with col3:
        ordenar_por = st.selectbox(
            "Ordenar por:",
            ['Poder', 'Nombre', 'Editorial', 'Fuerza', 'Velocidad'],
            index=0
        )
    
    # Mostrar tabla
    if columnas_mostrar:
        df_display = df_filtrado[columnas_mostrar].sort_values(ordenar_por, ascending=False)
        
        if mostrar_todos:
            st.dataframe(df_display, use_container_width=True, height=600)
        else:
            st.dataframe(df_display.head(50), use_container_width=True, height=400)
        
        # Estadísticas de la tabla
        st.markdown(f"**Mostrando {len(df_display)} de {len(df_filtrado)} héroes**")
    
    # Botones de descarga
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        csv = df_filtrado.to_csv(index=False)
        st.download_button(
            label="⬇️ Descargar datos filtrados (CSV)",
            data=csv,
            file_name=f"superheroes_filtrados_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        # Resumen estadístico
        resumen = df_filtrado[powerstats_cols].describe()
        csv_resumen = resumen.to_csv()
        st.download_button(
            label="📊 Descargar resumen estadístico",
            data=csv_resumen,
            file_name=f"resumen_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col3:
        # Top 10
        top_10_full = df_filtrado.nlargest(10, 'Poder')[['Nombre', 'Editorial', 'Poder'] + powerstats_cols]
        csv_top10 = top_10_full.to_csv(index=False)
        st.download_button(
            label="🏆 Descargar Top 10",
            data=csv_top10,
            file_name=f"top10_superheroes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )

else:
    st.warning("⚠️ No hay datos disponibles. Por favor, ejecuta primero el script populate_db.py")

# Cerrar conexión
db.close()

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; padding: 10px;'>
        🎛️ Dashboard Interactivo de Superhéroes - Filtros dinámicos y visualizaciones en tiempo real<br>
        Desarrollado con Streamlit, Plotly y SQLAlchemy
    </div>
    """,
    unsafe_allow_html=True
)