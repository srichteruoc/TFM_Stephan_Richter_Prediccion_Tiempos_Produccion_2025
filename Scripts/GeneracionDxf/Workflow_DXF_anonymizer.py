"""
Workflow Completo - Ejemplo Práctico
Demuestra el flujo completo desde la creación hasta el análisis
"""

from pathlib import Path
import json


def workflow_complete():
    """
    Workflow completo de principio a fin
    """

    print("=" * 70)
    print("🎭 DXF ANONYMIZER - WORKFLOW COMPLETO")
    print("=" * 70)

    # ========================================================================
    # PASO 1: SETUP - Crear estructura de carpetas
    # ========================================================================
    print("\n📁 PASO 1: Setup")
    print("-" * 70)

    folders = {
        'input': Path('./piezas_clientes'),
        'output': Path('./piezas_anonimizadas'),
        'dataset': Path('./dataset_sheet_metal'),
        'reports': Path('./reports')
    }

    for name, folder in folders.items():
        folder.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ Carpeta creada: {folder}")

    # ========================================================================
    # PASO 2: GENERAR DATOS DE PRUEBA
    # ========================================================================
    print("\n🔧 PASO 2: Generar DXF de Prueba")
    print("-" * 70)

    # Ejecutar generador de pruebas
    import create_test_dxf
    create_test_dxf.create_simple_sheet_metal_part(
        str(folders['input'] / "cliente_001.dxf")
    )
    create_test_dxf.create_complex_sheet_metal_part(
        str(folders['input'] / "cliente_002.dxf")
    )

    print("  ✓ Archivos de prueba generados")

    # ========================================================================
    # PASO 3: ANALIZAR ARCHIVOS ORIGINALES
    # ========================================================================
    print("\n🔍 PASO 3: Análisis de Archivos Originales")
    print("-" * 70)

    from dxf_anonymizer_phase1 import DXFAnalyzer

    analysis_results = {}

    for dxf_file in folders['input'].glob("*.dxf"):
        print(f"\n  Analizando: {dxf_file.name}")

        analyzer = DXFAnalyzer(str(dxf_file))
        analyzer.load()
        features = analyzer.extract_features()

        # Guardar análisis
        analysis_results[dxf_file.name] = {
            'circles': len(features.circles),
            'lines': len(features.lines),
            'arcs': len(features.arcs),
            'bounds': features.bounds
        }

        print(f"    - Círculos: {len(features.circles)}")
        print(f"    - Líneas: {len(features.lines)}")
        print(f"    - Arcos: {len(features.arcs)}")
        if features.bounds:
            print(f"    - Dimensiones: {features.bounds['width']:.1f} x {features.bounds['height']:.1f} mm")

    # Guardar análisis en JSON
    analysis_file = folders['reports'] / 'original_analysis.json'
    with open(analysis_file, 'w') as f:
        json.dump(analysis_results, f, indent=2)
    print(f"\n  ✓ Análisis guardado en: {analysis_file}")

    # ========================================================================
    # PASO 4: ANONIMIZACIÓN - NIVEL ÚNICO
    # ========================================================================
    print("\n🎭 PASO 4: Anonimización (Nivel Medium)")
    print("-" * 70)

    from dxf_anonymizer_phase1 import DXFAnonymizer

    anonymizer = DXFAnonymizer(anonymization_level='medium')

    for dxf_file in folders['input'].glob("*.dxf"):
        input_path = str(dxf_file)
        output_name = f"anon_{dxf_file.name}"
        output_path = str(folders['output'] / output_name)

        print(f"\n  Procesando: {dxf_file.name}")
        report = anonymizer.anonymize(input_path, output_path)

        # Guardar reporte individual
        report_file = folders['reports'] / f"report_{dxf_file.stem}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"    ✓ Anonimizado: {output_name}")
        print(f"    ✓ Reporte: {report_file.name}")

    # ========================================================================
    # PASO 5: CREAR DATASET MULTI-NIVEL
    # ========================================================================
    print("\n📦 PASO 5: Crear Dataset Multi-Nivel")
    print("-" * 70)

    from batch_processor import DatasetCreator

    creator = DatasetCreator(
        source_folder=str(folders['input']),
        dataset_folder=str(folders['dataset'])
    )

    creator.create_dataset(levels=['light', 'medium', 'aggressive'])

    # ========================================================================
    # PASO 6: COMPARACIÓN Y VALIDACIÓN
    # ========================================================================
    print("\n📊 PASO 6: Comparación Original vs Anonimizado")
    print("-" * 70)

    comparison_results = []

    for original_file in folders['input'].glob("*.dxf"):
        original_name = original_file.name
        anon_file = folders['output'] / f"anon_{original_name}"

        if not anon_file.exists():
            continue

        print(f"\n  Comparando: {original_name}")

        # Analizar original
        analyzer_orig = DXFAnalyzer(str(original_file))
        analyzer_orig.load()
        features_orig = analyzer_orig.extract_features()

        # Analizar anonimizado
        analyzer_anon = DXFAnalyzer(str(anon_file))
        analyzer_anon.load()
        features_anon = analyzer_anon.extract_features()

        # Calcular diferencias
        comparison = {
            'file': original_name,
            'original': {
                'circles': len(features_orig.circles),
                'lines': len(features_orig.lines),
                'width': features_orig.bounds['width'] if features_orig.bounds else 0,
                'height': features_orig.bounds['height'] if features_orig.bounds else 0
            },
            'anonymized': {
                'circles': len(features_anon.circles),
                'lines': len(features_anon.lines),
                'width': features_anon.bounds['width'] if features_anon.bounds else 0,
                'height': features_anon.bounds['height'] if features_anon.bounds else 0
            },
            'changes': {
                'circles_delta': len(features_anon.circles) - len(features_orig.circles),
                'lines_delta': len(features_anon.lines) - len(features_orig.lines),
                'width_change_%': 0,
                'height_change_%': 0
            }
        }

        # Calcular cambios porcentuales
        if features_orig.bounds and features_anon.bounds:
            orig_w = features_orig.bounds['width']
            anon_w = features_anon.bounds['width']
            orig_h = features_orig.bounds['height']
            anon_h = features_anon.bounds['height']

            if orig_w > 0:
                comparison['changes']['width_change_%'] = ((anon_w - orig_w) / orig_w) * 100
            if orig_h > 0:
                comparison['changes']['height_change_%'] = ((anon_h - orig_h) / orig_h) * 100

        comparison_results.append(comparison)

        print(f"    Original:    {comparison['original']['circles']} círculos, "
              f"{comparison['original']['width']:.1f}x{comparison['original']['height']:.1f}mm")
        print(f"    Anonimizado: {comparison['anonymized']['circles']} círculos, "
              f"{comparison['anonymized']['width']:.1f}x{comparison['anonymized']['height']:.1f}mm")
        print(f"    Cambio:      {comparison['changes']['width_change_%']:+.1f}% ancho, "
              f"{comparison['changes']['height_change_%']:+.1f}% alto")

    # Guardar comparación
    comparison_file = folders['reports'] / 'comparison.json'
    with open(comparison_file, 'w') as f:
        json.dump(comparison_results, f, indent=2)
    print(f"\n  ✓ Comparación guardada en: {comparison_file}")

    # ========================================================================
    # PASO 7: RESUMEN FINAL
    # ========================================================================
    print("\n" + "=" * 70)
    print("✅ WORKFLOW COMPLETADO")
    print("=" * 70)

    print("\n📂 Archivos generados:")
    print(f"  • Originales:      {folders['input']}")
    print(f"  • Anonimizados:    {folders['output']}")
    print(f"  • Dataset:         {folders['dataset']}")
    print(f"  • Reportes:        {folders['reports']}")

    print("\n📊 Estadísticas:")
    total_files = len(list(folders['input'].glob("*.dxf")))
    total_anon = len(list(folders['output'].glob("*.dxf")))
    print(f"  • Archivos originales: {total_files}")
    print(f"  • Archivos anonimizados: {total_anon}")

    print("\n💡 Próximos pasos:")
    print("  1. Revisa los archivos en las carpetas de salida")
    print("  2. Compara visualmente en un visor DXF")
    print("  3. Valida que las piezas sean manufacturables")
    print("  4. Ajusta niveles de anonimización si es necesario")

    print("\n🎉 ¡Listo para usar tu dataset anonimizado!")
    print("=" * 70 + "\n")


