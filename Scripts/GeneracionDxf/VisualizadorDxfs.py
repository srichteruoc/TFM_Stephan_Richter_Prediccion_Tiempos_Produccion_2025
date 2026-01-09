#!/usr/bin/env python3
"""
Visualizador de DXF - Grid 4x4
Genera una figura con 16 ejemplos de piezas sintéticas para la memoria del TFM
"""

import ezdxf
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.collections import LineCollection, PatchCollection
from pathlib import Path
import random
import numpy as np


def get_entity_lines(entity):
    """Extrae líneas de una entidad DXF para visualización"""
    lines = []

    if entity.dxftype() == 'LINE':
        start = (entity.dxf.start.x, entity.dxf.start.y)
        end = (entity.dxf.end.x, entity.dxf.end.y)
        lines.append([start, end])

    elif entity.dxftype() == 'LWPOLYLINE':
        points = list(entity.get_points(format='xy'))
        if entity.closed:
            points.append(points[0])
        for i in range(len(points) - 1):
            lines.append([points[i], points[i + 1]])

    elif entity.dxftype() == 'POLYLINE':
        points = [(v.dxf.location.x, v.dxf.location.y) for v in entity.vertices]
        if entity.is_closed:
            points.append(points[0])
        for i in range(len(points) - 1):
            lines.append([points[i], points[i + 1]])

    elif entity.dxftype() == 'CIRCLE':
        cx, cy = entity.dxf.center.x, entity.dxf.center.y
        r = entity.dxf.radius
        # Aproximar círculo con polígono
        theta = np.linspace(0, 2 * np.pi, 64)
        points = [(cx + r * np.cos(t), cy + r * np.sin(t)) for t in theta]
        for i in range(len(points) - 1):
            lines.append([points[i], points[i + 1]])
        lines.append([points[-1], points[0]])

    elif entity.dxftype() == 'ARC':
        cx, cy = entity.dxf.center.x, entity.dxf.center.y
        r = entity.dxf.radius
        start_angle = np.radians(entity.dxf.start_angle)
        end_angle = np.radians(entity.dxf.end_angle)
        if end_angle < start_angle:
            end_angle += 2 * np.pi
        theta = np.linspace(start_angle, end_angle, 32)
        points = [(cx + r * np.cos(t), cy + r * np.sin(t)) for t in theta]
        for i in range(len(points) - 1):
            lines.append([points[i], points[i + 1]])

    elif entity.dxftype() == 'ELLIPSE':
        cx, cy = entity.dxf.center.x, entity.dxf.center.y
        major_x, major_y = entity.dxf.major_axis.x, entity.dxf.major_axis.y
        ratio = entity.dxf.ratio
        major_len = np.sqrt(major_x ** 2 + major_y ** 2)
        minor_len = major_len * ratio
        rotation = np.arctan2(major_y, major_x)

        theta = np.linspace(0, 2 * np.pi, 64)
        points = []
        for t in theta:
            x = major_len * np.cos(t)
            y = minor_len * np.sin(t)
            # Rotar
            x_rot = x * np.cos(rotation) - y * np.sin(rotation) + cx
            y_rot = x * np.sin(rotation) + y * np.cos(rotation) + cy
            points.append((x_rot, y_rot))
        for i in range(len(points) - 1):
            lines.append([points[i], points[i + 1]])
        lines.append([points[-1], points[0]])

    return lines


def plot_dxf(ax, filepath, title=None):
    """Dibuja un archivo DXF en un axes de matplotlib"""
    try:
        doc = ezdxf.readfile(filepath)
        msp = doc.modelspace()

        all_lines = []
        all_x = []
        all_y = []

        for entity in msp:
            lines = get_entity_lines(entity)
            all_lines.extend(lines)
            for line in lines:
                all_x.extend([line[0][0], line[1][0]])
                all_y.extend([line[0][1], line[1][1]])

        if all_lines:
            lc = LineCollection(all_lines, colors='#2E86AB', linewidths=1.2)
            ax.add_collection(lc)

            # Calcular límites con margen
            min_x, max_x = min(all_x), max(all_x)
            min_y, max_y = min(all_y), max(all_y)

            margin_x = (max_x - min_x) * 0.1 or 10
            margin_y = (max_y - min_y) * 0.1 or 10

            ax.set_xlim(min_x - margin_x, max_x + margin_x)
            ax.set_ylim(min_y - margin_y, max_y + margin_y)
            ax.set_aspect('equal')

        ax.set_xticks([])
        ax.set_yticks([])
        ax.spines['top'].set_visible(True)
        ax.spines['right'].set_visible(True)
        ax.spines['bottom'].set_visible(True)
        ax.spines['left'].set_visible(True)

        if title:
            # Acortar título si es muy largo
            if len(title) > 25:
                title = title[:22] + "..."
            ax.set_title(title, fontsize=8, pad=3)

        return True

    except Exception as e:
        ax.text(0.5, 0.5, f"Error:\n{str(e)[:30]}",
                ha='center', va='center', fontsize=7, color='red',
                transform=ax.transAxes)
        ax.set_xticks([])
        ax.set_yticks([])
        if title:
            ax.set_title(title, fontsize=8, pad=3)
        return False


