#!/usr/bin/env python3
"""
02_transformador.py
--------------------------------------------------
ETL - ETAPA TRANSFORM

- Lee superhéroes base desde data_raw.json
- Genera registros históricos de powerstats
- Produce exactamente N registros (ej. 1000)

NO consulta la BD
--------------------------------------------------
"""

import json
from datetime import datetime, timedelta, timezone
import random

# ==================================================
# LOGS INLINE
# ==================================================
def log_etapa(nombre):
    print("\n" + "=" * 60)
    print(f"🛠️  ETAPA: {nombre}")
    print("=" * 60)

def log_info(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ℹ️  {msg}")

def log_ok(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ {msg}")

# ==================================================
# TRANSFORM
# ==================================================
def transformar():
    log_etapa("TRANSFORM – Generación de histórico de powerstats")

    # -------------------------------
    # Lectura RAW
    # -------------------------------
    with open("data_raw.json", encoding="utf-8") as f:
        raw = json.load(f)

    superheroes = raw["superheroes"]
    total_historicos = raw["metadata"]["total_registros_historicos"]

    log_info(f"Superhéroes base: {len(superheroes)}")
    log_info(f"Registros históricos a generar: {total_historicos}")

    transformados = []

    inicio = datetime.now(timezone.utc)

    # -------------------------------
    # Generación del histórico
    # -------------------------------
    for i in range(total_historicos):
        hero = random.choice(superheroes)

        base = hero["stats"]

        registro = {
            "superhero": {
                "superhero_api_id": hero["superhero_api_id"],
                "nombre": hero["nombre"]
            },
            "apariencia": hero["apariencia"],
            "powerstats": [{
                "inteligencia": max(0, min(100, base["inteligencia"] + random.randint(-3, 3))),
                "fuerza": max(0, min(100, base["fuerza"] + random.randint(-3, 3))),
                "velocidad": max(0, min(100, base["velocidad"] + random.randint(-3, 3))),
                "durabilidad": max(0, min(100, base["durabilidad"] + random.randint(-3, 3))),
                "poder": max(0, min(100, base["poder"] + random.randint(-3, 3))),
                "combate": max(0, min(100, base["combate"] + random.randint(-3, 3))),
                "fecha_extraccion": (
                    inicio - timedelta(minutes=i * 10)
                ).isoformat()
            }]
        }

        transformados.append(registro)

        if (i + 1) % 200 == 0:
            log_info(f"{i + 1}/{total_historicos} registros históricos generados")

    # -------------------------------
    # Escritura
    # -------------------------------
    with open("data_transformada.json", "w", encoding="utf-8") as f:
        json.dump(transformados, f, indent=2)

    log_ok("Transformación completada")
    log_ok(f"Archivo generado: data_transformada.json")
    log_ok(f"Total registros generados: {len(transformados)}")

# ==================================================
# MAIN
# ==================================================
if __name__ == "__main__":
    transformar()