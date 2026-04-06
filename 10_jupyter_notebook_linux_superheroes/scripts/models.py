#!/usr/bin/env python3
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Boolean,
    ForeignKey,
    Index
)
from sqlalchemy.orm import relationship
from scripts.database import Base


# =========================================================
# TABLA 1: SUPERHEROES
# =========================================================
class Superhero(Base):
    """
    Modelo para información general del superhéroe
    (datos estáticos / identidad)
    """
    __tablename__ = "superheroes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    superhero_api_id = Column(Integer, unique=True, nullable=False, index=True)

    nombre = Column(String(150), nullable=False, index=True)
    nombre_real = Column(String(200), nullable=True)
    editorial = Column(String(100), nullable=True)
    alineacion = Column(String(50), nullable=True)

    lugar_nacimiento = Column(String(255), nullable=True)
    primera_aparicion = Column(String(200), nullable=True)

    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    activo = Column(Boolean, default=True)

    # Relaciones
    powerstats = relationship(
        "PowerStats",
        back_populates="superhero",
        cascade="all, delete-orphan"
    )

    apariencia = relationship(
        "Apariencia",
        back_populates="superhero",
        uselist=False,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Superhero(nombre={self.nombre}, editorial={self.editorial})>"


# =========================================================
# TABLA 2: POWERSTATS
# =========================================================
class PowerStats(Base):
    """
    Modelo para estadísticas de poder del superhéroe
    (datos cuantitativos / hechos)
    """
    __tablename__ = "powerstats"

    id = Column(Integer, primary_key=True, autoincrement=True)

    superhero_id = Column(
        Integer,
        ForeignKey("superheroes.id"),
        nullable=False,
        index=True
    )

    inteligencia = Column(Integer, nullable=True)
    fuerza = Column(Integer, nullable=True)
    velocidad = Column(Integer, nullable=True)
    durabilidad = Column(Integer, nullable=True)
    poder = Column(Integer, nullable=True)
    combate = Column(Integer, nullable=True)

    fecha_extraccion = Column(DateTime, default=datetime.utcnow, index=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    # Relación
    superhero = relationship("Superhero", back_populates="powerstats")

    # Índices para análisis y búsquedas
    __table_args__ = (
        Index("idx_powerstats_hero_fecha", "superhero_id", "fecha_extraccion"),
    )

    def __repr__(self):
        return f"<PowerStats(superhero_id={self.superhero_id})>"


# =========================================================
# TABLA 3: METRICAS ETL
# =========================================================
class MetricasETL(Base):
    """
    Modelo para registrar métricas de ejecución del ETL
    """
    __tablename__ = "metricas_etl"

    id = Column(Integer, primary_key=True, autoincrement=True)

    fecha_ejecucion = Column(DateTime, default=datetime.utcnow, index=True)
    registros_extraidos = Column(Integer, nullable=False)
    registros_guardados = Column(Integer, nullable=False)
    registros_fallidos = Column(Integer, default=0)

    tiempo_ejecucion_segundos = Column(Float, nullable=False)
    estado = Column(String(50), nullable=False)  # SUCCESS, PARTIAL, FAILED
    mensaje = Column(String(500), nullable=True)

    def __repr__(self):
        return f"<MetricasETL(estado={self.estado}, registros_guardados={self.registros_guardados})>"


# =========================================================
# TABLA 4 (OPCIONAL): APARIENCIA
# =========================================================
class Apariencia(Base):
    """
    Modelo para características físicas del superhéroe
    """
    __tablename__ = "apariencia"

    id = Column(Integer, primary_key=True, autoincrement=True)

    superhero_id = Column(
        Integer,
        ForeignKey("superheroes.id"),
        nullable=False,
        unique=True,
        index=True
    )

    genero = Column(String(50), nullable=True)
    raza = Column(String(100), nullable=True)
    altura = Column(String(50), nullable=True)
    peso = Column(String(50), nullable=True)
    color_ojos = Column(String(50), nullable=True)
    color_cabello = Column(String(50), nullable=True)

    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    # Relación
    superhero = relationship("Superhero", back_populates="apariencia")

    def __repr__(self):
        return f"<Apariencia(superhero_id={self.superhero_id})>"