def get_dxf_dimensions(filepath):
    """Obtiene las dimensiones del bounding box de un DXF"""
    try:
        doc = ezdxf.readfile(filepath)
        msp = doc.modelspace()

        all_x = []
        all_y = []

        for entity in msp:
            lines = get_entity_lines(entity)
            for line in lines:
                all_x.extend([line[0][0], line[1][0]])
                all_y.extend([line[0][1], line[1][1]])

        if all_x and all_y:
            width = max(all_x) - min(all_x)
            height = max(all_y) - min(all_y)
            return width, height
        return None, None
    except:
        return None, None


def create_dxf_grid(folder_path, output_file="grid_piezas_sinteticas.png",
                    rows=4, cols=4, random_selection=True, dpi=200):
    """
    Crea un grid de visualización de archivos DXF

    Args:
        folder_path: Carpeta con los archivos DXF
        output_file: Nombre del archivo de salida
        rows: Número de filas del grid
        cols: Número de columnas del grid
        random_selection: Si True, selecciona archivos aleatorios
        dpi: Resolución de la imagen
    """
    folder = Path(folder_path)

    if not folder.exists():
        print(f"Error: No existe la carpeta {folder_path}")
        return

    # Buscar archivos DXF
    dxf_files = list(folder.glob("*.dxf")) + list(folder.glob("*.DXF"))

    if not dxf_files:
        print(f"No se encontraron archivos DXF en {folder_path}")
        return

    print(f"Encontrados {len(dxf_files)} archivos DXF")

    # Seleccionar archivos
    n_files = rows * cols
    if random_selection and len(dxf_files) > n_files:
        selected_files = random.sample(dxf_files, n_files)
    else:
        selected_files = dxf_files[:n_files]

    # Crear figura
    fig, axes = plt.subplots(rows, cols, figsize=(12, 14))
    fig.suptitle('Ejemplos de Geometrías Sintéticas Generadas',
                 fontsize=14, fontweight='bold', y=0.98)

    # Aplanar array de axes
    axes_flat = axes.flatten()

    # Dibujar cada DXF
    for idx, (ax, dxf_file) in enumerate(zip(axes_flat, selected_files)):
        print(f"Procesando [{idx + 1}/{n_files}]: {dxf_file.name}")

        # Obtener dimensiones
        width, height = get_dxf_dimensions(str(dxf_file))

        # Crear título con nombre y dimensiones
        name = dxf_file.stem
        if len(name) > 20:
            name = name[:17] + "..."

        if width is not None and height is not None:
            title = f"{name}\n({width:.1f} × {height:.1f} mm)"
        else:
            title = name

        plot_dxf(ax, str(dxf_file), title=title)

    # Si hay menos archivos que celdas, ocultar las celdas vacías
    for idx in range(len(selected_files), len(axes_flat)):
        axes_flat[idx].axis('off')

    plt.tight_layout()
    plt.subplots_adjust(top=0.94, hspace=0.4, wspace=0.2)

    # Guardar
    plt.savefig(output_file, dpi=dpi, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    print(f"\nGuardado: {output_file}")

    # Mostrar
    plt.show()

    return fig


if __name__ == "__main__":
    # Configuración
    DXF_FOLDER = r"C:\Users\r_ste.MSI\Documents\UOC\TFM\Datos_Sinteticos\Generador_Piezas_Dxf\Dataset_Piezas_Sinteticas_y_Anonimizadas"
    OUTPUT_FILE = r"C:\Users\r_ste.MSI\Documents\UOC\TFM\Datos_Sinteticos\Generador_Piezas_Dxf\Dataset_Piezas_Sinteticas_y_Anonimizadas\grid_piezas_sinteticas.png"

    # Crear grid
    create_dxf_grid(
        folder_path=DXF_FOLDER,
        output_file=OUTPUT_FILE,
        rows=4,
        cols=4,
        random_selection=True,  # Cambiar a False para las primeras 16
        dpi=200
    )