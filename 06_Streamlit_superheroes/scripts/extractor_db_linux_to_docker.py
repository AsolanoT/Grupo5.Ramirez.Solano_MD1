#!/usr/bin/env python3
"""
extractor_db_linux_to_docker.py
--------------------------------------------------
Migración de datos desde PostgreSQL LOCAL (Linux / WSL)
hacia PostgreSQL en Docker (superheroes_etl).

- NO consume API
- NO transforma datos
- Migra:
    * superheroes
    * powerstats
    * apariencia
    * metricas_etl
--------------------------------------------------
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from scripts.models import (
    Superhero,
    PowerStats,
    Apariencia,
    MetricasETL
)

# ==================================================
# CONFIGURACIÓN BD ORIGEN (LINUX / WSL)
# ==================================================
LINUX_DB_URL = (
    "postgresql+psycopg2://"
    "postgres:123456@"
    "localhost:5432/superheroes_etl"
)

engine_linux = create_engine(LINUX_DB_URL)
SessionLinux = sessionmaker(bind=engine_linux)

# ==================================================
# CONFIGURACIÓN BD DESTINO (DOCKER)
# ==================================================
DOCKER_DB_URL = (
    "postgresql+psycopg2://"
    "postgres:123456@"
    "localhost:5435/superheroes_etl"
)

engine_docker = create_engine(DOCKER_DB_URL)
SessionDocker = sessionmaker(bind=engine_docker)

# ==================================================
# PROCESO DE MIGRACIÓN
# ==================================================
def migrar_datos():
    db_linux = SessionLinux()
    db_docker = SessionDocker()

    try:
        print("📥 Leyendo datos desde PostgreSQL Linux...")

        heroes_linux = db_linux.query(Superhero).all()
        stats_linux = db_linux.query(PowerStats).all()
        apariencias_linux = db_linux.query(Apariencia).all()
        metricas_linux = db_linux.query(MetricasETL).all()

        print(f"  Superhéroes: {len(heroes_linux)}")
        print(f"  PowerStats: {len(stats_linux)}")
        print(f"  Apariencias: {len(apariencias_linux)}")
        print(f"  Métricas ETL: {len(metricas_linux)}")

        # --------------------------------------------------
        # SUPERHEROES (con mapeo de IDs)
        # --------------------------------------------------
        superhero_id_map = {}

        for h in heroes_linux:
            existente = (
                db_docker.query(Superhero)
                .filter_by(superhero_api_id=h.superhero_api_id)
                .first()
            )

            if not existente:
                nuevo = Superhero(
                    superhero_api_id=h.superhero_api_id,
                    nombre=h.nombre,
                    nombre_real=h.nombre_real,
                    editorial=h.editorial,
                    alineacion=h.alineacion,
                    lugar_nacimiento=h.lugar_nacimiento,
                    primera_aparicion=h.primera_aparicion,
                    fecha_creacion=h.fecha_creacion,
                    activo=h.activo
                )
                db_docker.add(nuevo)
                db_docker.flush()
                superhero_id_map[h.id] = nuevo.id
            else:
                superhero_id_map[h.id] = existente.id

        db_docker.commit()
        print("✅ Superhéroes migrados")

        # --------------------------------------------------
        # APARIENCIA (1 a 1)
        # --------------------------------------------------
        apariencias_docker = []

        for a in apariencias_linux:
            apariencias_docker.append(
                Apariencia(
                    superhero_id=superhero_id_map[a.superhero_id],
                    genero=a.genero,
                    raza=a.raza,
                    altura=a.altura,
                    peso=a.peso,
                    color_ojos=a.color_ojos,
                    color_cabello=a.color_cabello,
                    fecha_creacion=a.fecha_creacion
                )
            )

        db_docker.bulk_save_objects(apariencias_docker)
        db_docker.commit()
        print(f"✅ {len(apariencias_docker)} apariencias migradas")

        # --------------------------------------------------
        # POWERSTATS (tabla de hechos)
        # --------------------------------------------------
        stats_docker = []

        for s in stats_linux:
            stats_docker.append(
                PowerStats(
                    superhero_id=superhero_id_map[s.superhero_id],
                    inteligencia=s.inteligencia,
                    fuerza=s.fuerza,
                    velocidad=s.velocidad,
                    durabilidad=s.durabilidad,
                    poder=s.poder,
                    combate=s.combate,
                    fecha_extraccion=s.fecha_extraccion,
                    fecha_creacion=s.fecha_creacion
                )
            )

        db_docker.bulk_save_objects(stats_docker)
        db_docker.commit()
        print(f"✅ {len(stats_docker)} powerstats migrados")

        # --------------------------------------------------
        # METRICAS ETL
        # --------------------------------------------------
        metricas_docker = []

        for m in metricas_linux:
            metricas_docker.append(
                MetricasETL(
                    fecha_ejecucion=m.fecha_ejecucion,
                    registros_extraidos=m.registros_extraidos,
                    registros_guardados=m.registros_guardados,
                    registros_fallidos=m.registros_fallidos,
                    tiempo_ejecucion_segundos=m.tiempo_ejecucion_segundos,
                    estado=m.estado,
                    mensaje=m.mensaje
                )
            )

        db_docker.bulk_save_objects(metricas_docker)
        db_docker.commit()
        print(f"✅ {len(metricas_docker)} métricas ETL migradas")

        print("🎉 Migración Linux → Docker completada exitosamente")

    except Exception as e:
        db_docker.rollback()
        print("❌ Error durante la migración:", e)

    finally:
        db_linux.close()
        db_docker.close()


# ==================================================
# MAIN
# ==================================================
if __name__ == "__main__":
    migrar_datos()