#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
from datetime import datetime
from scripts.database import SessionLocal, init_db, engine
from scripts.models import Ciudad, RegistroClima, Base
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def populate_from_csv():
    """Poblar la base de datos desde el archivo clima.csv existente"""
    
    # Verificar que existe el archivo
    if not os.path.exists('data/clima.csv'):
        logger.error("❌ No se encuentra data/clima.csv. Ejecuta primero extractor.py")
        return False
    
    # Leer datos del CSV
    df = pd.read_csv('data/clima.csv')
    logger.info(f"📊 Datos leídos: {len(df)} registros")
    
    # Crear sesión
    db = SessionLocal()
    
    try:
        # Primero, crear las ciudades
        ciudades_dict = {}
        for _, row in df.iterrows():
            ciudad_nombre = row['ciudad']
            
            # Buscar o crear ciudad
            ciudad = db.query(Ciudad).filter(Ciudad.nombre == ciudad_nombre).first()
            if not ciudad:
                ciudad = Ciudad(
                    nombre=ciudad_nombre,
                    pais=row.get('pais', 'Colombia'),
                    latitud=row.get('latitud'),
                    longitud=row.get('longitud')
                )
                db.add(ciudad)
                db.flush()  # Para obtener el ID
                logger.info(f"🏙️ Ciudad creada: {ciudad_nombre}")
            
            ciudades_dict[ciudad_nombre] = ciudad
        
        db.commit()
        
        # Luego, crear los registros climáticos
        for _, row in df.iterrows():
            ciudad_nombre = row['ciudad']
            ciudad = ciudades_dict[ciudad_nombre]
            
            # Parsear fecha
            try:
                fecha = pd.to_datetime(row['fecha_extraccion']).to_pydatetime()
            except:
                fecha = datetime.now()
            
            # Crear registro
            registro = RegistroClima(
                ciudad_id=ciudad.id,
                temperatura=row['temperatura'],
                sensacion_termica=row['sensacion_termica'],
                humedad=row['humedad'],
                velocidad_viento=row['velocidad_viento'],
                descripcion=row['descripcion'],
                codigo_tiempo=row.get('codigo_tiempo', 0),
                fecha_extraccion=fecha
            )
            db.add(registro)
        
        db.commit()
        logger.info(f"✅ {len(df)} registros climáticos guardados en BD")
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
        # Contar registros
        total_ciudades = db.query(Ciudad).count()
        total_registros = db.query(RegistroClima).count()
        
        logger.info(f"📊 Verificación BD:")
        logger.info(f"   - Ciudades: {total_ciudades}")
        logger.info(f"   - Registros climáticos: {total_registros}")
        
        # Mostrar últimos registros
        ultimos = db.query(RegistroClima).order_by(RegistroClima.fecha_extraccion.desc()).limit(5).all()
        for r in ultimos:
            ciudad = db.query(Ciudad).filter(Ciudad.id == r.ciudad_id).first()
            logger.info(f"   → {ciudad.nombre}: {r.temperatura}°C, {r.fecha_extraccion}")
            
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