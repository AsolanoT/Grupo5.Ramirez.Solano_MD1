
# 📊 Minería de Datos – Grupo 5

## Proyecto ETL y Análisis Predictivo de Superhéroes

# 🚀 Clonar

Para clonar este proyecto desde Git:

```bash
git clone https://github.com/AsolanoT/Grupo5.Ramirez.Solano_MD1.git
```

---

# 👥 Autores – Grupo 5

**Jordan Ramírez Gallego**
📧 [jramirez-2023a@corhuila.edu.co](mailto:jramirez-2023a@corhuila.edu.co)

**Angel Gustavo Solano Trujillo**
📧 [agsolano-2023a@corhuila.edu.co](mailto:agsolano-2023a@corhuila.edu.co)

---

# 📌 Descripción del Proyecto

Este proyecto implementa un proceso **ETL (Extract, Transform, Load)** utilizando la API pública de SuperheroAPI para extraer información estructurada sobre superhéroes, incluyendo estadísticas de poder, afiliaciones y biografías.

Los datos extraídos son procesados, almacenados en una base de datos PostgreSQL y posteriormente utilizados para análisis exploratorio, visualización interactiva y modelos de machine learning.

API utilizada:
[https://superheroapi.com/](https://superheroapi.com/)

---

# 🎯 Objetivo del Proyecto

Desarrollar una arquitectura de datos completa que permita:

* Extraer información desde una API externa.
* Transformar y estructurar datos para análisis.
* Diseñar una base de datos optimizada en PostgreSQL.
* Implementar visualizaciones interactivas.
* Aplicar modelos de machine learning para análisis predictivo.
* Presentar resultados con métricas de evaluación y recomendaciones.

---

# 📂 Descripción de los Datos

La API proporciona información detallada sobre superhéroes, incluyendo:

* Nombre
* Editorial (Marvel, DC, etc.)
* Estadísticas de poder:

  * Inteligencia
  * Fuerza
  * Velocidad
  * Durabilidad
  * Poder
  * Combate
* Información biográfica
* Afiliaciones

Los valores de poder se encuentran en escala de 0 a 100.
Algunos registros pueden contener valores faltantes (null), los cuales se tratan durante la fase de transformación o modelado.

---

# 📏 Alcance

El proyecto incluye:

* Implementación de un extractor ETL con manejo de errores y logging.
* Almacenamiento estructurado en PostgreSQL.
* Dashboard interactivo en Streamlit.
* Análisis exploratorio de datos.
* Modelos de machine learning para:

  * Clasificación de superhéroes por nivel de fortaleza.
  * Predicción de valores faltantes.
  * Agrupamiento por afiliación.
* Contenerización con Docker Compose.
* Documentación técnica y presentación ejecutiva.

No incluye entrenamiento en tiempo real ni integración con APIs privadas.

---

# 🛠 Herramientas

Las herramientas empleadas en este proyecto incluyen:

* **VS Code** – Entorno de desarrollo
* **Python** – Lenguaje principal
* **WSL** – Entorno Linux en Windows
* **PostgreSQL** – Base de datos relacional
* **Docker & Docker Compose** – Orquestación de contenedores
* **Streamlit** – Dashboard interactivo
* **Scikit-Learn** – Modelos de machine learning
* **Pandas & NumPy** – Procesamiento de datos
* **Matplotlib / Seaborn / Plotly** – Visualización

---

# 💡 Solución

Se diseñó una arquitectura modular compuesta por:

1. **Extractor ETL**

   * Consume la API.
   * Maneja errores.
   * Registra logs.
   * Genera archivos CSV y JSON.

2. **Base de Datos PostgreSQL**

   * Diseño relacional optimizado.
   * Inserción estructurada de datos.
   * Consultas analíticas.

3. **Dashboard Streamlit**

   * Visualización interactiva de estadísticas.
   * Filtros por editorial.
   * Comparaciones entre héroes.

4. **Machine Learning**

   * Clasificación de fortaleza.
   * Regresión para predicción de poder faltante.
   * Clustering por características similares.

---

# 🏗 Arquitectura de Datos

```
Superhero API
       ↓
Extractor ETL
       ↓
Transformación
       ↓
PostgreSQL
       ↓
Dashboard + ML
```

---

# 📁 Estructura del Proyecto

```
etl-superheroes/
├── data/
├── logs/
├── scripts/
│   ├── extractor.py
│   ├── transformador.py
│   ├── visualizador.py
├── notebooks/
├── docker-compose.yml
├── requirements.txt
├── README.md
└── .env
```

---

# 📊 Análisis Propuestos

* Distribución de poderes.
* Clasificación de superhéroes por fortaleza.
* Predicción de poder faltante mediante regresión.
* Agrupamiento por afiliación utilizando clustering.
* Comparación estadística entre editoriales.


