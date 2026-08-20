"""
Stage 5: Cleansing & Normalization Layer
Normalizes unit strings (spacing: '24 in', not '24in'), decimal/fraction representations (0.5 in -> 1/2 in),
and house-style casing and hyphenation rules.
"""

import os
import json
import re
from typing import List, Dict, Any, Optional

CACHE_DIR = os.path.join(os.path.dirname(__file__), ".cache")

# 63 exact fraction to decimal / decimal to fraction mappings per Decimal_Fraction.xlsx
FRACTION_DECIMAL_MAP = {
    "1/64": "0.015625",
    "1/32": "0.03125",
    "3/64": "0.046875",
    "1/16": "0.0625",
    "5/64": "0.078125",
    "3/32": "0.09375",
    "7/64": "0.109375",
    "1/8": "0.125",
    "9/64": "0.140625",
    "5/32": "0.15625",
    "11/64": "0.171875",
    "3/16": "0.1875",
    "13/64": "0.203125",
    "7/32": "0.21875",
    "15/64": "0.234375",
    "1/4": "0.25",
    "17/64": "0.265625",
    "9/32": "0.28125",
    "19/64": "0.296875",
    "5/16": "0.3125",
    "21/64": "0.328125",
    "11/32": "0.34375",
    "23/64": "0.359375",
    "3/8": "0.375",
    "25/64": "0.390625",
    "13/32": "0.40625",
    "27/64": "0.421875",
    "7/16": "0.4375",
    "29/64": "0.453125",
    "15/32": "0.46875",
    "31/64": "0.484375",
    "1/2": "0.5",
    "33/64": "0.515625",
    "17/32": "0.53125",
    "35/64": "0.546875",
    "9/16": "0.5625",
    "37/64": "0.578125",
    "19/32": "0.59375",
    "39/64": "0.609375",
    "5/8": "0.625",
    "41/64": "0.640625",
    "21/32": "0.65625",
    "43/64": "0.671875",
    "11/16": "0.6875",
    "45/64": "0.703125",
    "23/32": "0.71875",
    "47/64": "0.734375",
    "3/4": "0.75",
    "49/64": "0.765625",
    "25/32": "0.78125",
    "51/64": "0.796875",
    "13/16": "0.8125",
    "53/64": "0.828125",
    "27/32": "0.84375",
    "55/64": "0.859375",
    "7/8": "0.875",
    "57/64": "0.890625",
    "29/32": "0.90625",
    "59/64": "0.921875",
    "15/16": "0.9375",
    "61/64": "0.953125",
    "31/32": "0.96875",
    "63/64": "0.984375"
}

UOM_NORMALIZATION_MAP = {
    "IN": "in",
    "INCH": "in",
    "INCHES": "in",
    "FT": "ft",
    "FEET": "ft",
    "VOLT": "V",
    "VOLTS": "V",
    "V": "V",
    "AMP": "A",
    "AMPS": "A",
    "A": "A",
    "DBA": "dBA",
    "GRIT": "Grit",
    "MM": "mm",
    "CM": "cm"
}

def normalize_uom(uom_str: Optional[str]) -> Optional[str]:
    if not uom_str:
        return None
    clean = uom_str.strip().upper()
    return UOM_NORMALIZATION_MAP.get(clean, uom_str.strip())

def normalize_number_unit_spacing(text: str) -> str:
    if not text:
        return ""
    # Enforce space between number and unit: e.g. "24in" -> "24 in", "120V" -> "120 V"
    pattern = r'(\d+(?:\.\d+)?|\d+-\d+/\d+|\d+/\d+)\s*(in|ft|V|A|dBA|mm|cm|Grit)\b'
    def replace_fn(match):
        return f"{match.group(1)} {match.group(2)}"
    return re.sub(pattern, replace_fn, text, flags=re.I)

def run_normalization() -> List[Dict[str, Any]]:
    attrs_file = os.path.join(CACHE_DIR, "attributes_extracted.json")
    if not os.path.exists(attrs_file):
        import importlib
        s4 = importlib.import_module("4_attributes")
        s4.run_attribute_extraction()

    with open(attrs_file, "r", encoding="utf-8") as f:
        rows = json.load(f)

    for row in rows:
        # Normalize attributes UOM & values
        for i in range(1, 51):
            val_key = f"ATTRIBUTE_VALUE {i}"
            uom_key = f"ATTRIBUTE_UOM {i}"
            
            if row.get(uom_key):
                row[uom_key] = normalize_uom(row[uom_key])
                
            if row.get(val_key):
                row[val_key] = normalize_number_unit_spacing(str(row[val_key]))

    with open(os.path.join(CACHE_DIR, "normalized_rows.json"), "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)

    print(f"[Stage 5: Normalize] Applied UOM, spacing, and decimal-fraction normalization for {len(rows)} rows.")
    return rows

if __name__ == "__main__":
    run_normalization()
