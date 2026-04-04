#!/usr/bin/env python3
"""
extractor_db.py
------------------------------------------------
Carga datos desde PostgreSQL LOCAL hacia
PostgreSQL en SUPABASE usando bulk insert.

NO consume API.
NO transforma datos.
------------------------------------------------
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from scripts.models import Ciudad, RegistroClima

# ---------------------------------------------
# Configuración BD LOCAL (desde .env)
# ---------------------------------------------
from scripts.database import SessionLocal as SessionLocalLocal

# ---------------------------------------------
# Configuración BD SUPABASE (hardcode solo aquí)
# ---------------------------------------------
SUPABASE_URL = (
    "postgresql+psycopg2://"
    "postgres.cwhrrhnunvrmbitxqveq:"
    "weatherstack_Etl_Corhuila@"
    "aws-1-us-east-1.pooler.supabase.com:6543/postgres"
)

engine_supabase = create_engine(
    SUPABASE_URL,
    connect_args={"sslmode": "require"}
)

SessionLocalSupabase = sessionmaker(bind=engine_supabase)

# ---------------------------------------------
# Transferencia
# ---------------------------------------------
def transferir_datos():
    db_local = SessionLocalLocal()
    db_supabase = SessionLocalSupabase()

    try:
        print("📥 Leyendo datos desde BD local...")

        ciudades_local = db_local.query(Ciudad).all()
        registros_local = db_local.query(RegistroClima).all()

        print(f"  Ciudades encontradas: {len(ciudades_local)}")
        print(f"  Registros clima encontrados: {len(registros_local)}")

        # -----------------------------
        # Insertar ciudades
        # -----------------------------
        ciudad_map = {}

        for c in ciudades_local:
            existe = (
                db_supabase.query(Ciudad)
                .filter_by(nombre=c.nombre)
                .first()
            )

            if not existe:
                nueva = Ciudad(
                    nombre=c.nombre,
                    pais=c.pais,
                    latitud=c.latitud,
                    longitud=c.longitud
                )
                db_supabase.add(nueva)
                db_supabase.flush()
                ciudad_map[c.id] = nueva.id
            else:
                ciudad_map[c.id] = existe.id

        db_supabase.commit()
        print("✅ Ciudades sincronizadas")

        # -----------------------------
        # Bulk insert registros clima
        # -----------------------------
        registros_supabase = []

        for r in registros_local:
            registros_supabase.append(
                RegistroClima(
                    ciudad_id=ciudad_map[r.ciudad_id],
                    temperatura=r.temperatura,
                    sensacion_termica=r.sensacion_termica,
                    humedad=r.humedad,
                    velocidad_viento=r.velocidad_viento,
                    descripcion=r.descripcion,
                    codigo_tiempo=r.codigo_tiempo,
                    fecha_extraccion=r.fecha_extraccion
                )
            )

        db_supabase.bulk_save_objects(registros_supabase)
        db_supabase.commit()

        print(f"✅ {len(registros_supabase)} registros cargados en Supabase")

    except Exception as e:
        db_supabase.rollback()
        print("❌ Error durante la carga:", e)

    finally:
        db_local.close()
        db_supabase.close()

# ---------------------------------------------
# MAIN
# ---------------------------------------------
if __name__ == "__main__":
    transferir_datos()