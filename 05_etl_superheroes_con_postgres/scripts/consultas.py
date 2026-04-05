#!/usr/bin/env python3
import sys
sys.path.insert(0, ".")

from sqlalchemy import func
import pandas as pd

from scripts.database import SessionLocal
from scripts.models import Superhero, PowerStats, Apariencia, MetricasETL

# Sesión de BD
db = SessionLocal()


# =========================================================
# Se implementaron consultas analíticas sobre PostgreSQL para 
# validar los datos cargados por el ETL y facilitar su uso en dashboards y análisis.
# CONSULTA 1: Ranking de poder promedio por superhéroe
# =========================================================
def ranking_poder_promedio():
    """
    Calcula el poder promedio de cada superhéroe
    (promedio de inteligencia, fuerza, velocidad, durabilidad, poder y combate)
    """
    registros = db.query(
        Superhero.nombre.label("Superhéroe"),
        func.avg(
            (
                PowerStats.inteligencia +
                PowerStats.fuerza +
                PowerStats.velocidad +
                PowerStats.durabilidad +
                PowerStats.poder +
                PowerStats.combate
            ) / 6.0
        ).label("Poder Promedio")
    ).join(PowerStats).group_by(Superhero.nombre).order_by(
        func.avg(
            (
                PowerStats.inteligencia +
                PowerStats.fuerza +
                PowerStats.velocidad +
                PowerStats.durabilidad +
                PowerStats.poder +
                PowerStats.combate
            ) / 6.0
        ).desc()
    ).limit(10).all()

    df = pd.DataFrame(registros, columns=["Superhéroe", "Poder Promedio"])

    print("\n🏆 TOP 10 SUPERHÉROES POR PODER PROMEDIO")
    print(df.to_string(index=False))


# =========================================================
# CONSULTA 2: Estadísticas promedio por editorial
# =========================================================
def poder_promedio_por_editorial():
    """
    Calcula el poder promedio por editorial (Marvel, DC, etc.)
    """
    registros = db.query(
        Superhero.editorial.label("Editorial"),
        func.avg(
            (
                PowerStats.inteligencia +
                PowerStats.fuerza +
                PowerStats.velocidad +
                PowerStats.durabilidad +
                PowerStats.poder +
                PowerStats.combate
            ) / 6.0
        ).label("Poder Promedio")
    ).join(PowerStats).group_by(
        Superhero.editorial
    ).order_by(
        func.avg(
            (
                PowerStats.inteligencia +
                PowerStats.fuerza +
                PowerStats.velocidad +
                PowerStats.durabilidad +
                PowerStats.poder +
                PowerStats.combate
            ) / 6.0
        ).desc()
    ).all()

    df = pd.DataFrame(registros, columns=["Editorial", "Poder Promedio"])

    print("\n📊 PODER PROMEDIO POR EDITORIAL")
    print(df.to_string(index=False))


# =========================================================
# CONSULTA 3: Superhéroe más fuerte (fuerza máxima)
# =========================================================
def superheroe_mas_fuerte():
    """
    Identifica el registro con mayor valor de fuerza
    """
    registro = db.query(
        Superhero.nombre,
        PowerStats.fuerza
    ).join(PowerStats).order_by(
        PowerStats.fuerza.desc()
    ).first()

    if registro:
        print(f"\n💪 SUPERHÉROE MÁS FUERTE: {registro.nombre} con fuerza {registro.fuerza}")


# =========================================================
# CONSULTA 4: Conteo de superhéroes por editorial
# =========================================================
def conteo_por_editorial():
    """
    Cuenta el número de superhéroes por editorial
    """
    registros = db.query(
        Superhero.editorial,
        func.count(Superhero.id).label("Cantidad")
    ).group_by(Superhero.editorial).order_by(
        func.count(Superhero.id).desc()
    ).all()

    df = pd.DataFrame(registros, columns=["Editorial", "Cantidad de Superhéroes"])

    print("\n📚 CANTIDAD DE SUPERHÉROES POR EDITORIAL")
    print(df.to_string(index=False))


# =========================================================
# CONSULTA 5: Últimas ejecuciones del ETL
# =========================================================
def metricas_etl():
    """
    Muestra las últimas ejecuciones del ETL
    """
    metricas = db.query(MetricasETL).order_by(
        MetricasETL.fecha_ejecucion.desc()
    ).limit(5).all()

    print("\n📈 ÚLTIMAS 5 EJECUCIONES DEL ETL")
    for m in metricas:
        print(
            f"  - {m.fecha_ejecucion}: {m.estado} "
            f"({m.registros_guardados} registros en "
            f"{m.tiempo_ejecucion_segundos:.2f}s)"
        )


# =========================================================
# MAIN
# =========================================================
if __name__ == "__main__":
    try:
        print("\n" + "=" * 60)
        print("ANÁLISIS DE DATOS - SUPERHEROES (POSTGRESQL)")
        print("=" * 60)

        ranking_poder_promedio()
        poder_promedio_por_editorial()
        superheroe_mas_fuerte()
        conteo_por_editorial()
        metricas_etl()

        print("\n" + "=" * 60 + "\n")

    finally:
        db.close()