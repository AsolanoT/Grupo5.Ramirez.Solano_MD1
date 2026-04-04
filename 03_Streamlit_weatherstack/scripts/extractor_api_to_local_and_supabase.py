#!/usr/bin/env python3
"""
extractor_api_to_local_and_supabase.py
--------------------------------------------------
ETL REAL:
- Extrae datos desde la API Weatherstack
- Los guarda en PostgreSQL LOCAL
- Los guarda en PostgreSQL SUPABASE
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
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from scripts.database import SessionLocal
from scripts.models import Ciudad, RegistroClima, MetricasETL

# ===============================
# CONFIGURACIÓN
# ===============================
load_dotenv()

API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("WEATHERSTACK_BASE_URL")
CIUDADES = [c.strip() for c in os.getenv("CIUDADES").split(",")]

if not API_KEY:
    raise ValueError("API_KEY no configurada en el entorno")

# -------------------------------
# SUPABASE
# -------------------------------
SUPABASE_URL = (
    "postgresql+psycopg2://"
    "postgres.cwhrrhnunvrmbitxqveq:"
    "weatherstack_Etl_Corhuila@"
    "aws-1-us-east-1.pooler.supabase.com:6543/postgres"
)

engine_supabase = create_engine(
    SUPABASE_URL,
    connect_args={"sslmode": "require"}
)
SessionSupabase = sessionmaker(bind=engine_supabase)

# -------------------------------
# LOGGING
# -------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/etl.log")
    ]
)
logger = logging.getLogger(__name__)

# ===============================
# CLASE ETL
# ===============================
class WeatherstackETL:

    def __init__(self):
        self.db_local = SessionLocal()
        self.db_supabase = SessionSupabase()

        # Métricas
        self.tiempo_inicio = time.time()
        self.registros_extraidos = 0
        self.registros_guardados = 0
        self.registros_fallidos = 0

    # ---------------------------
    # EXTRACT
    # ---------------------------
    def extraer(self, ciudad):
        try:
            response = requests.get(
                f"{BASE_URL}/current",
                params={
                    "access_key": API_KEY,
                    "query": ciudad
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            if "error" in data:
                self.registros_fallidos += 1
                logger.error(f"API error en {ciudad}: {data['error']['info']}")
                return None

            self.registros_extraidos += 1
            return data

        except Exception as e:
            self.registros_fallidos += 1
            logger.error(f"Error extrayendo {ciudad}: {e}")
            return None

    # ---------------------------
    # TRANSFORM
    # ---------------------------
    def transformar(self, data):
        current = data.get("current", {})
        location = data.get("location", {})

        return {
            "ciudad": location.get("name"),
            "pais": location.get("country"),
            "latitud": location.get("lat"),
            "longitud": location.get("lon"),
            "temperatura": current.get("temperature"),
            "sensacion_termica": current.get("feelslike"),
            "humedad": current.get("humidity"),
            "velocidad_viento": current.get("wind_speed"),
            "descripcion": current.get("weather_descriptions", ["N/A"])[0],
            "codigo_tiempo": current.get("weather_code"),
            "fecha": datetime.now(timezone.utc)
        }

    # ---------------------------
    # LOAD (LOCAL + SUPABASE)
    # ---------------------------
    def cargar(self, datos):
        # ---------- LOCAL ----------
        ciudad_local = (
            self.db_local.query(Ciudad)
            .filter_by(nombre=datos["ciudad"])
            .first()
        )

        if not ciudad_local:
            ciudad_local = Ciudad(
                nombre=datos["ciudad"],
                pais=datos["pais"],
                latitud=datos["latitud"],
                longitud=datos["longitud"]
            )
            self.db_local.add(ciudad_local)
            self.db_local.flush()

        registro_local = RegistroClima(
            ciudad_id=ciudad_local.id,
            temperatura=datos["temperatura"],
            sensacion_termica=datos["sensacion_termica"],
            humedad=datos["humedad"],
            velocidad_viento=datos["velocidad_viento"],
            descripcion=datos["descripcion"],
            codigo_tiempo=int(datos["codigo_tiempo"]),
            fecha_extraccion=datos["fecha"]
        )
        self.db_local.add(registro_local)

        # ---------- SUPABASE ----------
        ciudad_sb = (
            self.db_supabase.query(Ciudad)
            .filter_by(nombre=datos["ciudad"])
            .first()
        )

        if not ciudad_sb:
            ciudad_sb = Ciudad(
                nombre=datos["ciudad"],
                pais=datos["pais"],
                latitud=datos["latitud"],
                longitud=datos["longitud"]
            )
            self.db_supabase.add(ciudad_sb)
            self.db_supabase.flush()

        registro_sb = RegistroClima(
            ciudad_id=ciudad_sb.id,
            temperatura=datos["temperatura"],
            sensacion_termica=datos["sensacion_termica"],
            humedad=datos["humedad"],
            velocidad_viento=datos["velocidad_viento"],
            descripcion=datos["descripcion"],
            codigo_tiempo=int(datos["codigo_tiempo"]),
            fecha_extraccion=datos["fecha"]
        )
        self.db_supabase.add(registro_sb)

        self.registros_guardados += 1

    # ---------------------------
    # MÉTRICAS
    # ---------------------------
    def guardar_metricas(self, estado):
        tiempo_total = time.time() - self.tiempo_inicio

        # Métricas para BD LOCAL
        metricas_local = MetricasETL(
            fecha_ejecucion=datetime.now(timezone.utc),
            registros_extraidos=self.registros_extraidos,
            registros_guardados=self.registros_guardados,
            registros_fallidos=self.registros_fallidos,
            tiempo_ejecucion_segundos=tiempo_total,
            estado=estado,
            mensaje=(
                f"Extraídos: {self.registros_extraidos}, "
                f"Guardados: {self.registros_guardados}, "
                f"Fallidos: {self.registros_fallidos}"
            )
        )

        self.db_local.add(metricas_local)
        self.db_local.commit()

        # Métricas para SUPABASE (objeto nuevo)
        metricas_supabase = MetricasETL(
            fecha_ejecucion=metricas_local.fecha_ejecucion,
            registros_extraidos=metricas_local.registros_extraidos,
            registros_guardados=metricas_local.registros_guardados,
            registros_fallidos=metricas_local.registros_fallidos,
            tiempo_ejecucion_segundos=metricas_local.tiempo_ejecucion_segundos,
            estado=metricas_local.estado,
            mensaje=metricas_local.mensaje
        )

        self.db_supabase.add(metricas_supabase)
        self.db_supabase.commit()

    # ---------------------------
    # PIPELINE
    # ---------------------------
    def ejecutar(self):
        try:
            for ciudad in CIUDADES:
                raw = self.extraer(ciudad)
                if not raw:
                    continue

                datos = self.transformar(raw)
                self.cargar(datos)
                logger.info(f"Procesado: {ciudad}")

            self.db_local.commit()
            self.db_supabase.commit()

            estado = "SUCCESS" if self.registros_fallidos == 0 else "PARTIAL"
            self.guardar_metricas(estado)

            logger.info("✅ ETL completado (LOCAL + SUPABASE)")

        except Exception as e:
            self.db_local.rollback()
            self.db_supabase.rollback()
            self.guardar_metricas("FAILED")
            logger.error(f"❌ Error ETL: {e}")

        finally:
            self.db_local.close()
            self.db_supabase.close()


# ===============================
# MAIN
# ===============================
if __name__ == "__main__":
    etl = WeatherstackETL()
    etl.ejecutar()