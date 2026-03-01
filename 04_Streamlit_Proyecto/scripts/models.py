#!/usr/bin/env python3
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Heroe(Base):
    __tablename__ = 'heroes'
    
    id = Column(Integer, primary_key=True)
    heroe_id_api = Column(Integer, unique=True, nullable=False)  # ID de la API
    nombre = Column(String(200), nullable=False)
    nombre_real = Column(String(200))
    editorial = Column(String(100))
    genero = Column(String(50))
    raza = Column(String(100))
    altura = Column(String(50))
    peso = Column(String(50))
    color_ojos = Column(String(50))
    color_pelo = Column(String(50))
    lugar_nacimiento = Column(Text)
    primera_aparicion = Column(String(200))
    alineacion = Column(String(50))  # good, bad, neutral
    
    # Powerstats
    inteligencia = Column(Integer)
    fuerza = Column(Integer)
    velocidad = Column(Integer)
    durabilidad = Column(Integer)
    poder = Column(Integer)
    combate = Column(Integer)
    
    # Imágenes
    imagen_url = Column(String(500))
    imagen_xs = Column(String(500))
    imagen_sm = Column(String(500))
    imagen_md = Column(String(500))
    imagen_lg = Column(String(500))
    
    # Metadatos
    fecha_creacion = Column(DateTime, default=datetime.now)
    fecha_actualizacion = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relaciones
    apariciones = relationship("Aparicion", back_populates="heroe", cascade="all, delete-orphan")
    trabajos = relationship("Trabajo", back_populates="heroe", cascade="all, delete-orphan")
    conexiones = relationship("Conexion", back_populates="heroe", cascade="all, delete-orphan")
    metricas_historial = relationship("MetricasHeroe", back_populates="heroe")
    
    def __repr__(self):
        return f"<Heroe(nombre='{self.nombre}', editorial='{self.editorial}')>"

class Aparicion(Base):
    __tablename__ = 'apariciones'
    
    id = Column(Integer, primary_key=True)
    heroe_id = Column(Integer, ForeignKey('heroes.id'))
    tipo = Column(String(50))  # 'editorial', 'personaje', etc.
    valor = Column(Text)
    
    heroe = relationship("Heroe", back_populates="apariciones")
    
    def __repr__(self):
        return f"<Aparicion(heroe_id={self.heroe_id}, tipo='{self.tipo}')>"

class Trabajo(Base):
    __tablename__ = 'trabajos'
    
    id = Column(Integer, primary_key=True)
    heroe_id = Column(Integer, ForeignKey('heroes.id'))
    ocupacion = Column(Text)
    base = Column(Text)
    
    heroe = relationship("Heroe", back_populates="trabajos")
    
    def __repr__(self):
        return f"<Trabajo(heroe_id={self.heroe_id})>"

class Conexion(Base):
    __tablename__ = 'conexiones'
    
    id = Column(Integer, primary_key=True)
    heroe_id = Column(Integer, ForeignKey('heroes.id'))
    grupo_afiliacion = Column(Text)
    familiares = Column(Text)
    
    heroe = relationship("Heroe", back_populates="conexiones")
    
    def __repr__(self):
        return f"<Conexion(heroe_id={self.heroe_id})>"

class MetricasHeroe(Base):
    __tablename__ = 'metricas_heroes'
    
    id = Column(Integer, primary_key=True)
    heroe_id = Column(Integer, ForeignKey('heroes.id'))
    fecha_registro = Column(DateTime, default=datetime.now)
    poder_total = Column(Integer)  # Suma de powerstats
    poder_promedio = Column(Float)  # Promedio de powerstats
    
    heroe = relationship("Heroe", back_populates="metricas_historial")

class MetricasETL(Base):
    __tablename__ = 'metricas_etl'
    
    id = Column(Integer, primary_key=True)
    fecha_ejecucion = Column(DateTime, default=datetime.now)
    registros_extraidos = Column(Integer, default=0)
    registros_guardados = Column(Integer, default=0)
    registros_fallidos = Column(Integer, default=0)
    tiempo_ejecucion_segundos = Column(Float, default=0.0)
    estado = Column(String(50))  # 'exitoso', 'fallido'
    error_message = Column(Text, nullable=True)