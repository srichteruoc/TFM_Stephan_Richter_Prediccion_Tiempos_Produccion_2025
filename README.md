# Predicción de Tiempos de Producción mediante
# Aprendizaje Automático: Integración de Datos Reales y
# Sintéticos en Procesos de Corte Láser y Plegado

## Trabajo Final de Máster - Ciencia de Datos (UOC, 2025)

**Autor:** Stephan Richter
**Tutor:** Lorena Polo Navarro
**Fecha:** Enero 2025

---

## Descripción

Sistema de predicción de tiempos de fabricación para corte láser y plegado, utilizando datos sintéticos de TruTops Calculate calibrados con datos reales de producción.

| Proceso | R² | MAE | Viable |
|---------|:--:|:---:|:------:|
| Corte Láser | 0.57 | 16.7 seg | SI |
| Plegado | 0.27 | 38.9 seg | NO |

---

## Estructura
```
├── Dataset_Piezas_Sinteticas_y_Anonimizadas/
│   ├── catalogo_piezas.csv
│   ├── Dxfs.zip
│   └── grid_piezas_sinteticas.png
├── Docs/
│   ├── TFM_Richter_Prediccion_Tiempos_Producción_2025.pdf
│   └── TFM_Richter_Prediccion_Tiempos_Producción_2025.pptx
├── Notebooks/
│   ├── 01_ETL_Preparacion_Datos/
│   │   └── datos_procesados/
│   ├── 02_Entrenamiento_Modelos_Sinteticos/
│   │   ├── datos_sinteticos/
│   │   └── modelos_exportados/
│   ├── 02b_Entrenamiento_Modelos_Sinteticos_Plegado/
│   │   ├── datos_sinteticos/
│   │   └── modelos_exportados/
│   └── 03_Validacion_Datos_Reales/
│       └── modelos_exportados/
├── Scripts/
│   ├── GeneracionDxf/
│   └── Generacion_Lectura_Calculos/
├── README.md
└── requirements.txt
```

---

## Ejecución

1. Instalar dependencias: `pip install -r requirements.txt`
2. Ejecutar notebooks en orden: 01 → 02 → 03

---

## Licencia

Esta obra está sujeta a una licencia [Creative Commons Reconocimiento-NoComercial-SinObraDerivada 3.0 España (CC BY-NC-ND 3.0 ES)](https://creativecommons.org/licenses/by-nc-nd/3.0/es/)

![CC BY-NC-ND](https://licensebuttons.net/l/by-nc-nd/3.0/es/88x31.png)
```

## requirements.txt
```
numpy>=1.24.0
pandas>=2.0.0
scipy>=1.10.0
scikit-learn>=1.3.0
matplotlib>=3.7.0
seaborn>=0.12.0
ezdxf>=1.0.0
jupyter>=1.0.0
openpyxl>=3.1.0
tqdm>=4.65.0