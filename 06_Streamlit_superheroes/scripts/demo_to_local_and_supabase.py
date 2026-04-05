#!/usr/bin/env python3
"""
demo_to_local_and_supabase.py
--------------------------------------------------
Genera EXACTAMENTE 100 powerstats sintéticos
y los guarda tanto en:

1. PostgreSQL LOCAL
2. PostgreSQL SUPABASE

NO consume API
NO depende del ETL real
DEMO DATA para Streamlit / Supabase
--------------------------------------------------
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from scripts.database import SessionLocal
from scripts.models import Superhero, PowerStats, Apariencia

# =========================================================
# CONFIG SUPABASE (CAMBIA SOLO EL PASSWORD)
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

SessionSupabase = sessionmaker(bind=engine_supabase)

# =========================================================
# CONFIG DEMO
# =========================================================
rng = np.random.default_rng(seed=42)
TOTAL_REGISTROS = 100

SUPERHEROES_DEMO = [
    ("Superman", "DC Comics"),
    ("Batman", "DC Comics"),
    ("Wonder Woman", "DC Comics"),
    ("Flash", "DC Comics"),
    ("Aquaman", "DC Comics"),
    ("Iron Man", "Marvel Comics"),
    ("Spider-Man", "Marvel Comics"),
    ("Hulk", "Marvel Comics"),
    ("Thor", "Marvel Comics"),
    ("Captain America", "Marvel Comics"),
]

# =========================================================
# PROCESO PRINCIPAL
# =========================================================
def generar_y_guardar():
    db_local = SessionLocal()
    db_supabase = SessionSupabase()

    try:
        print("🚀 Generando DEMO DATA de Superheroes (100 registros)")

        hero_map_local = {}
        hero_map_supabase = {}

        # -------------------------------------------------
        # CREAR SUPERHÉROES EN AMBAS BD
        # -------------------------------------------------
        for nombre, editorial in SUPERHEROES_DEMO:

            # ---------- LOCAL
            hero_local = db_local.query(Superhero).filter_by(nombre=nombre).first()
            if not hero_local:
                hero_local = Superhero(
                    superhero_api_id=int(rng.integers(10000, 99999)),
                    nombre=nombre,
                    editorial=editorial,
                    activo=True
                )
                db_local.add(hero_local)
                db_local.flush()

                db_local.add(
                    Apariencia(
                        superhero_id=hero_local.id,
                        genero="Male",
                        raza="Humano",
                        altura="1.80 m",
                        peso="85 kg",
                        color_ojos="Azul",
                        color_cabello="Negro"
                    )
                )

            hero_map_local[nombre] = hero_local.id

            # ---------- SUPABASE
            hero_sb = db_supabase.query(Superhero).filter_by(nombre=nombre).first()
            if not hero_sb:
                hero_sb = Superhero(
                    superhero_api_id=hero_local.superhero_api_id,
                    nombre=nombre,
                    editorial=editorial,
                    activo=True
                )
                db_supabase.add(hero_sb)
                db_supabase.flush()

                db_supabase.add(
                    Apariencia(
                        superhero_id=hero_sb.id,
                        genero="Male",
                        raza="Humano",
                        altura="1.80 m",
                        peso="85 kg",
                        color_ojos="Azul",
                        color_cabello="Negro"
                    )
                )

            hero_map_supabase[nombre] = hero_sb.id

        db_local.commit()
        db_supabase.commit()
        print("✅ Superhéroes DEMO creados en LOCAL y SUPABASE")

        # -------------------------------------------------
        # GENERAR POWERSTATS
        # -------------------------------------------------
        stats_local = []
        stats_supabase = []

        fecha = datetime.now(timezone.utc) - timedelta(days=5)
        registros_por_hero = TOTAL_REGISTROS // len(SUPERHEROES_DEMO)

        for nombre, _ in SUPERHEROES_DEMO:
            for _ in range(registros_por_hero):
                base_stats = dict(
                    inteligencia=int(rng.integers(20, 100)),
                    fuerza=int(rng.integers(20, 100)),
                    velocidad=int(rng.integers(20, 100)),
                    durabilidad=int(rng.integers(20, 100)),
                    poder=int(rng.integers(20, 100)),
                    combate=int(rng.integers(20, 100)),
                    fecha_extraccion=fecha
                )

                stats_local.append(
                    PowerStats(
                        superhero_id=hero_map_local[nombre],
                        **base_stats
                    )
                )

                stats_supabase.append(
                    PowerStats(
                        superhero_id=hero_map_supabase[nombre],
                        **base_stats
                    )
                )

                fecha += timedelta(minutes=30)

        # -------------------------------------------------
        # BULK INSERT
        # -------------------------------------------------
        db_local.bulk_save_objects(stats_local)
        db_supabase.bulk_save_objects(stats_supabase)

        db_local.commit()
        db_supabase.commit()

        print(f"✅ {len(stats_local)} registros DEMO insertados en LOCAL y SUPABASE")
        print("🎉 DEMO DATA COMPLETADA CON ÉXITO")

    except Exception as e:
        db_local.rollback()
        db_supabase.rollback()
        print("❌ Error en DEMO DATA:", e)

    finally:
        db_local.close()
        db_supabase.close()


# =========================================================
# MAIN
# =========================================================
if __name__ == "__main__":
    generar_y_guardar()