#!/usr/bin/env python3
"""
extractor_db_supabase.py
--------------------------------------------------
Migración de datos desde PostgreSQL LOCAL
hacia PostgreSQL en SUPABASE.

- NO consume API
- NO transforma datos
- Sincroniza tablas:
    - superheroes
    - powerstats
    - apariencia
    - metricas_etl
--------------------------------------------------
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from scripts.database import SessionLocal as SessionLocalLocal
from scripts.models import (
    Superhero,
    PowerStats,
    Apariencia,
    MetricasETL
)

# =========================================================
# CONFIGURACIÓN BD SUPABASE
# =========================================================
SUPABASE_URL = (
    "postgresql+psycopg2://"
    "postgres.gynzdwivsthccemknwsm:"
    "superheroes_Etl_Corhuila@"
    "aws-1-us-east-1.pooler.supabase.com:6543/postgres"
)

engine_supabase = create_engine(
    SUPABASE_URL,
    connect_args={"sslmode": "require"}
)

SessionLocalSupabase = sessionmaker(bind=engine_supabase)

# =========================================================
# TRANSFERENCIA DE DATOS
# =========================================================
def transferir_datos():
    db_local = SessionLocalLocal()
    db_supabase = SessionLocalSupabase()

    try:
        print("📥 Leyendo datos desde PostgreSQL LOCAL...")

        heroes_local = db_local.query(Superhero).all()
        stats_local = db_local.query(PowerStats).all()
        apariencias_local = db_local.query(Apariencia).all()
        metricas_local = db_local.query(MetricasETL).all()

        print(f"  Superhéroes: {len(heroes_local)}")
        print(f"  PowerStats: {len(stats_local)}")
        print(f"  Apariencias: {len(apariencias_local)}")
        print(f"  Métricas ETL: {len(metricas_local)}")

        # -------------------------------------------------
        # SUPERHEROES (lookup + map id)
        # -------------------------------------------------
        superhero_map = {}

        for h in heroes_local:
            existe = (
                db_supabase.query(Superhero)
                .filter_by(superhero_api_id=h.superhero_api_id)
                .first()
            )

            if not existe:
                nuevo = Superhero(
                    superhero_api_id=h.superhero_api_id,
                    nombre=h.nombre,
                    nombre_real=h.nombre_real,
                    editorial=h.editorial,
                    alineacion=h.alineacion,
                    lugar_nacimiento=h.lugar_nacimiento,
                    primera_aparicion=h.primera_aparicion,
                    activo=h.activo
                )
                db_supabase.add(nuevo)
                db_supabase.flush()
                superhero_map[h.id] = nuevo.id
            else:
                superhero_map[h.id] = existe.id

        db_supabase.commit()
        print("✅ Superhéroes sincronizados")

        # -------------------------------------------------
        # POWERSTATS (bulk insert)
        # -------------------------------------------------
        powerstats_supabase = [
            PowerStats(
                superhero_id=superhero_map[s.superhero_id],
                inteligencia=s.inteligencia,
                fuerza=s.fuerza,
                velocidad=s.velocidad,
                durabilidad=s.durabilidad,
                poder=s.poder,
                combate=s.combate,
                fecha_extraccion=s.fecha_extraccion,
                fecha_creacion=s.fecha_creacion
            )
            for s in stats_local
        ]

        db_supabase.bulk_save_objects(powerstats_supabase)
        db_supabase.commit()
        print(f"✅ {len(powerstats_supabase)} powerstats cargados")

        # -------------------------------------------------
        # APARIENCIA
        # -------------------------------------------------
        apariencias_supabase = [
            Apariencia(
                superhero_id=superhero_map[a.superhero_id],
                genero=a.genero,
                raza=a.raza,
                altura=a.altura,
                peso=a.peso,
                color_ojos=a.color_ojos,
                color_cabello=a.color_cabello,
                fecha_creacion=a.fecha_creacion
            )
            for a in apariencias_local
        ]

        db_supabase.bulk_save_objects(apariencias_supabase)
        db_supabase.commit()
        print(f"✅ {len(apariencias_supabase)} apariencias cargadas")

        # -------------------------------------------------
        # METRICAS ETL
        # -------------------------------------------------
        metricas_supabase = [
            MetricasETL(
                fecha_ejecucion=m.fecha_ejecucion,
                registros_extraidos=m.registros_extraidos,
                registros_guardados=m.registros_guardados,
                registros_fallidos=m.registros_fallidos,
                tiempo_ejecucion_segundos=m.tiempo_ejecucion_segundos,
                estado=m.estado,
                mensaje=m.mensaje
            )
            for m in metricas_local
        ]

        db_supabase.bulk_save_objects(metricas_supabase)
        db_supabase.commit()
        print(f"✅ {len(metricas_supabase)} métricas ETL cargadas")

        print("🎉 Migración a Supabase completada exitosamente")

    except Exception as e:
        db_supabase.rollback()
        print("❌ Error durante la migración:", e)

    finally:
        db_local.close()
        db_supabase.close()


# =========================================================
# MAIN
# =========================================================
if __name__ == "__main__":
    transferir_datos()