def quick_test():
    """Test rápido con un solo archivo"""

    print("\n🚀 TEST RÁPIDO")
    print("=" * 70)

    # Crear archivo de prueba
    from create_test_dxf import create_simple_sheet_metal_part
    create_simple_sheet_metal_part("test_piece.dxf")

    # Anonimizar
    from dxf_anonymizer_phase1 import DXFAnonymizer

    anonymizer = DXFAnonymizer('medium')
    report = anonymizer.anonymize(
        'test_piece.dxf',
        'test_piece_anon.dxf'
    )

    print("\n✅ Test completado")
    print(f"   Original: test_piece.dxf")
    print(f"   Anonimizado: test_piece_anon.dxf")
    print(f"\n📊 Transformaciones aplicadas:")
    for key, value in report['transformations'].items():
        print(f"   - {key}: {value}")


if __name__ == "__main__":
    import sys

    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║          DXF Anonymizer - Workflow Example                ║
    ╚════════════════════════════════════════════════════════════╝
    """)

    print("\nSelecciona una opción:")
    print("  1. Workflow completo (demo completa)")
    print("  2. Test rápido (un solo archivo)")
    print("  3. Salir")

    # Para ejecución automática, descomentar:
    # quick_test()
    # workflow_complete()

    print("\n💡 Descomenta las funciones al final del archivo para ejecutar")