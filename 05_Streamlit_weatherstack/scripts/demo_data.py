#!/usr/bin/env python3
"""
demo_data.py
--------------------------------------------------
Genera ~1000 registros sintéticos de clima con
variación horaria.

Simula lecturas cada ~30 minutos durante ~8 días
para 5 ciudades colombianas.

NO consume la API Weatherstack.
Inserta los datos directamente en PostgreSQL.
--------------------------------------------------
"""
import sys
import os

# Agrega la raíz del proyecto al PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError

from scripts.database import SessionLocal
from scripts.models import Ciudad, RegistroClima

# Semilla para reproducibilidad
random = np.random.default_rng(seed=42)

# -------------------------------
# Configuración de ciudades base
# -------------------------------
CIUDADES = [
    {
        "ciudad": "Bogotá",
        "pais": "Colombia",
        "latitud": 4.711,
        "longitud": -74.0721,
        "temp_base": 14,
        "humedad_base": 80,
        "viento_base": 15,
    },
    {
        "ciudad": "Medellín",
        "pais": "Colombia",
        "latitud": 6.2442,
        "longitud": -75.5812,
        "temp_base": 22,
        "humedad_base": 68,
        "viento_base": 10,
    },
    {
        "ciudad": "Cali",
        "pais": "Colombia",
        "latitud": 3.4516,
        "longitud": -76.5320,
        "temp_base": 26,
        "humedad_base": 70,
        "viento_base": 12,
    },
    {
        "ciudad": "Barranquilla",
        "pais": "Colombia",
        "latitud": 10.9685,
        "longitud": -74.7813,
        "temp_base": 29,
        "humedad_base": 75,
        "viento_base": 18,
    },
    {
        "ciudad": "Cartagena",
        "pais": "Colombia",
        "latitud": 10.3910,
        "longitud": -75.4794,
        "temp_base": 30,
        "humedad_base": 78,
        "viento_base": 20,
    },
]

DESCRIPCIONES = [
    "Despejado",
    "Parcialmente nublado",
    "Nublado",
    "Lluvia ligera",
    "Tormenta"
]

# -------------------------------
# Generación de datos
# -------------------------------
def generar_datos():
    db = SessionLocal()

    try:
        from datetime import timezone

        TOTAL_REGISTROS = 1000
        REGISTROS_POR_CIUDAD = TOTAL_REGISTROS // len(CIUDADES)

        inicio = datetime.now(timezone.utc) - timedelta(days=8)
        total_registros = 0

        for c in CIUDADES:
            # Crear o recuperar ciudad
            ciudad = (
                db.query(Ciudad)
                .filter_by(nombre=c["ciudad"])
                .first()
            )

            if not ciudad:
                ciudad = Ciudad(
                    nombre=c["ciudad"],
                    pais=c["pais"],
                    latitud=c["latitud"],
                    longitud=c["longitud"]
                )
                db.add(ciudad)
                db.commit()
                db.refresh(ciudad)

            fecha = inicio

            for _ in range(REGISTROS_POR_CIUDAD):
                if total_registros >= TOTAL_REGISTROS:
                    break

                temperatura = c["temp_base"] + random.normal(0, 2)
                humedad = min(100, max(40, c["humedad_base"] + random.normal(0, 5)))
                viento = max(0, c["viento_base"] + random.normal(0, 3))
                descripcion = random.choice(DESCRIPCIONES)

                registro = RegistroClima(
                    ciudad_id=ciudad.id,
                    temperatura=round(temperatura, 1),
                    sensacion_termica=round(temperatura + random.normal(0, 1), 1),
                    humedad=round(humedad, 1),
                    velocidad_viento=round(viento, 1),
                    descripcion=descripcion,
                    codigo_tiempo=int(random.integers(100, 900)),
                    fecha_extraccion=fecha
                )

                db.add(registro)
                fecha += timedelta(minutes=30)
                total_registros += 1

        db.commit()
        print(f"✅ Datos sintéticos generados correctamente: {total_registros} registros")

    except IntegrityError as e:
        db.rollback()
        print("❌ Error de integridad:", e)

    except Exception as e:
        db.rollback()
        print("❌ Error generando datos:", e)

    finally:
        db.close()


# -------------------------------
# EJECUCIÓN
# -------------------------------
if __name__ == "__main__":
    generar_datos()
