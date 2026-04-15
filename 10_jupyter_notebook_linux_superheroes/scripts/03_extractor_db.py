#!/usr/bin/env python3
"""
03_extractor_db.py
--------------------------------------------------
ETL - ETAPA LOAD

- Lee data_transformada.json
- Inserta SOLO powerstats como histórico
- Reutiliza superhéroes existentes
- Registra métricas ETL

NO consume APIs
NO transforma datos
--------------------------------------------------
"""

import sys
import os

# Asegurar acceso al paquete scripts
sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

import json
from datetime import datetime, timezone

from scripts.database import SessionLocal
from scripts.models import Superhero, PowerStats, Apariencia, MetricasETL

# ==================================================
# UTILIDADES DE LOG (INLINE)
# ==================================================
def log_etapa(nombre):
    print("\n" + "=" * 60)
    print(f"📦 ETAPA: {nombre}")
    print("=" * 60)

def log_info(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ℹ️  {msg}")

def log_ok(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ {msg}")

def log_warn(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️  {msg}")

# ==================================================
# LOAD
# ==================================================
def cargar_db():
    log_etapa("LOAD – Inserción de histórico en PostgreSQL")

    db = SessionLocal()

    insertados = 0
    omitidos = 0   # solo aplica a superhéroes nuevos
    fallidos = 0

    inicio = datetime.now(timezone.utc)

    try:
        # -------------------------------
        # Lectura de datos transformados
        # -------------------------------
        with open("data_transformada.json", encoding="utf-8") as f:
            data = json.load(f)

        total = len(data)
        log_info(f"Registros históricos a procesar: {total}")

        # -------------------------------
        # Inserción
        # -------------------------------
        for idx, item in enumerate(data, start=1):
            try:
                # -------- SUPERHÉROE --------
                hero = (
                    db.query(Superhero)
                    .filter_by(superhero_api_id=item["superhero"]["superhero_api_id"])
                    .first()
                )

                if not hero:
                    # Solo se crea si NO existe
                    hero = Superhero(
                        superhero_api_id=item["superhero"]["superhero_api_id"],
                        nombre=item["superhero"]["nombre"],
                        fecha_creacion=inicio,
                        activo=True
                    )
                    db.add(hero)
                    db.flush()

                    # Apariencia SOLO se crea una vez
                    apar = Apariencia(
                        superhero_id=hero.id,
                        **item["apariencia"]
                    )
                    db.add(apar)

                    omitidos += 1  # omitido como "nuevo héroe reutilizado"

                # -------- POWERSTATS (SIEMPRE) --------
                for stat in item["powerstats"]:
                    ps = PowerStats(
                        superhero_id=hero.id,
                        **{k: v for k, v in stat.items() if k != "fecha_extraccion"},
                        fecha_extraccion=datetime.fromisoformat(stat["fecha_extraccion"])
                    )
                    db.add(ps)

                insertados += 1

                if idx % 200 == 0:
                    log_info(f"{idx}/{total} registros históricos cargados")

            except Exception as e:
                db.rollback()
                fallidos += 1
                log_warn(f"Error en registro {idx}: {e}")

        db.commit()

        # -------------------------------
        # Métricas ETL
        # -------------------------------
        fin = datetime.now(timezone.utc)
        duracion = (fin - inicio).total_seconds()

        estado = "SUCCESS" if fallidos == 0 else "PARTIAL"

        metricas = MetricasETL(
            fecha_ejecucion=inicio,
            registros_extraidos=total,
            registros_guardados=insertados,
            registros_fallidos=fallidos,
            tiempo_ejecucion_segundos=duracion,
            estado=estado,
            mensaje=(
                f"PowerStats insertados: {insertados}, "
                f"Héroes reutilizados: {omitidos}, "
                f"Fallidos: {fallidos}"
            )
        )
        db.add(metricas)
        db.commit()

        # -------------------------------
        # Resumen final
        # -------------------------------
        log_ok("Carga completada correctamente")
        log_ok(f"PowerStats insertados: {insertados}")
        log_warn(f"Superhéroes reutilizados: {omitidos}")
        log_warn(f"Fallidos: {fallidos}")
        log_ok(f"Tiempo total: {duracion:.2f} segundos")
        log_ok(f"Estado ETL: {estado}")

    finally:
        db.close()

# ==================================================
# MAIN
# ==================================================
if __name__ == "__main__":
    cargar_db()