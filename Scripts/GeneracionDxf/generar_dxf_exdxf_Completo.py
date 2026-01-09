#!/usr/bin/env python3
"""
Script completo para generar archivos DXF
- Procesar CSV existente
- Generar piezas aleatorias (rectángulos y arandelas con/sin agujeros)

Instalación: pip install ezdxf pandas
"""

import ezdxf
import pandas as pd
import random
import math
import csv
import os
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple


# ============================================================================
# FUNCIONES ORIGINALES - PROCESAR CSV
# ============================================================================

def crear_rectangulo_dxf(ancho, largo, nombre_archivo, carpeta_salida):
    """
    Crea un archivo DXF con un rectángulo simple centrado
    """
    doc = ezdxf.new('R2018', setup=True)
    msp = doc.modelspace()

    x1, y1 = -ancho / 2, -largo / 2
    x2, y2 = ancho / 2, largo / 2

    puntos = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
    msp.add_lwpolyline(puntos, close=True)

    # texto = f"{ancho}x{largo}"
    # msp.add_text(
    #     texto,
    #     dxfattribs={'height': min(ancho, largo) * 0.1, 'layer': 'TEXT'}
    # ).set_placement((0, 0), align='MIDDLE_CENTER')

    ruta_completa = os.path.join(carpeta_salida, nombre_archivo)
    doc.saveas(ruta_completa)
    print(f"✓ Creado: {nombre_archivo}")


def procesar_csv(archivo_csv, carpeta_salida='DXF_Piezas'):
    """
    Lee el CSV y genera un archivo DXF por cada fila
    """
    Path(carpeta_salida).mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(archivo_csv)

    print(f"\nProcesando {len(df)} piezas desde CSV...\n")

    for idx, row in df.iterrows():
        num_pieza = str(row['Nº pieza']).strip()
        ancho = float(row['Anchura'])
        largo = float(row['Longitud'])
        cantidad = int(row['Cantidad real'])
        material = str(row['Material en bruto']).strip()

        nombre_archivo = f"{num_pieza}_{cantidad}_{material}.dxf"
        nombre_archivo = nombre_archivo.replace('/', '-').replace('\\', '-')

        try:
            crear_rectangulo_dxf(ancho, largo, nombre_archivo, carpeta_salida)
        except Exception as e:
            print(f"✗ Error en {nombre_archivo}: {e}")

    print(f"\n¡Completado! {len(df)} archivos DXF creados en '{carpeta_salida}'")


# ============================================================================
# NUEVAS FUNCIONES - GENERACIÓN ALEATORIA
# ============================================================================

@dataclass
class ConfiguracionGeneracion:
    """Configuración para la generación aleatoria de piezas"""
    numero_total_piezas: int = 20

    longitud_maxima: float = 500.0
    ancho_maximo: float = 500.0
    diametro_exterior_maximo: float = 500.0

    longitud_minima: float = 50.0
    ancho_minimo: float = 50.0
    diametro_exterior_minimo: float = 50.0

    diametro_agujero_min: float = 3.0
    diametro_agujero_max: float = 20.0
    cantidad_agujeros_min: int = 1
    cantidad_agujeros_max: int = 8
    margen_borde_rectangulo: float = 15.0

    relacion_diametro_minima: float = 0.3

    carpeta_dxf: str = 'DXF_Aleatorios'
    archivo_csv: str = 'piezas_generadas.csv'


def crear_rectangulo_con_agujeros(ancho: float, largo: float,
                                  diametros_agujeros: List[float],
                                  posiciones_agujeros: List[Tuple[float, float]],
                                  nombre_archivo: str, carpeta_salida: str):
    """Crea un rectángulo con agujeros circulares"""
    doc = ezdxf.new('R2018', setup=True)
    msp = doc.modelspace()

    x1, y1 = -ancho / 2, -largo / 2
    x2, y2 = ancho / 2, largo / 2

    puntos_rectangulo = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
    msp.add_lwpolyline(puntos_rectangulo, close=True)

    for (x, y), diametro in zip(posiciones_agujeros, diametros_agujeros):
        radio = diametro / 2
        msp.add_circle((x, y), radio)

    ruta_completa = Path(carpeta_salida) / nombre_archivo
    doc.saveas(ruta_completa)


