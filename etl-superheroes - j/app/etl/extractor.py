import os
import requests
import logging
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime

# Cargar variables
load_dotenv()

# Crear carpetas si no existen
os.makedirs("logs", exist_ok=True)
os.makedirs("data/raw", exist_ok=True)

# Configurar logging
logging.basicConfig(
    filename="logs/etl.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

class SuperheroExtractor:

    def __init__(self):
        self.token = os.getenv("API_TOKEN")
        self.base_url = os.getenv("BASE_URL")

        if not self.token:
            raise ValueError("API_TOKEN no configurado")

    def get_hero(self, hero_id):
        url = f"{self.base_url}/{self.token}/{hero_id}"

        try:
            response = requests.get(url, timeout=10)

            if response.status_code != 200:
                logger.warning(f"Status {response.status_code} para ID {hero_id}")
                return None

            data = response.json()

            if data.get("response") == "error":
                logger.warning(f"Error API para ID {hero_id}")
                return None

            logger.info(f"Héroe {hero_id} extraído correctamente")
            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"Error conexión ID {hero_id}: {str(e)}")
            return None

    def run(self, start=1, end=50):
        heroes = []

        for hero_id in range(start, end + 1):
            hero = self.get_hero(hero_id)
            if hero:
                heroes.append(hero)

        return heroes


if __name__ == "__main__":

    extractor = SuperheroExtractor()
    data = extractor.run(1, 100)

    if data:
        df = pd.json_normalize(data)

        file_path = f"data/raw/superheroes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(file_path, index=False)

        logger.info(f"Datos guardados en {file_path}")
        print(f"✅ Extracción completada: {len(data)} héroes guardados")
    else:
        print("❌ No se extrajeron datos")
