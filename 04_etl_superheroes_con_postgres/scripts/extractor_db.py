# Extractor que sirve para extraer datos de la API de Superhéroes y guardarlos en PostgreSQL
# - Consume la API de SuperheroAPI POR MEDIO DEL ID
# El extractor utiliza identificadores oficiales de la SuperheroAPI, garantizando consistencia, 
# eliminando ambigüedades y permitiendo una carga idempotente en PostgreSQL. 

#!/usr/bin/env python3
"""
extractor_db.py
--------------------------------------------------
ETL SuperheroAPI (OPCIÓN B - por ID)

- Consume SuperheroAPI usando IDs oficiales
- Extrae biography, powerstats y appearance
- Guarda datos normalizados en PostgreSQL
- Registra métricas del proceso ETL
--------------------------------------------------
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import requests
import time
from datetime import datetime, timezone
from dotenv import load_dotenv
import logging
from sqlalchemy.exc import IntegrityError

from scripts.database import SessionLocal
from scripts.models import Superhero, PowerStats, Apariencia, MetricasETL

# ==================================================
# CARGAR VARIABLES DE ENTORNO
# ==================================================
load_dotenv()

API_KEY = os.getenv("API_KEY")
BASE_URL = f"https://superheroapi.com/api/{API_KEY}"

HEROES = [
    int(h.strip())
    for h in os.getenv("HEROES", "").split(",")
    if h.strip().isdigit()
]

if not API_KEY:
    raise ValueError("❌ API_KEY no configurada en .env")

# ==================================================
# LOGGING
# ==================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/etl.log"),
        logging.StreamHandler()
    ],
)
logger = logging.getLogger(__name__)


# ==================================================
# CLASE EXTRACTOR
# ==================================================
class SuperheroExtractor:
    def __init__(self):
        self.db = SessionLocal()

        self.tiempo_inicio = time.time()
        self.registros_extraidos = 0
        self.registros_guardados = 0
        self.registros_fallidos = 0

    # --------------------------------------------------
    # EXTRACT: obtener héroe base por ID
    # --------------------------------------------------
    def obtener_heroe(self, hero_id):
        try:
            url = f"{BASE_URL}/{hero_id}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("response") != "success":
                logger.warning(f"⚠️ Héroe no encontrado con ID {hero_id}")
                self.registros_fallidos += 1
                return None

            self.registros_extraidos += 1
            return data

        except Exception as e:
            logger.error(f"❌ Error obteniendo héroe {hero_id}: {e}")
            self.registros_fallidos += 1
            return None

    # --------------------------------------------------
    # EXTRACT: endpoint específico
    # --------------------------------------------------
    def obtener_endpoint(self, hero_id, endpoint):
        try:
            url = f"{BASE_URL}/{hero_id}/{endpoint}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"❌ Error en {endpoint} para ID {hero_id}: {e}")
            return None

    # --------------------------------------------------
    # LOAD: guardar datos en PostgreSQL
    # --------------------------------------------------
    def guardar_en_bd(self, hero, biography, powerstats, appearance):
        try:
            # SUPERHERO
            superhero = (
                self.db.query(Superhero)
                .filter_by(superhero_api_id=int(hero["id"]))
                .first()
            )

            if not superhero:
                superhero = Superhero(
                    superhero_api_id=int(hero["id"]),
                    nombre=hero.get("name"),
                    nombre_real=biography.get("full-name"),
                    editorial=biography.get("publisher"),
                    alineacion=biography.get("alignment"),
                    lugar_nacimiento=biography.get("place-of-birth"),
                    primera_aparicion=biography.get("first-appearance"),
                )
                self.db.add(superhero)
                self.db.flush()

            # POWERSTATS (histórico)
            stats = PowerStats(
                superhero_id=superhero.id,
                inteligencia=self._to_int(powerstats.get("intelligence")),
                fuerza=self._to_int(powerstats.get("strength")),
                velocidad=self._to_int(powerstats.get("speed")),
                durabilidad=self._to_int(powerstats.get("durability")),
                poder=self._to_int(powerstats.get("power")),
                combate=self._to_int(powerstats.get("combat")),
                fecha_extraccion=datetime.now(timezone.utc),
            )
            self.db.add(stats)

            # APARIENCIA (idempotente)
            if appearance:
                existente = (
                    self.db.query(Apariencia)
                    .filter_by(superhero_id=superhero.id)
                    .first()
                )

                if not existente:
                    apar = Apariencia(
                        superhero_id=superhero.id,
                        genero=appearance.get("gender"),
                        raza=appearance.get("race"),
                        altura=",".join(appearance.get("height", [])),
                        peso=",".join(appearance.get("weight", [])),
                        color_ojos=appearance.get("eye-color"),
                        color_cabello=appearance.get("hair-color"),
                    )
                    self.db.add(apar)

            self.db.commit()
            self.registros_guardados += 1
            logger.info(f"✅ Datos guardados para {superhero.nombre}")

        except IntegrityError as e:
            self.db.rollback()
            self.registros_fallidos += 1
            logger.error(f"❌ Error de integridad: {e}")

        except Exception as e:
            self.db.rollback()
            self.registros_fallidos += 1
            logger.error(f"❌ Error guardando datos: {e}")

    # --------------------------------------------------
    # MÉTRICAS ETL
    # --------------------------------------------------
    def guardar_metricas(self, estado):
        try:
            tiempo_total = time.time() - self.tiempo_inicio

            metricas = MetricasETL(
                registros_extraidos=self.registros_extraidos,
                registros_guardados=self.registros_guardados,
                registros_fallidos=self.registros_fallidos,
                tiempo_ejecucion_segundos=tiempo_total,
                estado=estado,
                mensaje=(
                    f"Extraídos: {self.registros_extraidos}, "
                    f"Guardados: {self.registros_guardados}, "
                    f"Fallidos: {self.registros_fallidos}"
                ),
            )

            self.db.add(metricas)
            self.db.commit()
            logger.info("📊 Métricas ETL guardadas")

        except Exception as e:
            logger.error(f"❌ Error guardando métricas: {e}")

    # --------------------------------------------------
    # PIPELINE PRINCIPAL
    # --------------------------------------------------
    def ejecutar(self):
        try:
            logger.info(f"🚀 Iniciando ETL para {len(HEROES)} superhéroes (por ID)")

            for hero_id in HEROES:
                hero = self.obtener_heroe(hero_id)
                if not hero:
                    continue

                biography = self.obtener_endpoint(hero_id, "biography")
                powerstats = self.obtener_endpoint(hero_id, "powerstats")
                appearance = self.obtener_endpoint(hero_id, "appearance")

                if biography and powerstats:
                    self.guardar_en_bd(
                        hero,
                        biography,
                        powerstats,
                        appearance
                    )

            estado = "SUCCESS" if self.registros_fallidos == 0 else "PARTIAL"
            self.guardar_metricas(estado)
            return estado == "SUCCESS"

        except Exception as e:
            logger.error(f"❌ Error general del ETL: {e}")
            self.guardar_metricas("FAILED")
            return False

        finally:
            self.db.close()

    # --------------------------------------------------
    # UTILIDAD
    # --------------------------------------------------
    @staticmethod
    def _to_int(valor):
        try:
            return int(valor)
        except (TypeError, ValueError):
            return None


# ==================================================
# MAIN
# ==================================================
if __name__ == "__main__":
    extractor = SuperheroExtractor()
    success = extractor.ejecutar()
    exit(0 if success else 1)