def crear_arandela(diametro_exterior: float, diametro_interior: float,
                   nombre_archivo: str, carpeta_salida: str):
    """Crea una arandela (dos círculos concéntricos)"""
    doc = ezdxf.new('R2018', setup=True)
    msp = doc.modelspace()

    radio_exterior = diametro_exterior / 2
    msp.add_circle((0, 0), radio_exterior)

    radio_interior = diametro_interior / 2
    msp.add_circle((0, 0), radio_interior)

    ruta_completa = Path(carpeta_salida) / nombre_archivo
    doc.saveas(ruta_completa)


def crear_arandela_con_agujeros(diametro_exterior: float, diametro_interior: float,
                                cantidad_agujeros: int, diametro_agujeros: float,
                                nombre_archivo: str, carpeta_salida: str):
    """Crea una arandela con agujeros distribuidos circularmente"""
    doc = ezdxf.new('R2018', setup=True)
    msp = doc.modelspace()

    radio_exterior = diametro_exterior / 2
    msp.add_circle((0, 0), radio_exterior)

    radio_interior = diametro_interior / 2
    msp.add_circle((0, 0), radio_interior)

    radio_agujeros = (radio_exterior + radio_interior) / 2
    radio_agujero = diametro_agujeros / 2

    angulo_incremento = 360.0 / cantidad_agujeros

    for i in range(cantidad_agujeros):
        angulo = math.radians(i * angulo_incremento)
        x = radio_agujeros * math.cos(angulo)
        y = radio_agujeros * math.sin(angulo)
        msp.add_circle((x, y), radio_agujero)

    ruta_completa = Path(carpeta_salida) / nombre_archivo
    doc.saveas(ruta_completa)


def generar_posiciones_agujeros_rectangulo(ancho: float, largo: float,
                                           cantidad: int, diametros: List[float],
                                           margen: float) -> Tuple[List[Tuple[float, float]], str]:
    """Genera posiciones para agujeros con distribución aleatoria"""
    tipos_distribucion = ['cuadricula', 'circular', 'aleatoria']
    tipo = random.choice(tipos_distribucion)

    posiciones = []
    x1, y1 = -ancho / 2, -largo / 2
    x2, y2 = ancho / 2, largo / 2

    if tipo == 'cuadricula':
        cols = int(math.sqrt(cantidad))
        filas = int(math.ceil(cantidad / cols))

        ancho_util = ancho - 2 * margen
        largo_util = largo - 2 * margen

        espaciado_x = ancho_util / (cols + 1) if cols > 0 else 0
        espaciado_y = largo_util / (filas + 1) if filas > 0 else 0

        idx = 0
        for fila in range(filas):
            for col in range(cols):
                if idx >= cantidad:
                    break
                x = x1 + margen + espaciado_x * (col + 1)
                y = y1 + margen + espaciado_y * (fila + 1)
                posiciones.append((x, y))
                idx += 1

    elif tipo == 'circular':
        centro_x, centro_y = 0, 0
        radio_x = (ancho / 2) - margen - max(diametros) / 2
        radio_y = (largo / 2) - margen - max(diametros) / 2

        angulo_incremento = 360.0 / cantidad

        for i in range(cantidad):
            angulo = math.radians(i * angulo_incremento)
            x = centro_x + radio_x * math.cos(angulo)
            y = centro_y + radio_y * math.sin(angulo)
            posiciones.append((x, y))

    else:  # aleatoria
        max_radio = max(diametros) / 2

        for _ in range(cantidad):
            x = random.uniform(x1 + margen + max_radio, x2 - margen - max_radio)
            y = random.uniform(y1 + margen + max_radio, y2 - margen - max_radio)
            posiciones.append((x, y))

    return posiciones, tipo

