"""
Stage 0: Ingestion & Data Cleansing Layer
Loads raw sample dataset and delivery format template/ground truth.
Applies Hard Constraint #1: Nullifies placeholder strings like '-- Unbranded --', '-- No Unilog Brand --', '-- No DIB Brand --', '-- No X --', '-', etc.
"""

import os
import json
import csv
import re
from typing import Dict, List, Any, Optional

INPUT_FILE = os.path.join(os.path.dirname(__file__), "Unihack_ Sample Dataset - Input.csv")
EXPECTED_OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "Unihack_ Expected Output - Delivery Format.csv")
CACHE_DIR = os.path.join(os.path.dirname(__file__), ".cache")

PLACEHOLDER_PATTERNS = [
    r"^--\s*Unbranded\s*--$",
    r"^--\s*No\s+.*Brand\s*--$",
    r"^--\s*No\s+.*--$",
    r"^-\s*$",
    r"^null$",
    r"^none$",
    r"^nan$",
    r"^n/a$",
    r"^\s*$"
]

def is_placeholder_null(val: Optional[str]) -> bool:
    if val is None:
        return True
    s = str(val).strip()
    for pattern in PLACEHOLDER_PATTERNS:
        if re.match(pattern, s, re.IGNORECASE):
            return True
    return False

def clean_value(val: Optional[str]) -> Optional[str]:
    if is_placeholder_null(val):
        return None
    return str(val).strip()

def clean_row(row: Dict[str, Any]) -> Dict[str, Any]:
    cleaned = {}
    for k, v in row.items():
        cleaned[k] = clean_value(v)
    return cleaned

def load_raw_dataset() -> List[Dict[str, Any]]:
    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(f"Input dataset not found at {INPUT_FILE}")
    
    cleaned_rows = []
    with open(INPUT_FILE, mode="r", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            c_row = clean_row(row)
            c_row["_row_id"] = idx
            cleaned_rows.append(c_row)
            
    return cleaned_rows

def load_delivery_format_columns() -> List[str]:
    if not os.path.exists(EXPECTED_OUTPUT_FILE):
        raise FileNotFoundError(f"Delivery format file not found at {EXPECTED_OUTPUT_FILE}")
        
    with open(EXPECTED_OUTPUT_FILE, mode="r", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.reader(f)
        headers = next(reader)
        return [h.strip() for h in headers]

def load_ground_truth_rows() -> List[Dict[str, Any]]:
    if not os.path.exists(EXPECTED_OUTPUT_FILE):
        return []
    rows = []
    with open(EXPECTED_OUTPUT_FILE, mode="r", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            c_row = clean_row(row)
            c_row["_gt_row_id"] = idx
            rows.append(c_row)
    return rows

def run_ingest() -> Dict[str, Any]:
    os.makedirs(CACHE_DIR, exist_ok=True)
    raw_data = load_raw_dataset()
    headers = load_delivery_format_columns()
    gt_rows = load_ground_truth_rows()

    cache_data = {
        "raw_data_count": len(raw_data),
        "delivery_format_columns_count": len(headers),
        "ground_truth_count": len(gt_rows),
        "headers": headers
    }
    
    with open(os.path.join(CACHE_DIR, "ingested_raw.json"), "w", encoding="utf-8") as f:
        json.dump(raw_data, f, indent=2)

    with open(os.path.join(CACHE_DIR, "delivery_headers.json"), "w", encoding="utf-8") as f:
        json.dump(headers, f, indent=2)

    with open(os.path.join(CACHE_DIR, "ground_truth.json"), "w", encoding="utf-8") as f:
        json.dump(gt_rows, f, indent=2)

    print(f"[Stage 0: Ingest] Loaded {len(raw_data)} raw rows, {len(headers)} output columns, {len(gt_rows)} ground truth rows.")
    return cache_data

if __name__ == "__main__":
    run_ingest()
