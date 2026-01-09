#!/usr/bin/env python3
"""
TruTops Calculate Result Parser - Multi-Part Version

This script reads TruTops Calculate result XML files and extracts key information
into a summarized CSV table. Now supports files with multiple parts.
"""

import os
import csv
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import re


@dataclass
class CalculationSummary:
    """Summary data extracted from calculation results"""
    # File identification
    filename: str = ""
    part_id: str = ""  # Added to track which part in multi-part files
    article_no: str = ""
    article_description: str = ""

    # Part information
    part_dimensions_x: float = 0.0  # mm
    part_dimensions_y: float = 0.0  # mm
    part_weight: float = 0.0  # kg
    part_area: float = 0.0  # mm²
    cutting_length: float = 0.0  # mm

    # Material information
    material_name: str = ""
    material_thickness: float = 0.0  # mm
    material_cost_per_kg: float = 0.0  # EUR/kg

    # Working place information
    machine_name: str = ""
    machine_hour_cost: float = 0.0  # EUR/h
    operator_hour_cost: float = 0.0  # EUR/h
    overhead_rate: float = 0.0  # EUR/h

    # Processing times
    laser_time: str = "00:00:00"  # hh:mm:ss
    positioning_time: str = "00:00:00"  # hh:mm:ss
    setup_time: str = "00:00:00"  # hh:mm:ss
    pallet_changing_time: str = "00:00:00"  # hh:mm:ss
    total_processing_time: str = "00:00:00"  # hh:mm:ss

    # Energy and gas consumption
    power_consumption_kwh: float = 0.0  # kWh
    electricity_cost_per_kwh: float = 0.0  # EUR/kWh
    electricity_cost_total: float = 0.0  # EUR

    compressed_air_consumption: float = 0.0  # Nm³
    compressed_air_cost_per_nm3: float = 0.0  # EUR/Nm³
    compressed_air_cost_total: float = 0.0  # EUR

    oxygen_consumption: float = 0.0  # Nm³
    oxygen_cost_per_nm3: float = 0.0  # EUR/Nm³
    oxygen_cost_total: float = 0.0  # EUR

    nitrogen_consumption: float = 0.0  # Nm³
    nitrogen_cost_per_nm3: float = 0.0  # EUR/Nm³
    nitrogen_cost_total: float = 0.0  # EUR

    argon_consumption: float = 0.0  # Nm³
    argon_cost_per_nm3: float = 0.0  # EUR/Nm³
    argon_cost_total: float = 0.0  # EUR

    # Nesting information
    sheet_dimensions_x: float = 0.0  # mm
    sheet_dimensions_y: float = 0.0  # mm
    parts_per_sheet: int = 0
    material_utilization: float = 0.0  # %
    waste_percentage: float = 0.0  # %
    material_consumption: float = 0.0  # m²

    # Cost breakdown
    net_cost_per_piece: float = 0.0  # EUR
    gross_cost_per_piece: float = 0.0  # EUR
    material_cost_per_piece: float = 0.0  # EUR
    processing_cost_per_piece: float = 0.0  # EUR

    # Scale prices
    cost_qty_1: float = 0.0  # EUR for quantity 1
    cost_qty_10: float = 0.0  # EUR for quantity 10
    cost_qty_100: float = 0.0  # EUR for quantity 100
    cost_qty_500: float = 0.0  # EUR for quantity 500

    # Additional information
    currency: str = "EUR"
    calculation_date: str = ""
    author_version: str = ""


