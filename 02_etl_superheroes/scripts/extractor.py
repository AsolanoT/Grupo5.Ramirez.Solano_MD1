#!/usr/bin/env python3
import os
import requests
import json
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/etl.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class SuperheroExtractor:
    def __init__(self):
        self.token = os.getenv("API_TOKEN")
        self.base_url = os.getenv("BASE_URL")
        self.heroes = os.getenv("HEROES").split(",")

        if not self.token:
            raise ValueError("API_TOKEN no configurado")

    def extraer_heroe(self, hero_id):
        try:
            url = f"{self.base_url}/{self.token}/{hero_id}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data.get("response") == "error":
                logger.error(f"Error API: {data.get('error')}")
                return None

            logger.info(f"Heroe {data.get('name')} extraído correctamente")
            return data

        except Exception as e:
            logger.error(f"Error extrayendo héroe {hero_id}: {str(e)}")
            return None

    def transformar(self, data):
        try:
            return {
                "nombre": data.get("name"),
                "inteligencia": data["powerstats"].get("intelligence"),
                "fuerza": data["powerstats"].get("strength"),
                "velocidad": data["powerstats"].get("speed"),
                "durabilidad": data["powerstats"].get("durability"),
                "poder": data["powerstats"].get("power"),
                "combate": data["powerstats"].get("combat"),
                "editorial": data["biography"].get("publisher"),
                "fecha_extraccion": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error transformando datos: {str(e)}")
            return None

    def ejecutar(self):
        datos = []

        logger.info("Iniciando extracción de superhéroes...")

        for hero_id in self.heroes:
            raw = self.extraer_heroe(hero_id.strip())
            if raw:
                transformado = self.transformar(raw)
                if transformado:
                    datos.append(transformado)

        return datos


if __name__ == "__main__":
    extractor = SuperheroExtractor()
    datos = extractor.ejecutar()

    with open("data/superheroes_raw.json", "w") as f:
        json.dump(datos, f, indent=2)

    df = pd.DataFrame(datos)
    df.to_csv("data/superheroes.csv", index=False)

    print("\nEXTRACCIÓN COMPLETADA\n")
    print(df)