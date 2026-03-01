#!/usr/bin/env python3
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys
sys.path.insert(0, '.')

from scripts.database import SessionLocal
from scripts.models import Heroe, MetricasHeroe

# Configuración de la página
st.set_page_config(
    page_title="Dashboard de Superhéroes",
    page_icon="🦸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título principal
st.title("🦸 Dashboard de Superhéroes - API SuperHero")
st.markdown("---")

# Conectar a la base de datos
db = SessionLocal()

try:
    # Obtener todos los héroes
    heroes = db.query(Heroe).all()
    
    # Crear DataFrame
    data = []
    for heroe in heroes:
        data.append({
            'ID': heroe.id,
            'Nombre': heroe.nombre,
            'Editorial': heroe.editorial or 'Desconocida',
            'Inteligencia': heroe.inteligencia or 0,
            'Fuerza': heroe.fuerza or 0,
            'Velocidad': heroe.velocidad or 0,
            'Durabilidad': heroe.durabilidad or 0,
            'Poder': heroe.poder or 0,
            'Combate': heroe.combate or 0,
            'Género': heroe.genero or 'Desconocido',
            'Raza': heroe.raza or 'Desconocida',
            'Alineación': heroe.alineacion or 'Desconocida'
        })
    
    df = pd.DataFrame(data)
    
    # Sidebar con filtros
    st.sidebar.title("🔧 Filtros")
    
    editoriales = ['Todas'] + list(df['Editorial'].unique())
    editorial_seleccionada = st.sidebar.selectbox("Editorial:", editoriales)
    
    if editorial_seleccionada != 'Todas':
        df_filtrado = df[df['Editorial'] == editorial_seleccionada]
    else:
        df_filtrado = df
    
    # Métricas principales
    st.subheader("📊 Estadísticas Generales")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🦸 Total Héroes", len(df_filtrado))
    
    with col2:
        poder_promedio = df_filtrado['Poder'].mean()
        st.metric("⚡ Poder Promedio", f"{poder_promedio:.1f}")
    
    with col3:
        heroe_mas_fuerte = df_filtrado.loc[df_filtrado['Poder'].idxmax()]
        st.metric("💪 Más Fuerte", heroe_mas_fuerte['Nombre'], 
                 f"Poder: {heroe_mas_fuerte['Poder']}")
    
    with col4:
        editoriales_count = df_filtrado['Editorial'].nunique()
        st.metric("🏢 Editoriales", editoriales_count)
    
    st.markdown("---")
    
    # Gráficas
    st.subheader("📈 Análisis de Powerstats")
    
    # Gráfico de barras de powerstats promedio por editorial
    powerstats = ['Inteligencia', 'Fuerza', 'Velocidad', 'Durabilidad', 'Poder', 'Combate']
    
    if not df_filtrado.empty:
        df_stats = df_filtrado.groupby('Editorial')[powerstats].mean().reset_index()
        
        fig = go.Figure()
        for stat in powerstats:
            fig.add_trace(go.Bar(
                name=stat,
                x=df_stats['Editorial'],
                y=df_stats[stat],
                text=df_stats[stat].round(1),
                textposition='auto',
            ))
        
        fig.update_layout(
            title="Powerstats Promedio por Editorial",
            xaxis_title="Editorial",
            yaxis_title="Valor Promedio",
            barmode='group',
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Dos columnas para gráficas adicionales
        col1, col2 = st.columns(2)
        
        with col1:
            # Top 10 héroes más poderosos
            top_10 = df_filtrado.nlargest(10, 'Poder')[['Nombre', 'Poder', 'Editorial']]
            fig_top = px.bar(
                top_10,
                x='Nombre',
                y='Poder',
                color='Editorial',
                title="Top 10 Héroes más Poderosos",
                labels={'Poder': 'Nivel de Poder'}
            )
            st.plotly_chart(fig_top, use_container_width=True)
        
        with col2:
            # Distribución por alineación
            if 'Alineación' in df_filtrado.columns:
                alignment_counts = df_filtrado['Alineación'].value_counts()
                fig_pie = px.pie(
                    values=alignment_counts.values,
                    names=alignment_counts.index,
                    title="Distribución por Alineación"
                )
                st.plotly_chart(fig_pie, use_container_width=True)
        
        st.markdown("---")
        
        # Análisis de poder por género
        st.subheader("⚥ Análisis por Género")
        
        if 'Género' in df_filtrado.columns:
            gender_stats = df_filtrado.groupby('Género')[powerstats].mean().round(1)
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig_radar = go.Figure()
                
                for genero in gender_stats.index:
                    if genero != 'Desconocido' and genero != '-':
                        fig_radar.add_trace(go.Scatterpolar(
                            r=gender_stats.loc[genero].values,
                            theta=powerstats,
                            fill='toself',
                            name=genero
                        ))
                
                fig_radar.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, 100]
                        )),
                    showlegend=True,
                    title="Powerstats por Género"
                )
                
                st.plotly_chart(fig_radar, use_container_width=True)
            
            with col2:
                st.dataframe(gender_stats, use_container_width=True)
        
        st.markdown("---")
        
        # Tabla detallada
        st.subheader("📋 Lista Completa de Héroes")
        
        # Selector de columnas a mostrar
        columnas_default = ['Nombre', 'Editorial', 'Poder', 'Fuerza', 'Velocidad', 'Alineación']
        columnas_disponibles = df_filtrado.columns.tolist()
        
        columnas_mostrar = st.multiselect(
            "Selecciona columnas a mostrar:",
            columnas_disponibles,
            default=[col for col in columnas_default if col in columnas_disponibles]
        )
        
        if columnas_mostrar:
            st.dataframe(
                df_filtrado[columnas_mostrar].sort_values('Poder', ascending=False),
                use_container_width=True,
                height=500
            )
        
        # Descargar datos
        csv = df_filtrado.to_csv(index=False)
        st.download_button(
            label="📥 Descargar datos como CSV",
            data=csv,
            file_name=f"superheroes_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
        
    else:
        st.warning("No hay datos para mostrar con los filtros seleccionados")

finally:
    db.close()