class TruTopsResultParser:
    """Parser for TruTops Calculate result XML files"""

    def __init__(self):
        self.namespaces = {}

    def parse_time_string(self, time_str: str) -> str:
        """Parse time string and return in HH:MM:SS format"""
        if not time_str:
            return "00:00:00"

        if ":" in time_str:
            return time_str.split(".")[0]

        return "00:00:00"

    def parse_float_value(self, element: ET.Element, default: float = 0.0) -> float:
        """Safely parse float value from XML element"""
        if element is None:
            return default

        text = element.text
        if not text:
            return default

        try:
            cleaned = re.sub(r'[^\d.,\-]', '', text.replace(',', '.'))
            return float(cleaned) if cleaned else default
        except (ValueError, TypeError):
            return default

    def time_string_to_hours(self, time_str: str) -> float:
        """Convert time string HH:MM:SS to decimal hours"""
        if not time_str or time_str == "00:00:00":
            return 0.0

        try:
            parts = time_str.split(":")
            if len(parts) >= 3:
                hours = float(parts[0])
                minutes = float(parts[1])
                seconds = float(parts[2].split(".")[0])
                return hours + (minutes / 60.0) + (seconds / 3600.0)
            return 0.0
        except:
            return 0.0

    def extract_scale_prices(self, part: ET.Element) -> Dict[str, float]:
        """Extract scale prices for different quantities from a part"""
        scale_prices = {}

        scale_entries = part.findall(".//ScalePriceEntry")
        for entry in scale_entries:
            qty_elem = entry.find(".//Quantity")
            cost_elem = entry.find(".//NetcostsAPiece")

            if qty_elem is not None and cost_elem is not None:
                try:
                    qty = int(float(self.parse_float_value(qty_elem)))
                    cost = self.parse_float_value(cost_elem)
                    scale_prices[f"qty_{qty}"] = cost
                except:
                    continue

        return scale_prices

    def calculate_energy_and_gas_consumption(self, root: ET.Element, part: ET.Element, summary: CalculationSummary):
        """Calculate energy and gas consumption based on processing times and rates"""

        # Get operator costs and rates from OrderData
        operator = root.find(".//OrderData/Operator")
        if operator is not None:
            elec_cost = operator.find(".//ElectricEnergyCosts/metric_qty")
            if elec_cost is not None:
                summary.electricity_cost_per_kwh = self.parse_float_value(elec_cost)

            compressed_air = operator.find(".//CompressedAir/Costs/metric_qty")
            if compressed_air is not None:
                summary.compressed_air_cost_per_nm3 = self.parse_float_value(compressed_air)

            oxygen = operator.find(".//Oxygen/Costs/metric_qty")
            if oxygen is not None:
                summary.oxygen_cost_per_nm3 = self.parse_float_value(oxygen)

            nitrogen = operator.find(".//Nitrogen/Costs/metric_qty")
            if nitrogen is not None:
                summary.nitrogen_cost_per_nm3 = self.parse_float_value(nitrogen)

            argon = operator.find(".//Argon/Costs/metric_qty")
            if argon is not None:
                summary.argon_cost_per_nm3 = self.parse_float_value(argon)

        # Get laser machine data for power consumption
        laser_machine = part.find(".//LaserMachine")
        if laser_machine is not None:
            power_100 = laser_machine.find(".//Power100Percent")
            power_1 = laser_machine.find(".//Power1Percent")

            if power_100 is not None and power_1 is not None:
                max_power_kw = self.parse_float_value(power_100)
                min_power_kw = self.parse_float_value(power_1)

                working_step = part.find(".//WorkingStep")
                if working_step is not None:
                    time_data = working_step.find(".//TargetProcessingTimeData")
                    if time_data is not None:
                        laser_time_elem = time_data.find(".//LaserTime")
                        if laser_time_elem is not None:
                            laser_time_str = laser_time_elem.text or "00:00:00"
                            laser_hours = self.time_string_to_hours(laser_time_str)

                            avg_power_kw = (max_power_kw + min_power_kw) / 2
                            summary.power_consumption_kwh = avg_power_kw * laser_hours
                            summary.electricity_cost_total = summary.power_consumption_kwh * summary.electricity_cost_per_kwh

        # Estimate gas consumption
        if summary.laser_time and summary.laser_time != "00:00:00":
            laser_hours = self.time_string_to_hours(summary.laser_time)

            if laser_hours > 0:
                summary.compressed_air_consumption = laser_hours * 10.0
                summary.compressed_air_cost_total = summary.compressed_air_consumption * summary.compressed_air_cost_per_nm3

                material_thickness = summary.material_thickness

                if "stainless" in summary.material_name.lower() or "1.43" in summary.material_name:
                    nitrogen_rate = max(0.5, min(3.0, material_thickness * 0.3))
                    summary.nitrogen_consumption = laser_hours * nitrogen_rate
                    summary.nitrogen_cost_total = summary.nitrogen_consumption * summary.nitrogen_cost_per_nm3
                elif "carbon" in summary.material_name.lower() or material_thickness < 3.0:
                    oxygen_rate = max(0.3, min(2.0, material_thickness * 0.2))
                    summary.oxygen_consumption = laser_hours * oxygen_rate
                    summary.oxygen_cost_total = summary.oxygen_consumption * summary.oxygen_cost_per_nm3

    def parse_single_part(self, root: ET.Element, part: ET.Element, filename: str) -> CalculationSummary:
        """Parse a single part from the XML"""
        summary = CalculationSummary()
        summary.filename = filename

        # Part ID
        summary.part_id = part.get("ID", "")

        # Basic file information (from root)
        datetime_elem = root.find(".//datetime")
        if datetime_elem is not None:
            summary.calculation_date = datetime_elem.text or ""

        author_elem = root.find(".//author")
        if author_elem is not None:
            summary.author_version = author_elem.get("authorversion", "")

        # Currency information
        options = root.find(".//Options")
        if options is not None:
            summary.currency = options.get("BaseCurrency", "EUR")

        # Article information
        article_no = part.find(".//ArticleNo")
        if article_no is not None:
            summary.article_no = article_no.text or ""

        desc_elem = part.find(".//ArticleDescription")
        if desc_elem is not None:
            summary.article_description = desc_elem.text or ""

        # Material information
        material_elem = part.find(".//Material")
        if material_elem is not None:
            mat_name = material_elem.find(".//MaterialName")
            if mat_name is not None:
                summary.material_name = mat_name.text or ""

            thickness = material_elem.find(".//MaterialThickness")
            if thickness is not None:
                summary.material_thickness = self.parse_float_value(thickness)

        # Material costs
        cost_elem = part.find(".//BasicMaterialGroupCosts/metric_qty")
        if cost_elem is not None:
            summary.material_cost_per_kg = self.parse_float_value(cost_elem)

        # Part information
        part_info = part.find(".//PartInformation")
        if part_info is not None:
            size_x = part_info.find(".//SizeX")
            if size_x is not None:
                summary.part_dimensions_x = self.parse_float_value(size_x)

            size_y = part_info.find(".//SizeY")
            if size_y is not None:
                summary.part_dimensions_y = self.parse_float_value(size_y)

            weight = part_info.find(".//PartWeight")
            if weight is not None:
                summary.part_weight = self.parse_float_value(weight)

            area = part_info.find(".//PartArea")
            if area is not None:
                summary.part_area = self.parse_float_value(area)

            cutting = part_info.find(".//CuttingLength")
            if cutting is not None:
                summary.cutting_length = self.parse_float_value(cutting)

        # FALLBACK: Si SizeX/SizeY son 0, buscar en ApproxGeometry
        if summary.part_dimensions_x == 0.0 or summary.part_dimensions_y == 0.0:
            approx_geom = part.find(".//ApproxGeometry/outside/contour")
            if approx_geom is not None:
                param3 = approx_geom.find(".//parameter_3/val")
                param4 = approx_geom.find(".//parameter_4/val")
                if param3 is not None and summary.part_dimensions_x == 0.0:
                    summary.part_dimensions_x = self.parse_float_value(param3)
                if param4 is not None and summary.part_dimensions_y == 0.0:
                    summary.part_dimensions_y = self.parse_float_value(param4)
                    
        # Working step information
        working_step = part.find(".//WorkingStep")
        if working_step is not None:
            workplace = working_step.find(".//WorkStepName")
            if workplace is not None:
                summary.machine_name = workplace.text or ""

            workplace_data = working_step.find(".//WorkPlaceData")
            if workplace_data is not None:
                machine_cost = workplace_data.find(".//MachineHourCosts/Value/metric_qty")
                if machine_cost is not None:
                    summary.machine_hour_cost = self.parse_float_value(machine_cost)

                operator_cost = workplace_data.find(".//HourlyRate/Value/metric_qty")
                if operator_cost is not None:
                    summary.operator_hour_cost = self.parse_float_value(operator_cost)

                overhead = workplace_data.find(".//OverheadRate/metric_qty")
                if overhead is not None:
                    summary.overhead_rate = self.parse_float_value(overhead)

            # Processing times
            time_data = working_step.find(".//TargetProcessingTimeData")
            if time_data is not None:
                laser_time = time_data.find(".//LaserTime")
                if laser_time is not None:
                    summary.laser_time = self.parse_time_string(laser_time.text)

                pos_time = time_data.find(".//PositioningTime")
                if pos_time is not None:
                    summary.positioning_time = self.parse_time_string(pos_time.text)

                setup_time = time_data.find(".//SetupTime")
                if setup_time is not None:
                    summary.setup_time = self.parse_time_string(setup_time.text)

                pallet_changing_time = time_data.find(".//PalletChangingTime")
                if pallet_changing_time is not None:
                    summary.pallet_changing_time = self.parse_time_string(pallet_changing_time.text)

            proc_time = working_step.find(".//TargetProcessingTime")
            if proc_time is not None:
                summary.total_processing_time = self.parse_time_string(proc_time.text)

        # Cost information
        sales_prices = part.find(".//SalesPrices/OrderPrice")
        if sales_prices is not None:
            net_cost = sales_prices.find(".//NetcostsAPiece")
            if net_cost is not None:
                summary.net_cost_per_piece = self.parse_float_value(net_cost)

            gross_cost = sales_prices.find(".//GrosscostsAPiece")
            if gross_cost is not None:
                summary.gross_cost_per_piece = self.parse_float_value(gross_cost)

        # Scale prices
        scale_prices = self.extract_scale_prices(part)
        summary.cost_qty_1 = scale_prices.get("qty_1", summary.net_cost_per_piece)
        summary.cost_qty_10 = scale_prices.get("qty_10", 0.0)
        summary.cost_qty_100 = scale_prices.get("qty_100", 0.0)
        summary.cost_qty_500 = scale_prices.get("qty_500", 0.0)

        # Calculate energy and gas consumption
        self.calculate_energy_and_gas_consumption(root, part, summary)

        # Nesting information (from root)
        nesting = root.find(".//nesting")
        if nesting is not None:
            allocation = nesting.find(".//allocation")
            if allocation is not None:
                sheet_id = allocation.get("sheet-id", "")
                if "x" in sheet_id:
                    parts = sheet_id.split("x")
                    if len(parts) >= 3:
                        try:
                            summary.sheet_dimensions_x = float(parts[-2])
                            summary.sheet_dimensions_y = float(parts[-1])
                        except:
                            pass

                positions = allocation.findall(".//pos")
                summary.parts_per_sheet = len(positions)

        sheet_data = root.find(".//sheetData")
        if sheet_data is not None:
            consumption = sheet_data.find(".//materialConsumption/value")
            if consumption is not None:
                summary.material_consumption = self.parse_float_value(consumption)

        waste_elem = root.find(".//waste/value")
        if waste_elem is not None:
            summary.waste_percentage = self.parse_float_value(waste_elem)
            summary.material_utilization = 100.0 - summary.waste_percentage

        return summary

    def parse_calculation_file(self, filepath: str) -> List[CalculationSummary]:
        """Parse a calculation result file and return a list of summaries (one per part)"""
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
            filename = Path(filepath).name

            summaries = []

            # Find all manufacturing parts (excluding the root/order part)
            parts = root.findall(".//Part[@type='sheetmetalpart']")

            for part in parts:
                # Skip parts that are orders (root nodes)
                article_no_elem = part.find(".//ArticleNo")
                if article_no_elem is not None:
                    article_no = article_no_elem.text or ""
                    # Skip if it's an order part (common names: "Order", "Pedido", etc.)
                    if article_no.lower() in ["order", "pedido", "auftrag"]:
                        continue

                # Check if the part has ProcessingTechnology="NONE" which indicates root
                proc_tech = part.get("ProcessingTechnology", "")
                if proc_tech == "NONE":
                    continue

                # Parse this part
                summary = self.parse_single_part(root, part, filename)

                # Only add if it has some useful data
                if summary.article_no or summary.net_cost_per_piece > 0:
                    summaries.append(summary)

            return summaries

        except Exception as e:
            print(f"Error parsing file {filepath}: {e}")
            return []

    def parse_multiple_files(self, file_paths: List[str]) -> List[CalculationSummary]:
        """Parse multiple calculation result files"""
        summaries = []

        for filepath in file_paths:
            if os.path.exists(filepath):
                file_summaries = self.parse_calculation_file(filepath)
                summaries.extend(file_summaries)
            else:
                print(f"File not found: {filepath}")

        return summaries

    def export_to_csv(self, summaries: List[CalculationSummary], output_file: str = "calculation_summary.csv"):
        """Export summaries to CSV file"""
        if not summaries:
            print("No data to export")
            return

        fieldnames = [
            'filename', 'part_id', 'article_no', 'article_description',
            'part_dimensions_x_mm', 'part_dimensions_y_mm', 'part_weight_kg', 'part_area_mm2', 'cutting_length_mm',
            'material_name', 'material_thickness_mm', 'material_cost_per_kg_eur',
            'machine_name', 'machine_hour_cost_eur', 'operator_hour_cost_eur', 'overhead_rate_eur',
            'laser_time', 'positioning_time', 'setup_time','pallet_changing_time', 'total_processing_time',
            'power_consumption_kwh', 'electricity_cost_per_kwh_eur', 'electricity_cost_total_eur',
            'compressed_air_consumption_nm3', 'compressed_air_cost_per_nm3_eur', 'compressed_air_cost_total_eur',
            'oxygen_consumption_nm3', 'oxygen_cost_per_nm3_eur', 'oxygen_cost_total_eur',
            'nitrogen_consumption_nm3', 'nitrogen_cost_per_nm3_eur', 'nitrogen_cost_total_eur',
            'argon_consumption_nm3', 'argon_cost_per_nm3_eur', 'argon_cost_total_eur',
            'sheet_dimensions_x_mm', 'sheet_dimensions_y_mm', 'parts_per_sheet',
            'material_utilization_percent', 'waste_percent', 'material_consumption_m2',
            'net_cost_per_piece_eur', 'gross_cost_per_piece_eur',
            'cost_qty_1_eur', 'cost_qty_10_eur', 'cost_qty_100_eur', 'cost_qty_500_eur',
            'currency', 'calculation_date', 'author_version'
        ]

        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for summary in summaries:
                row = {
                    'filename': summary.filename,
                    'part_id': summary.part_id,
                    'article_no': summary.article_no,
                    'article_description': summary.article_description,
                    'part_dimensions_x_mm': summary.part_dimensions_x,
                    'part_dimensions_y_mm': summary.part_dimensions_y,
                    'part_weight_kg': summary.part_weight,
                    'part_area_mm2': summary.part_area,
                    'cutting_length_mm': summary.cutting_length,
                    'material_name': summary.material_name,
                    'material_thickness_mm': summary.material_thickness,
                    'material_cost_per_kg_eur': summary.material_cost_per_kg,
                    'machine_name': summary.machine_name,
                    'machine_hour_cost_eur': summary.machine_hour_cost,
                    'operator_hour_cost_eur': summary.operator_hour_cost,
                    'overhead_rate_eur': summary.overhead_rate,
                    'laser_time': summary.laser_time,
                    'positioning_time': summary.positioning_time,
                    'setup_time': summary.setup_time,
                    'pallet_changing_time': summary.pallet_changing_time,
                    'total_processing_time': summary.total_processing_time,
                    'power_consumption_kwh': summary.power_consumption_kwh,
                    'electricity_cost_per_kwh_eur': summary.electricity_cost_per_kwh,
                    'electricity_cost_total_eur': summary.electricity_cost_total,
                    'compressed_air_consumption_nm3': summary.compressed_air_consumption,
                    'compressed_air_cost_per_nm3_eur': summary.compressed_air_cost_per_nm3,
                    'compressed_air_cost_total_eur': summary.compressed_air_cost_total,
                    'oxygen_consumption_nm3': summary.oxygen_consumption,
                    'oxygen_cost_per_nm3_eur': summary.oxygen_cost_per_nm3,
                    'oxygen_cost_total_eur': summary.oxygen_cost_total,
                    'nitrogen_consumption_nm3': summary.nitrogen_consumption,
                    'nitrogen_cost_per_nm3_eur': summary.nitrogen_cost_per_nm3,
                    'nitrogen_cost_total_eur': summary.nitrogen_cost_total,
                    'argon_consumption_nm3': summary.argon_consumption,
                    'argon_cost_per_nm3_eur': summary.argon_cost_per_nm3,
                    'argon_cost_total_eur': summary.argon_cost_total,
                    'sheet_dimensions_x_mm': summary.sheet_dimensions_x,
                    'sheet_dimensions_y_mm': summary.sheet_dimensions_y,
                    'parts_per_sheet': summary.parts_per_sheet,
                    'material_utilization_percent': summary.material_utilization,
                    'waste_percent': summary.waste_percentage,
                    'material_consumption_m2': summary.material_consumption,
                    'net_cost_per_piece_eur': summary.net_cost_per_piece,
                    'gross_cost_per_piece_eur': summary.gross_cost_per_piece,
                    'cost_qty_1_eur': summary.cost_qty_1,
                    'cost_qty_10_eur': summary.cost_qty_10,
                    'cost_qty_100_eur': summary.cost_qty_100,
                    'cost_qty_500_eur': summary.cost_qty_500,
                    'currency': summary.currency,
                    'calculation_date': summary.calculation_date,
                    'author_version': summary.author_version
                }
                writer.writerow(row)

        print(f"Exported {len(summaries)} part summaries to {output_file}")

    def process_directory(self, directory: str, pattern: str = "*.cprj", output_file: str = "calculation_summary.csv"):
        """Process all calculation files in a directory and subdirectories"""
        dir_path = Path(directory)
        if not dir_path.exists():
            print(f"Directory not found: {directory}")
            return

        found_files = list(dir_path.rglob(pattern))
        if not found_files:
            print(f"No files matching '{pattern}' found in {directory}")
            return

        print(f"Found {len(found_files)} files matching '{pattern}'")

        # Parse all files
        summaries = self.parse_multiple_files([str(f) for f in found_files])

        if not summaries:
            print("No files contained valid calculation results.")
            return

        # Export to CSV
        self.export_to_csv(summaries, output_file)

        # Print statistics
        print(f"\nProcessed {len(summaries)} parts from {len(found_files)} files")

        # Count parts per file
        files_with_parts = {}
        for s in summaries:
            files_with_parts[s.filename] = files_with_parts.get(s.filename, 0) + 1

        multi_part_files = [f for f, count in files_with_parts.items() if count > 1]
        if multi_part_files:
            print(f"Multi-part files detected: {len(multi_part_files)} files")
            for f in multi_part_files[:5]:  # Show first 5
                print(f"  {f}: {files_with_parts[f]} parts")

        return summaries


def main():
    """Example usage of the multi-part result parser"""
    parser = TruTopsResultParser()

    results_dir = r"C:\Users\r_ste.MSI\Documents\UOC\TFM\Datos_Sinteticos\PythonBatchCalculate\Calculos_Finales\Results"

    for directory in [results_dir, "calculations"]:
        if os.path.exists(directory):
            print(f"Processing directory: {directory}")
            summaries = parser.process_directory(
                directory=directory,
                pattern="*.cprj",
                output_file=r"C:\Users\r_ste.MSI\Documents\UOC\TFM\Datos_Sinteticos\PythonBatchCalculate\Calculos_Finales\Results\calculation_summary.csv"
            )

            if summaries:
                costs = [s.net_cost_per_piece for s in summaries if s.net_cost_per_piece > 0]
                avg_cost = sum(costs) / len(costs) if costs else 0

                print(f"- Total parts: {len(summaries)}")
                print(f"- Parts with cost data: {len(costs)}")
                print(f"- Average cost per piece: {avg_cost:.2f} EUR")
                break
        else:
            print(f"Directory not found: {directory}")


if __name__ == "__main__":
    main()