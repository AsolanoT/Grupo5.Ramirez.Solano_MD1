#!/usr/bin/env python3
"""
extractor_db_linux_to_docker.py
--------------------------------------------------
Migración de datos desde PostgreSQL en Linux (WSL)
hacia PostgreSQL en Docker.

- No consume API
- No transforma datos
- Migra ciudades, registros_clima y metricas_etl
--------------------------------------------------
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from scripts.models import Ciudad, RegistroClima, MetricasETL

# ==================================================
# CONFIGURACIÓN BD ORIGEN (LINUX / WSL)
# ==================================================
LINUX_DB_URL = (
    "postgresql+psycopg2://"
    "postgres:123456@"
    "localhost:5432/weatherstack_etl"
)

engine_linux = create_engine(LINUX_DB_URL)
SessionLinux = sessionmaker(bind=engine_linux)

# ==================================================
# CONFIGURACIÓN BD DESTINO (DOCKER)
# ==================================================
DOCKER_DB_URL = (
    "postgresql+psycopg2://"
    "postgres:123456@"
    "localhost:5435/weatherstack_etl"
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

        ciudades_linux = db_linux.query(Ciudad).all()
        registros_linux = db_linux.query(RegistroClima).all()
        metricas_linux = db_linux.query(MetricasETL).all()

        print(f"  Ciudades: {len(ciudades_linux)}")
        print(f"  Registros clima: {len(registros_linux)}")
        print(f"  Métricas ETL: {len(metricas_linux)}")

        # ----------------------------------------------
        # Migrar ciudades
        # ----------------------------------------------
        ciudad_id_map = {}

        for c in ciudades_linux:
            existente = (
                db_docker.query(Ciudad)
                .filter_by(nombre=c.nombre)
                .first()
            )

            if not existente:
                nueva = Ciudad(
                    nombre=c.nombre,
                    pais=c.pais,
                    latitud=c.latitud,
                    longitud=c.longitud,
                    activa=c.activa,
                    fecha_creacion=c.fecha_creacion
                )
                db_docker.add(nueva)
                db_docker.flush()
                ciudad_id_map[c.id] = nueva.id
            else:
                ciudad_id_map[c.id] = existente.id

        db_docker.commit()
        print("✅ Ciudades migradas")

        # ----------------------------------------------
        # Migrar registros de clima
        # ----------------------------------------------
        registros_docker = []

        for r in registros_linux:
            registros_docker.append(
                RegistroClima(
                    ciudad_id=ciudad_id_map[r.ciudad_id],
                    temperatura=r.temperatura,
                    sensacion_termica=r.sensacion_termica,
                    humedad=r.humedad,
                    velocidad_viento=r.velocidad_viento,
                    descripcion=r.descripcion,
                    codigo_tiempo=r.codigo_tiempo,
                    fecha_extraccion=r.fecha_extraccion,
                    fecha_creacion=r.fecha_creacion
                )
            )

        db_docker.bulk_save_objects(registros_docker)
        db_docker.commit()
        print(f"✅ {len(registros_docker)} registros_clima migrados")

        # ----------------------------------------------
        # Migrar métricas ETL
        # ----------------------------------------------
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
        print(f"✅ {len(metricas_docker)} métricas_etl migradas")

        print("🎉 Migración completada exitosamente")

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