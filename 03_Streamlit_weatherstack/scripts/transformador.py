#!/usr/bin/env python3
"""
transformador.py
----------------------------------------
Transforma datos de clima almacenados en
PostgreSQL para análisis y visualización.

Realiza:
- Limpieza básica
- Categorización climática
----------------------------------------
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
from scripts.database import SessionLocal
from scripts.models import RegistroClima, Ciudad

def categorizar_temperatura(temp):
    if temp < 18:
        return "Fría"
    elif 18 <= temp < 26:
        return "Templada"
    else:
        return "Caliente"

def categorizar_humedad(h):
    if h < 50:
        return "Baja"
    elif 50 <= h < 75:
        return "Media"
    else:
        return "Alta"

def transformar_datos():
    db = SessionLocal()

    query = (
        db.query(
            Ciudad.nombre,
            RegistroClima.temperatura,
            RegistroClima.humedad,
            RegistroClima.velocidad_viento,
            RegistroClima.fecha_extraccion
        )
        .join(Ciudad)
        .all()
    )

    df = pd.DataFrame(
        query,
        columns=["Ciudad", "Temperatura", "Humedad", "Viento", "Fecha"]
    )

    # Transformaciones
    df["Categoria_Temperatura"] = df["Temperatura"].apply(categorizar_temperatura)
    df["Categoria_Humedad"] = df["Humedad"].apply(categorizar_humedad)

    print("✅ Transformación completada")
    print(df.head())

    db.close()

if __name__ == "__main__":
    transformar_datos()