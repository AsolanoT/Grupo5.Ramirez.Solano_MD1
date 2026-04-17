#!/usr/bin/env python3
"""
01_demo_data.py (VERSIÓN MEJORADA)

- Genera datos artificiales con relaciones reales
- Poder depende de otras variables
- Mantiene estructura ETL
"""

import json
import numpy as np
from datetime import datetime

# ==================================================
# LOGGING SIMPLE
# ==================================================
def log_etapa(nombre):
    print("\n" + "=" * 60)
    print(f"🚀 ETAPA: {nombre}")
    print("=" * 60)

def log_info(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ℹ️  {msg}")

def log_ok(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ {msg}")

# ==================================================
# CONFIGURACIÓN
# ==================================================
rng = np.random.default_rng(seed=42)

TOTAL_REGISTROS_HISTORICOS = 3000  # Número total de registros históricos a generar (1000 por héroe)

SUPERHEROES_BASE = [
    {"superhero_api_id": 152, "nombre": "Captain Cold"},
    {"superhero_api_id": 153, "nombre": "Captain Epic"},
    {"superhero_api_id": 154, "nombre": "Captain Hindsight"},
    {"superhero_api_id": 155, "nombre": "Captain Mar-vell"},
    {"superhero_api_id": 156, "nombre": "Captain Marvel"},
    {"superhero_api_id": 157, "nombre": "Captain Marvel"},
    {"superhero_api_id": 158, "nombre": "Captain Marvel II"},
    {"superhero_api_id": 159, "nombre": "Captain Midnight"},
    {"superhero_api_id": 79655, "nombre": "Wonder Woman"},
    {"superhero_api_id": 68910, "nombre": "Flash"},
    {"superhero_api_id": 49498, "nombre": "Iron Man"},
    {"superhero_api_id": 48970, "nombre": "Spider-Man"},
    {"superhero_api_id": 87272, "nombre": "Hulk"},
    {"superhero_api_id": 17735, "nombre": "Thor"},
]

# ==================================================
# GENERACIÓN DE STATS CON RELACIÓN REAL
# ==================================================
def generar_stats_base():
    inteligencia = rng.integers(50, 95)
    fuerza = rng.integers(50, 95)
    velocidad = rng.integers(50, 95)
    durabilidad = rng.integers(50, 95)
    combate = rng.integers(50, 95)

    # 🔑 Poder ahora depende de otras variables
    ruido = rng.normal(0, 5)

    poder = (
        0.30 * fuerza +
        0.25 * inteligencia +
        0.20 * velocidad +
        0.15 * durabilidad +
        0.10 * combate +
        ruido
    )

    # Limitar a rango realista
    poder = int(np.clip(poder, 50, 100))

    return {
        "inteligencia": int(inteligencia),
        "fuerza": int(fuerza),
        "velocidad": int(velocidad),
        "durabilidad": int(durabilidad),
        "poder": poder,
        "combate": int(combate),
    }

# ==================================================
# EXTRACT
# ==================================================
def generar_data():
    log_etapa("EXTRACT – Superhéroes base + datos coherentes")

    log_info(f"Superhéroes base: {len(SUPERHEROES_BASE)}")
    log_info(f"Registros históricos objetivo: {TOTAL_REGISTROS_HISTORICOS}")

    heroes = []

    for hero in SUPERHEROES_BASE:
        heroes.append({
            "superhero_api_id": hero["superhero_api_id"],
            "nombre": hero["nombre"],
            "stats": generar_stats_base(),
            "apariencia": {
                "genero": rng.choice(["Male", "Female"]),
                "raza": rng.choice(["Human", "Mutant", "Alien"]),
                "altura": f"{rng.integers(165, 210)} cm",
                "peso": f"{rng.integers(60, 150)} kg"
            }
        })

    payload = {
        "metadata": {
            "generado_en": datetime.now().isoformat(),
            "total_registros_historicos": TOTAL_REGISTROS_HISTORICOS
        },
        "superheroes": heroes
    }

    with open("data_raw.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    log_ok("Data cruda generada correctamente")
    log_ok("Archivo: data_raw.json")

# ==================================================
# MAIN
# ==================================================
if __name__ == "__main__":
    generar_data()