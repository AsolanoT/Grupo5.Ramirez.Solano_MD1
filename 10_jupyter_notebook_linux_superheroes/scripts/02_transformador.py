#!/usr/bin/env python3
"""
02_transformador.py
--------------------------------------------------
ETL - ETAPA TRANSFORM

- Lee superhéroes base desde data_raw.json
- Genera registros históricos de powerstats
- Mantiene coherencia estadística entre variables
- Poder se recalcula en función de otras variables

NO consulta la BD
--------------------------------------------------
"""

import json
from datetime import datetime, timedelta, timezone
import random
import numpy as np

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
# FUNCIONES AUXILIARES
# ==================================================
def limitar(valor):
    return max(0, min(100, int(valor)))

def calcular_poder(inteligencia, fuerza, velocidad, durabilidad, combate):
    ruido = np.random.normal(0, 5)

    poder = (
        0.30 * fuerza +
        0.25 * inteligencia +
        0.20 * velocidad +
        0.15 * durabilidad +
        0.10 * combate +
        ruido
    )

    return limitar(poder)

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

        # 🔹 Variación realista (más amplia)
        inteligencia = limitar(base["inteligencia"] + random.randint(-10, 10))
        fuerza = limitar(base["fuerza"] + random.randint(-10, 10))
        velocidad = limitar(base["velocidad"] + random.randint(-10, 10))
        durabilidad = limitar(base["durabilidad"] + random.randint(-10, 10))
        combate = limitar(base["combate"] + random.randint(-10, 10))

        # 🔑 Poder recalculado correctamente
        poder = calcular_poder(
            inteligencia,
            fuerza,
            velocidad,
            durabilidad,
            combate
        )

        registro = {
            "superhero": {
                "superhero_api_id": hero["superhero_api_id"],
                "nombre": hero["nombre"]
            },
            "apariencia": hero["apariencia"],
            "powerstats": [{
                "inteligencia": inteligencia,
                "fuerza": fuerza,
                "velocidad": velocidad,
                "durabilidad": durabilidad,
                "poder": poder,
                "combate": combate,
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