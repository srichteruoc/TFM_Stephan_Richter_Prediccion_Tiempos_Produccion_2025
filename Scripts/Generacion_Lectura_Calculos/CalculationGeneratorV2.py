#!/usr/bin/env python3
"""
TruTops Calculate XML Generator

This script generates calculation files (.cprj) for TruTops Calculate
based on combinations of DXF files, materials, and working places.
"""

import os
import uuid
import itertools
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import xml.etree.ElementTree as ET
from xml.dom import minidom


@dataclass
class Material:
    """Material definition"""
    name: str
    thickness: Optional[float] = None


@dataclass
class WorkingPlace:
    """Working place/step definition"""
    name: str
    setup_time: str = "00:00:00"
    parameters: Optional[Dict[str, Any]] = None


@dataclass
class CalculationConfig:
    """Configuration for calculation generation"""
    measure_system: int = 1  # 1=metric, 0=imperial
    base_currency: str = "CHF"
    batch_report_type: int = 1
    author_version: str = "3.0"


class TruTopsCalculateGenerator:
    """Generator for TruTops Calculate XML files"""

    def __init__(self, config: CalculationConfig = None):
        self.config = config or CalculationConfig()

    def generate_uuid(self) -> str:
        """Generate a UUID for parts/articles"""
        return str(uuid.uuid4()).replace('-', '')[:12]

    def get_dxf_files_from_folder(self, folder_path: str, recursive: bool = False) -> List[str]:
        """
        Get all DXF files from a folder

        Args:
            folder_path: Path to the folder containing DXF files
            recursive: If True, search subdirectories recursively

        Returns:
            List of full paths to DXF files
        """
        folder = Path(folder_path)

        if not folder.exists():
            print(f"Folder not found: {folder_path}")
            return []

        if not folder.is_dir():
            print(f"Path is not a directory: {folder_path}")
            return []

        # Search for DXF files (case-insensitive)
        if recursive:
            dxf_files = list(folder.rglob("*.DXF")) + list(folder.rglob("*.dxf"))
        else:
            dxf_files = list(folder.glob("*.DXF")) + list(folder.glob("*.dxf"))

        # Convert to strings and remove duplicates
        dxf_paths = sorted(list(set(str(f) for f in dxf_files)))

        print(f"Found {len(dxf_paths)} DXF files in {folder_path}")
        if dxf_paths:
            print("Files found:")
            for dxf_path in dxf_paths:
                print(f"  - {Path(dxf_path).name}")

        return dxf_paths

    def create_calculation_xml(self,
                               dxf_file: str,
                               material: Material,
                               working_places: List[WorkingPlace],
                               part_name: str = None) -> str:
        """
        Create a calculation XML for a specific combination of DXF, material, and working places

        Args:
            dxf_file: Path to the DXF file
            material: Material specification
            working_places: List of working places/steps
            part_name: Optional part name (defaults to DXF filename without extension)

        Returns:
            XML string for the calculation
        """
        if part_name is None:
            part_name = Path(dxf_file).stem

        # Generate UUIDs
        order_uuid = self.generate_uuid()
        part_uuid = self.generate_uuid()

        # Create root document
        doc = ET.Element("document")

        # Create head
        head = ET.SubElement(doc, "head")
        author = ET.SubElement(head, "author")
        author.set("dtdversion", "")
        author.set("authorversion", self.config.author_version)
        author.set("description", "")

        # Create body
        body = ET.SubElement(doc, "body")

        # BatchReportTyp
        batch_report = ET.SubElement(body, "BatchReportTyp")
        batch_report.text = str(self.config.batch_report_type)

        # Options
        options = ET.SubElement(body, "Options")
        options.set("Measure", str(self.config.measure_system))
        options.set("BaseCurrency", self.config.base_currency)

        # OrderData
        order_data = ET.SubElement(body, "OrderData")
        article_uuid = ET.SubElement(order_data, "ArticleUuid")
        article_uuid.text = order_uuid
        article_no = ET.SubElement(order_data, "ArticleNo")
        article_no.text = "Order"
        quantity = ET.SubElement(order_data, "Quantity")
        quantity.text = "1"

        # Parts
        parts = ET.SubElement(body, "Parts")

        # Order part
        order_part = ET.SubElement(parts, "Part")
        order_part.set("Uuid", order_uuid)
        order_article_no = ET.SubElement(order_part, "ArticleNo")
        order_article_no.text = "Order"

        # SubItems for order
        sub_items = ET.SubElement(order_part, "SubItems")
        sub_item = ET.SubElement(sub_items, "SubItem")
        sub_article_uuid = ET.SubElement(sub_item, "ArticleUuid")
        sub_article_uuid.text = part_uuid
        sub_quantity = ET.SubElement(sub_item, "Quantity")
        sub_quantity.text = "1"

        # Manufacturing part
        part = ET.SubElement(parts, "Part")
        part.set("Uuid", part_uuid)
        part_article_no = ET.SubElement(part, "ArticleNo")
        part_article_no.text = part_name

        # Raw material
        raw_material = ET.SubElement(part, "RawMaterialName")
        raw_material.text = material.name

        # Working plan
        working_plan = ET.SubElement(part, "WorkingPlan")
        working_steps = ET.SubElement(working_plan, "WorkingSteps")

        # Add working steps
        for working_place in working_places:
            working_step = ET.SubElement(working_steps, "WorkingStep")

            work_step_name = ET.SubElement(working_step, "WorkStepName")
            work_step_name.text = working_place.name

            target_setup_time = ET.SubElement(working_step, "TargetSetupTime")
            target_setup_time.text = working_place.setup_time

            # Resources
            resources = ET.SubElement(working_step, "Resources")
            resource = ET.SubElement(resources, "Resource")
            resource_material = ET.SubElement(resource, "RawMaterialName")
            resource_material.text = material.name

            # Parameters (if any)
            if working_place.parameters:
                parameters = ET.SubElement(working_step, "Parameters")
                for param_name, param_value in working_place.parameters.items():
                    parameter = ET.SubElement(parameters, "Parameter")
                    name = ET.SubElement(parameter, "Name")
                    name.text = f"{working_place.name}.{param_name}"
                    value = ET.SubElement(parameter, "Value")
                    value.text = str(param_value)
            else:
                # Empty parameters node
                ET.SubElement(working_step, "Parameters")

        # Technology
        technology = ET.SubElement(part, "Technology")
        cad_filename = ET.SubElement(technology, "CADFileName")
        cad_filename.text = dxf_file

        return self._prettify_xml(doc)

    def _prettify_xml(self, elem: ET.Element) -> str:
        """Return a pretty-printed XML string"""
        rough_string = ET.tostring(elem, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        # Add XML declaration
        return '<?xml version="1.0" encoding="UTF-8"?>\n' + '\n'.join(reparsed.toprettyxml(indent="  ").split('\n')[1:])

    def generate_calculations(self,
                              dxf_files: List[str],
                              materials: List[Material],
                              working_places_sets: List[List[WorkingPlace]],
                              output_dir: str = "calculations") -> List[str]:
        """
        Generate calculation files for all combinations

        Args:
            dxf_files: List of DXF file paths
            materials: List of materials
            working_places_sets: List of working place sequences
            output_dir: Output directory for generated files

        Returns:
            List of generated file paths
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        generated_files = []

        # Generate all combinations
        for i, (dxf_file, material, working_places) in enumerate(
                itertools.product(dxf_files, materials, working_places_sets)
        ):
            part_name = Path(dxf_file).stem
            filename = f"calc_{i + 1:04d}_{part_name}_{material.name.replace('.', '_')}.cprj"
            filepath = output_path / filename

            # Generate XML content
            xml_content = self.create_calculation_xml(
                dxf_file=dxf_file,
                material=material,
                working_places=working_places,
                part_name=part_name
            )

            # Write to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(xml_content)

            generated_files.append(str(filepath))
            print(f"Generated: {filename}")

        return generated_files

    def create_batch_file(self,
                          calculation_files: List[str],
                          output_dir: str = "results",
                          batch_filename: str = "runcalc.cbat") -> str:
        """
        Create a batch file (.cbat) for running multiple calculations

        Args:
            calculation_files: List of calculation file paths
            output_dir: Output directory for results
            batch_filename: Name of the batch file

        Returns:
            Path to the created batch file
        """
        # Create root element
        auto_calc = ET.Element("AutoCalculation")
        auto_calc.set("type", "batch_normal")

        # General settings
        general = ET.SubElement(auto_calc, "General")
        output_dir_elem = ET.SubElement(general, "OutputDir")
        output_dir_elem.text = output_dir

        # Add calculations
        for calc_file in calculation_files:
            calculation = ET.SubElement(auto_calc, "Calculation")
            calc_file_elem = ET.SubElement(calculation, "CalculationFile")
            calc_file_elem.text = calc_file

        # Generate XML content
        xml_content = self._prettify_xml(auto_calc)

        # Write batch file
        with open(batch_filename, 'w', encoding='utf-8') as f:
            f.write(xml_content)

        print(f"Created batch file: {batch_filename}")
        return batch_filename


def main():
    """Example usage of the TruTops Calculate Generator"""

    # Configuration
    config = CalculationConfig(
        measure_system=1,  # metric
        base_currency="EUR",
        batch_report_type=1
    )

    # Create generator
    generator = TruTopsCalculateGenerator(config)

    # NEW: Get DXF files from folder instead of manual list
    dxf_folder = r"C:\Users\r_ste.MSI\Documents\UOC\TFM\Datos_Sinteticos\Generador_Piezas_Dxf\Dataset_Piezas_Sinteticas_y_Anonimizadas"
    dxf_files = generator.get_dxf_files_from_folder(dxf_folder, recursive=False)

    if not dxf_files:
        print("No DXF files found! Exiting.")
        return

    # Materials to test

    materials = [
        Material("St37-15"),
        Material("St37-40"),
        Material("St37-14"),
        Material("St37-30"),
        Material("St37-80"),
        Material("GALVA-15"),
        Material("St37-9"),
        Material("GALVA-30"),
        Material("St37-7"),
        Material("1.4301-40"),
        Material("St37-11"),
        Material("St37-18"),
        Material("GALVA-20"),
        Material("St37-20"),
        Material("St37-60"),
        Material("St37-50"),
        Material("1.4301-80"),
        Material("1.4301-20"),
        Material("1.4301-30")
    ]

    # Define working places with parameters
    laser_cutting = WorkingPlace(
        name="TruLaser 3030",
        setup_time="00:05:00"
    )

    #TruLaser 1030 Lean Edition (L111) 6KW
    #TruLaser 3030 (L20) 6KW
    bending = WorkingPlace(
        name="Biegen",
        setup_time="00:10:00",
        parameters={
            "TimePickUpPart": 1,
            "TimeBetweenBends": 0.5,
            "TimeBend": 0.2,
            "TimeProgramTest": 5
        }
    )

    welding = WorkingPlace(
        name="Schweissen",
        setup_time="00:15:00"
    )

    # Different working place sequences
    working_places_sets = [
        [laser_cutting],  # Only laser cutting
        # [laser_cutting, bending],  # Laser + bending
        # [laser_cutting, bending, welding]  # Full process
    ]

    output_dir = r"C:\Users\r_ste.MSI\Documents\UOC\TFM\Datos_Sinteticos\PythonBatchCalculate\Calculos_Finales"
    # Generate calculations
    print("\nGenerating calculation files...")
    generated_files = generator.generate_calculations(
        dxf_files=dxf_files,
        materials=materials,
        working_places_sets=working_places_sets,
        output_dir=output_dir
    )

    print(f"\nGenerated {len(generated_files)} calculation files")

    # Create batch file
    print("\nCreating batch file...")
    batch_file = generator.create_batch_file(
        calculation_files=generated_files,
        output_dir="calculations/Results",
        batch_filename="runcalc.cbat"
    )


    print(f"\nTo run the calculations, execute:")
    print(fr"C:\Program Files\TRUMPF\TruTops Calculate\bin\TruTopsCalculate.exe {output_dir}\runcalc.cbat")


if __name__ == "__main__":
    main()