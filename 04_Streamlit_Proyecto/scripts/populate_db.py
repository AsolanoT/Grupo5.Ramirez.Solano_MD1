#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import json
import math
from datetime import datetime
from scripts.database import SessionLocal, init_db
from scripts.models import Heroe, Aparicion, Trabajo, Conexion, MetricasHeroe
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_value(value):
    """Convierte valores nan a None para que PostgreSQL los maneje como NULL"""
    if isinstance(value, float) and math.isnan(value):
        return None
    return value

def populate_from_csv():
    """Poblar la base de datos desde el archivo superheroes.csv"""
    
    # Verificar que existe el archivo
    if not os.path.exists('data/superheroes.csv'):
        logger.error("❌ No se encuentra data/superheroes.csv. Ejecuta primero extractor.py")
        return False
    
    # Leer datos del CSV
    df = pd.read_csv('data/superheroes.csv')
    logger.info(f"📊 Datos leídos: {len(df)} registros")
    
    # Leer datos raw para información adicional y IDs
    raw_data = []
    if os.path.exists('data/superheroes_raw.json'):
        with open('data/superheroes_raw.json', 'r') as f:
            raw_data = json.load(f)
        logger.info(f"📁 Datos raw cargados: {len(raw_data)} registros")
    
    # Crear diccionario de datos raw por nombre
    raw_dict = {}
    id_dict = {}
    for item in raw_data:
        if 'nombre' in item:
            raw_dict[item['nombre']] = item
            if 'id' in item:
                id_dict[item['nombre']] = int(item['id'])
    
    # Crear sesión
    db = SessionLocal()
    
    try:
        # Limpiar datos existentes
        logger.info("🧹 Limpiando datos existentes...")
        db.query(MetricasHeroe).delete()
        db.query(Aparicion).delete()
        db.query(Trabajo).delete()
        db.query(Conexion).delete()
        db.query(Heroe).delete()
        db.commit()
        logger.info("✅ Datos anteriores eliminados")
        
        # Insertar héroes
        heroes_creados = 0
        for _, row in df.iterrows():
            nombre_heroe = row['nombre']
            
            # Obtener ID de la API desde los datos raw
            heroe_id_api = id_dict.get(nombre_heroe, 0)
            
            if heroe_id_api == 0:
                heroe_id_api = -heroes_creados - 1
                logger.warning(f"⚠️ No se encontró ID para {nombre_heroe}, usando ID temporal: {heroe_id_api}")
            
            # Buscar datos raw adicionales
            raw_info = raw_dict.get(nombre_heroe, {})
            
            # Limpiar valores numéricos (convertir nan a None)
            inteligencia = clean_value(row.get('inteligencia'))
            fuerza = clean_value(row.get('fuerza'))
            velocidad = clean_value(row.get('velocidad'))
            durabilidad = clean_value(row.get('durabilidad'))
            poder = clean_value(row.get('poder'))
            combate = clean_value(row.get('combate'))
            
            # Crear héroe
            heroe = Heroe(
                heroe_id_api=heroe_id_api,
                nombre=nombre_heroe,
                inteligencia=inteligencia,
                fuerza=fuerza,
                velocidad=velocidad,
                durabilidad=durabilidad,
                poder=poder,
                combate=combate,
                editorial=clean_value(row.get('editorial')),
                fecha_creacion=datetime.now()
            )
            
            # Añadir más campos si están disponibles en raw_info
            if raw_info:
                # Biography
                biography = raw_info.get('biography', {})
                heroe.nombre_real = clean_value(biography.get('full-name', ''))
                heroe.alineacion = clean_value(biography.get('alignment', ''))
                heroe.lugar_nacimiento = clean_value(biography.get('place-of-birth', ''))
                heroe.primera_aparicion = clean_value(biography.get('first-appearance', ''))
                
                # Appearance
                appearance = raw_info.get('appearance', {})
                if appearance:
                    heroe.genero = clean_value(appearance.get('gender', ''))
                    heroe.raza = clean_value(appearance.get('race', ''))
                    if appearance.get('height') and len(appearance['height']) > 1:
                        heroe.altura = clean_value(appearance['height'][1])
                    if appearance.get('weight') and len(appearance['weight']) > 1:
                        heroe.peso = clean_value(appearance['weight'][1])
                    heroe.color_ojos = clean_value(appearance.get('eye-color', ''))
                    heroe.color_pelo = clean_value(appearance.get('hair-color', ''))
                
                # Images
                images = raw_info.get('images', {})
                if images:
                    heroe.imagen_url = clean_value(images.get('url', ''))
                    heroe.imagen_xs = clean_value(images.get('xs', ''))
                    heroe.imagen_sm = clean_value(images.get('sm', ''))
                    heroe.imagen_md = clean_value(images.get('md', ''))
                    heroe.imagen_lg = clean_value(images.get('lg', ''))
            
            db.add(heroe)
            db.flush()
            heroes_creados += 1
            
            # Crear relaciones si hay datos raw
            if raw_info:
                # Work
                work = raw_info.get('work', {})
                if work:
                    trabajo = Trabajo(
                        heroe_id=heroe.id,
                        ocupacion=clean_value(work.get('occupation', '')),
                        base=clean_value(work.get('base', ''))
                    )
                    db.add(trabajo)
                
                # Connections
                connections = raw_info.get('connections', {})
                if connections:
                    conexion = Conexion(
                        heroe_id=heroe.id,
                        grupo_afiliacion=clean_value(connections.get('group-affiliation', '')),
                        familiares=clean_value(connections.get('relatives', ''))
                    )
                    db.add(conexion)
            
            # Crear métrica inicial (solo si hay al menos un valor numérico)
            valores_numericos = [v for v in [inteligencia, fuerza, velocidad, durabilidad, poder, combate] 
                               if v is not None]
            
            if valores_numericos:
                poder_total = sum(valores_numericos)
                poder_promedio = poder_total / len(valores_numericos)
            else:
                poder_total = 0
                poder_promedio = 0
            
            metrica = MetricasHeroe(
                heroe_id=heroe.id,
                poder_total=poder_total,
                poder_promedio=poder_promedio
            )
            db.add(metrica)
            
            logger.info(f"✅ Héroe creado: {heroe.nombre} (ID API: {heroe.heroe_id_api})")
        
        db.commit()
        logger.info(f"✅ {heroes_creados} héroes guardados en BD")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error poblando BD: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def verificar_datos():
    """Verificar que los datos se cargaron correctamente"""
    db = SessionLocal()
    try:
        total_heroes = db.query(Heroe).count()
        total_metricas = db.query(MetricasHeroe).count()
        
        logger.info(f"📊 Verificación BD:")
        logger.info(f"   - Héroes: {total_heroes}")
        logger.info(f"   - Métricas: {total_metricas}")
        
        # Mostrar top 5 héroes por poder
        top_heroes = db.query(Heroe).order_by(Heroe.poder.desc()).limit(5).all()
        logger.info("🏆 Top 5 Héroes por Poder:")
        for h in top_heroes:
            logger.info(f"   → {h.nombre}: {h.poder}")
            
    finally:
        db.close()

if __name__ == "__main__":
    # Inicializar BD (crear tablas)
    logger.info("🚀 Inicializando base de datos...")
    init_db()
    
    # Poblar datos
    logger.info("📦 Poblando base de datos...")
    if populate_from_csv():
        logger.info("✅ Base de datos poblada exitosamente")
        verificar_datos()
    else:
        logger.error("❌ Error poblando base de datos")