# Este código define una función que prueba la conexión a una base de datos PostgreSQL,
# intentando ejecutar una consulta simple y registrando el resultado para verificar si la conexión es exitosa.
"""
Prueba la conexión a la base de datos.

Esta función intenta establecer una conexión con la base de datos utilizando el motor configurado,
ejecuta una consulta simple (SELECT 1) para verificar la conectividad, y registra un mensaje de éxito
o error en el logger. Si la conexión falla, captura la excepción y registra el error.

Returns:
    bool: True si la conexión es exitosa y la consulta se ejecuta sin problemas, False en caso de error.
"""
#!/usr/bin/env python3
import os
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

logger = logging.getLogger(__name__)

# Configuración de la conexión
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Motor SQLAlchemy
engine = create_engine(DATABASE_URL, echo=False)

# Base para modelos ORM
Base = declarative_base()

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Metadata
metadata = MetaData()

def get_db():
    """Obtiene una sesión de base de datos"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_connection():
    """Prueba la conexión a la base de datos"""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("✅ Conexión a PostgreSQL exitosa")
        return True
    except Exception as e:
        logger.error(f"❌ Error conectando a PostgreSQL: {e}")
        return False

def create_all_tables():
    """Crea todas las tablas definidas en los modelos"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Tablas creadas exitosamente")
    except Exception as e:
        logger.error(f"❌ Error creando tablas: {e}")