def cantidad_agujeros_realista():
    """Distribución realista: más piezas simples, menos complejas"""
    opciones = [1, 1, 1, 2, 2,2, 4, 4, 8, 8, 16, 32]  # ponderado
    return random.choice(opciones)

def generar_piezas_aleatorias(config: ConfiguracionGeneracion):
    """Genera piezas aleatorias en pares (sin agujeros + con agujeros)"""
    Path(config.carpeta_dxf).mkdir(parents=True, exist_ok=True)

    datos_csv = []
    num_pares = config.numero_total_piezas // 2

    print(f"\n{'=' * 60}")
    print(f"GENERANDO {num_pares} PARES DE PIEZAS ({config.numero_total_piezas} ARCHIVOS DXF)")
    print(f"{'=' * 60}\n")

    for idx in range(num_pares):
        es_rectangulo = random.choice([True, False])

        if es_rectangulo:
            # PAR DE RECTÁNGULOS
            ancho = random.uniform(config.ancho_minimo, config.ancho_maximo)
            largo = random.uniform(config.longitud_minima, config.longitud_maxima)

            nombre_base = f"RECT_{idx + 1:03d}_{ancho:.1f}x{largo:.1f}"
            nombre_sin_agujeros = f"{nombre_base}.dxf"

            crear_rectangulo_dxf(ancho, largo, nombre_sin_agujeros, config.carpeta_dxf)

            datos_csv.append({
                'Archivo': nombre_sin_agujeros,
                'Tipo': 'Rectangulo',
                'Parametros': f'Ancho={ancho:.2f}, Largo={largo:.2f}',
                'Descripcion': f'Rectángulo de {ancho:.1f}mm x {largo:.1f}mm'
            })

            print(f"✓ {nombre_sin_agujeros}")

            # cantidad_agujeros = random.randint(config.cantidad_agujeros_min,
            #                                    config.cantidad_agujeros_max)

            cantidad_agujeros = cantidad_agujeros_realista()

            diametros_agujeros = [
                random.uniform(config.diametro_agujero_min, config.diametro_agujero_max)
                for _ in range(cantidad_agujeros)
            ]

            posiciones, tipo_distribucion = generar_posiciones_agujeros_rectangulo(
                ancho, largo, cantidad_agujeros, diametros_agujeros, config.margen_borde_rectangulo
            )

            nombre_con_agujeros = f"{nombre_base}_{cantidad_agujeros}holes.dxf"

            crear_rectangulo_con_agujeros(
                ancho, largo, diametros_agujeros, posiciones,
                nombre_con_agujeros, config.carpeta_dxf
            )

            diametros_str = ', '.join([f'{d:.2f}' for d in diametros_agujeros])
            datos_csv.append({
                'Archivo': nombre_con_agujeros,
                'Tipo': 'Rectangulo con agujeros',
                'Parametros': f'Ancho={ancho:.2f}, Largo={largo:.2f}, Agujeros={cantidad_agujeros}, Diametros=[{diametros_str}]',
                'Descripcion': f'Rectángulo {ancho:.1f}x{largo:.1f}mm con {cantidad_agujeros} agujeros (distribución {tipo_distribucion})'
            })

            print(f"✓ {nombre_con_agujeros} (distribución: {tipo_distribucion})")

        else:
            # PAR DE ARANDELAS
            d_exterior = random.uniform(config.diametro_exterior_minimo,
                                        config.diametro_exterior_maximo)

            d_interior_min = d_exterior * config.relacion_diametro_minima
            d_interior_max = d_exterior * 0.8
            d_interior = random.uniform(d_interior_min, d_interior_max)

            nombre_base = f"WASH_{idx + 1:03d}_D{d_exterior:.1f}-{d_interior:.1f}"
            nombre_sin_agujeros = f"{nombre_base}.dxf"

            crear_arandela(d_exterior, d_interior, nombre_sin_agujeros, config.carpeta_dxf)

            datos_csv.append({
                'Archivo': nombre_sin_agujeros,
                'Tipo': 'Arandela',
                'Parametros': f'D_exterior={d_exterior:.2f}, D_interior={d_interior:.2f}',
                'Descripcion': f'Arandela Ø{d_exterior:.1f}mm / Ø{d_interior:.1f}mm'
            })

            print(f"✓ {nombre_sin_agujeros}")

            cantidad_agujeros = random.randint(config.cantidad_agujeros_min,
                                               config.cantidad_agujeros_max)

            ancho_anillo = (d_exterior - d_interior) / 2
            d_agujero_max = min(config.diametro_agujero_max, ancho_anillo * 0.6)
            d_agujero = random.uniform(config.diametro_agujero_min, d_agujero_max)

            nombre_con_agujeros = f"{nombre_base}_{cantidad_agujeros}holes.dxf"

            crear_arandela_con_agujeros(
                d_exterior, d_interior, cantidad_agujeros, d_agujero,
                nombre_con_agujeros, config.carpeta_dxf
            )

            datos_csv.append({
                'Archivo': nombre_con_agujeros,
                'Tipo': 'Arandela con agujeros',
                'Parametros': f'D_exterior={d_exterior:.2f}, D_interior={d_interior:.2f}, Agujeros={cantidad_agujeros}, D_agujero={d_agujero:.2f}',
                'Descripcion': f'Arandela Ø{d_exterior:.1f}/Ø{d_interior:.1f}mm con {cantidad_agujeros} agujeros de Ø{d_agujero:.1f}mm (circular)'
            })

            print(f"✓ {nombre_con_agujeros} (distribución: circular)")

        print()

    # Guardar CSV
    ruta_csv = Path(config.carpeta_dxf) / config.archivo_csv
    with open(ruta_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Archivo', 'Tipo', 'Parametros', 'Descripcion'])
        writer.writeheader()
        writer.writerows(datos_csv)

    print(f"{'=' * 60}")
    print(f"✓ Generación completada!")
    print(f"✓ {config.numero_total_piezas} archivos DXF creados en '{config.carpeta_dxf}'")
    print(f"✓ Información guardada en '{ruta_csv}'")
    print(f"{'=' * 60}\n")


# ============================================================================
# MAIN - EJEMPLOS DE USO
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("GENERADOR DE ARCHIVOS DXF")
    print("=" * 60)
    print("\n¿Qué deseas hacer?")
    print("1. Procesar archivo CSV existente")
    print("2. Generar piezas aleatorias")
    print("3. Ambas cosas")

    opcion = input("\nSelecciona una opción (1/2/3): ").strip()

    if opcion in ['1', '3']:
        # OPCIÓN 1: Procesar CSV
        archivo_csv = input("\nRuta del archivo CSV (o Enter para 'piezas_ejemplo.csv'): ").strip()
        if not archivo_csv:
            archivo_csv = "piezas_ejemplo.csv"

        if os.path.exists(archivo_csv):
            procesar_csv(archivo_csv, carpeta_salida='DXF_desde_CSV')
        else:
            print(f"✗ Archivo '{archivo_csv}' no encontrado")

    if opcion in ['2', '3']:
        # OPCIÓN 2: Generar aleatorias
        print("\n" + "=" * 60)
        print("CONFIGURACIÓN DE GENERACIÓN ALEATORIA")
        print("=" * 60)

        config = ConfiguracionGeneracion(
            numero_total_piezas=2000,

            longitud_maxima=1450.0,
            ancho_maximo=2900,
            diametro_exterior_maximo=1450.0,

            longitud_minima=10.0,
            ancho_minimo=10.0,
            diametro_exterior_minimo=10.0,

            diametro_agujero_min=4.0,
            diametro_agujero_max=15.0,
            cantidad_agujeros_min=2,
            cantidad_agujeros_max=50,
            margen_borde_rectangulo=20.0,

            relacion_diametro_minima=0.35,

            carpeta_dxf='DXF_Piezas_Aleatorias',
            archivo_csv='catalogo_piezas.csv'
        )

        generar_piezas_aleatorias(config)

    print("\n✓ ¡Proceso completado!")
    print("Los archivos DXF pueden abrirse con AutoCAD, LibreCAD, o software de corte láser")
