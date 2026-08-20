"""
Stage 4: Attribute Extraction Layer
Extracts key-value-uom structured attribute triplets from Part_Desc and raw text using regex patterns and rules.
Constrains attributes to canonical LOV names and structures.
"""

import os
import json
import re
from typing import List, Dict, Any, Tuple, Optional

CACHE_DIR = os.path.join(os.path.dirname(__file__), ".cache")

def extract_attributes_from_desc(part_desc: str, mfr_name: str, brand_name: str) -> List[Tuple[str, str, Optional[str]]]:
    """
    Extracts list of (Label, Value, UOM) tuples from product description.
    """
    desc = part_desc or ""
    attrs: List[Tuple[str, str, Optional[str]]] = []
    seen_labels = set()

    def add_attr(label: str, val: str, uom: Optional[str] = None):
        if label not in seen_labels and val:
            attrs.append((label, val.strip(), uom.strip() if uom else None))
            seen_labels.add(label)

    # Series extraction
    if re.search(r"professional series", desc, re.I):
        add_attr("Series", "Professional Series")
    elif re.search(r"eco series", desc, re.I):
        add_attr("Series", "Eco Series")
    elif re.search(r"steel demon", desc, re.I):
        add_attr("Series", "Steel Demon")
    elif re.search(r"speed demon", desc, re.I):
        add_attr("Series", "Speed Demon")

    # Voltage
    vol_match = re.search(r"(\d+)\s*V\b", desc, re.I)
    if vol_match:
        add_attr("Voltage Rating", vol_match.group(1), "V")

    # Amperage
    amp_match = re.search(r"(\d+)\s*A\b", desc, re.I)
    if amp_match:
        add_attr("Amperage Rating", amp_match.group(1), "A")

    # Sound Level
    sound_match = re.search(r"(\d+)\s*dBA\b", desc, re.I)
    if sound_match:
        add_attr("Sound Level", sound_match.group(1), "dBA")

    # Grit
    grit_match = re.search(r"(P\d+|\d+\s*Grit)", desc, re.I)
    if grit_match:
        add_attr("Grit", grit_match.group(1).upper())

    # Dimension / Size patterns like 1/2"x18", 2.75x30, 5"x.045"x7/8"
    dim_match = re.search(r'(\d+(?:[/\.-]\d+)?(?:""|\")?\s*x\s*\.?\d+(?:[/\.-]\d+)?(?:\s*x\s*\d+(?:[/\.-]\d+)?)?(?:""|\")?)', desc)
    if dim_match:
        add_attr("Size", dim_match.group(1))

    # Material
    if re.search(r"stainless steel|ss\b", desc, re.I):
        add_attr("Material", "Stainless Steel")
    elif re.search(r"ceramic", desc, re.I):
        add_attr("Material", "Ceramic")
    elif re.search(r"masonry", desc, re.I):
        add_attr("Material", "Masonry")
    elif re.search(r"metal", desc, re.I):
        add_attr("Material", "Metal")

    # Color
    if re.search(r"\bblack\b|\bbss\b|\bbk\b", desc, re.I):
        add_attr("Color", "Black")
    elif re.search(r"\bwhite\b|\bwh\b", desc, re.I):
        add_attr("Color", "White")
    elif re.search(r"stainless steel|ss\b", desc, re.I):
        add_attr("Color", "Stainless Steel")

    # Mounting Type
    if re.search(r"built-in|built in|bltln", desc, re.I):
        add_attr("Mounting Type", "Built-in")
    elif re.search(r"leg", desc, re.I):
        add_attr("Mounting Type", "Leg")

    return attrs

def run_attribute_extraction() -> List[Dict[str, Any]]:
    classified_file = os.path.join(CACHE_DIR, "classified_rows.json")
    if not os.path.exists(classified_file):
        import importlib
        s3 = importlib.import_module("3_classify")
        s3.run_classification()

    with open(classified_file, "r", encoding="utf-8") as f:
        rows = json.load(f)

    for row in rows:
        part_desc = row.get("Part_Desc") or ""
        mfr_name = row.get("MANUFACTURER_NAME") or ""
        brand_name = row.get("BRAND_NAME") or ""

        extracted = extract_attributes_from_desc(part_desc, mfr_name, brand_name)
        row["extracted_attributes"] = extracted

        # Populate ATTRIBUTE_LABEL n, ATTRIBUTE_VALUE n, ATTRIBUTE_UOM n
        for idx, (label, val, uom) in enumerate(extracted, start=1):
            if idx <= 50:
                row[f"ATTRIBUTE_LABEL {idx}"] = label
                row[f"ATTRIBUTE_VALUE {idx}"] = val
                row[f"ATTRIBUTE_UOM {idx}"] = uom if uom else ""

    with open(os.path.join(CACHE_DIR, "attributes_extracted.json"), "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)

    print(f"[Stage 4: Attributes] Extracted attributes for {len(rows)} rows.")
    return rows

if __name__ == "__main__":
    run_attribute_extraction()
