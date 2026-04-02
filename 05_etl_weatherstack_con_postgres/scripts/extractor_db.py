#!/usr/bin/env python3

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


import os as os_env
import requests
from datetime import datetime
import time
from dotenv import load_dotenv
import logging
from sqlalchemy.exc import IntegrityError

from scripts.database import SessionLocal
from scripts.models import Ciudad, RegistroClima, MetricasETL

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/etl.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class WeatherstackExtractor:
    def __init__(self):
        self.api_key = os.getenv('API_KEY')
        self.base_url = os.getenv('WEATHERSTACK_BASE_URL')
        self.ciudades = [c.strip() for c in os.getenv('CIUDADES').split(',')]

        self.db = SessionLocal()
        self.tiempo_inicio = time.time()
        self.registros_extraidos = 0
        self.registros_guardados = 0
        self.registros_fallidos = 0

        if not self.api_key:
            raise ValueError("API_KEY no configurada en .env")

    # =========================
    # EXTRACT
    # =========================
    def extraer_clima(self, ciudad):
        try:
            url = f"{self.base_url}/current"
            params = {
                'access_key': self.api_key,
                'query': ciudad
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if 'error' in data:
                logger.error(f"❌ Error API para {ciudad}: {data['error']['info']}")
                self.registros_fallidos += 1
                return None

            self.registros_extraidos += 1
            logger.info(f"✅ Datos extraídos para {ciudad}")
            return data

        except Exception as e:
            logger.error(f"❌ Error extrayendo {ciudad}: {e}")
            self.registros_fallidos += 1
            return None

    # =========================
    # TRANSFORM
    # =========================
    def procesar_respuesta(self, response_data):
        try:
            current = response_data.get('current', {})
            location = response_data.get('location', {})

            return {
                'ciudad': location.get('name'),
                'pais': location.get('country'),
                'latitud': location.get('lat'),
                'longitud': location.get('lon'),
                'temperatura': current.get('temperature'),
                'sensacion_termica': current.get('feelslike'),
                'humedad': current.get('humidity'),
                'velocidad_viento': current.get('wind_speed'),
                'descripcion': current.get('weather_descriptions', ['N/A'])[0],
                'codigo_tiempo': current.get('weather_code')
            }
        except Exception as e:
            logger.error(f"❌ Error transformando datos: {e}")
            return None

    # =========================
    # LOAD
    # =========================
    def guardar_en_bd(self, datos):
        try:
            # Buscar o crear ciudad
            ciudad = self.db.query(Ciudad).filter_by(
                nombre=datos['ciudad']
            ).first()

            if not ciudad:
                ciudad = Ciudad(
                    nombre=datos['ciudad'],
                    pais=datos['pais'],
                    latitud=datos['latitud'],
                    longitud=datos['longitud']
                )
                self.db.add(ciudad)
                self.db.flush()  # obtener ID sin commit

            # Crear registro de clima
            registro = RegistroClima(
                ciudad_id=ciudad.id,
                temperatura=datos['temperatura'],
                sensacion_termica=datos['sensacion_termica'],
                humedad=datos['humedad'],
                velocidad_viento=datos['velocidad_viento'],
                descripcion=datos['descripcion'],
                codigo_tiempo=datos['codigo_tiempo'],
                fecha_extraccion=datetime.utcnow()
            )

            self.db.add(registro)
            self.db.commit()

            self.registros_guardados += 1
            logger.info(f"🌡️ Registro guardado para {datos['ciudad']}")

        except IntegrityError as e:
            self.db.rollback()
            self.registros_fallidos += 1
            logger.error(f"❌ Error de integridad: {e}")

        except Exception as e:
            self.db.rollback()
            self.registros_fallidos += 1
            logger.error(f"❌ Error guardando datos: {e}")

    # =========================
    # MÉTRICAS
    # =========================
    def guardar_metricas(self, estado):
        try:
            tiempo_total = time.time() - self.tiempo_inicio

            metricas = MetricasETL(
                registros_extraidos=self.registros_extraidos,
                registros_guardados=self.registros_guardados,
                registros_fallidos=self.registros_fallidos,
                tiempo_ejecucion_segundos=tiempo_total,
                estado=estado,
                mensaje=f"Extraídos: {self.registros_extraidos}, Guardados: {self.registros_guardados}, Fallidos: {self.registros_fallidos}"
            )

            self.db.add(metricas)
            self.db.commit()
            logger.info("📊 Métricas ETL guardadas")

        except Exception as e:
            logger.error(f"❌ Error guardando métricas: {e}")

    # =========================
    # PIPELINE
    # =========================
    def ejecutar_extraccion(self):
        try:
            logger.info(f"🚀 Iniciando ETL para {len(self.ciudades)} ciudades")

            for ciudad in self.ciudades:
                response = self.extraer_clima(ciudad)
                if response:
                    datos = self.procesar_respuesta(response)
                    if datos:
                        self.guardar_en_bd(datos)

            estado = "SUCCESS" if self.registros_fallidos == 0 else "PARTIAL"
            self.guardar_metricas(estado)

            return estado == "SUCCESS"

        except Exception as e:
            logger.error(f"❌ Error general ETL: {e}")
            self.guardar_metricas("FAILED")
            return False

        finally:
            self.db.close()


if __name__ == "__main__":
    extractor = WeatherstackExtractor()
    exito = extractor.ejecutar_extraccion()
    exit(0 if exito else 1)