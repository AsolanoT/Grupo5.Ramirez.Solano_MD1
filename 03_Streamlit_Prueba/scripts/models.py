#!/usr/bin/env python3
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Ciudad(Base):
    __tablename__ = 'ciudades'
    
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False, unique=True)
    pais = Column(String(100))
    latitud = Column(Float)
    longitud = Column(Float)
    fecha_creacion = Column(DateTime, default=datetime.now)
    
    # Relación con registros climáticos
    registros_clima = relationship("RegistroClima", back_populates="ciudad")
    
    def __repr__(self):
        return f"<Ciudad(nombre='{self.nombre}')>"

class RegistroClima(Base):
    __tablename__ = 'registros_clima'
    
    id = Column(Integer, primary_key=True)
    ciudad_id = Column(Integer, ForeignKey('ciudades.id'))
    temperatura = Column(Float)
    sensacion_termica = Column(Float)
    humedad = Column(Integer)
    velocidad_viento = Column(Float)
    descripcion = Column(String(200))
    codigo_tiempo = Column(Integer)
    fecha_extraccion = Column(DateTime, default=datetime.now)
    
    # Relación con ciudad
    ciudad = relationship("Ciudad", back_populates="registros_clima")
    
    def __repr__(self):
        return f"<RegistroClima(ciudad_id={self.ciudad_id}, temp={self.temperatura}°C)>"
    
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