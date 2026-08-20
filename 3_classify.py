"""
Stage 3: Taxonomy / Classpath Classification Layer
Maps items into canonical Classpath categories based on Part_Desc keywords and model patterns.
Also populates Dept, Class, Fine, and Product Name taxonomy levels.
"""

import os
import json
import re
from typing import List, Dict, Any, Tuple

CACHE_DIR = os.path.join(os.path.dirname(__file__), ".cache")

CLASSIFICATION_RULES = [
    # (Regex pattern on Part_Desc/MANUFACTURER_NAME, Classpath, Dept, Class, Fine, Product Name)
    (
        r"dishwasher",
        "Appliances & Consumer Electronics>Kitchen Appliances>Built-In Dishwashers",
        "Appliances", "Large Appliances", "Dishwashers", "Dishwasher"
    ),
    (
        r"dryer",
        "Appliances & Consumer Electronics>Laundry Appliances>Clothes Dryers",
        "Appliances", "Large Appliances", "Dryers", "Clothes Dryer"
    ),
    (
        r"washer|laundry center",
        "Appliances & Consumer Electronics>Laundry Appliances>Washing Machines",
        "Appliances", "Large Appliances", "Washing Machines", "Washing Machine"
    ),
    (
        r"sanding belt",
        "Abrasives & Polishing>Coated Abrasives>Sanding Belts",
        "Abrasives", "Coated Abrasives", "Sanding Belts", "Sanding Belt"
    ),
    (
        r"cut-off disc|cut off disc|cut off wheel",
        "Abrasives & Polishing>Bonded Abrasives>Cut-Off Wheels",
        "Abrasives", "Bonded Abrasives", "Cut-Off Wheels", "Cut-Off Disc"
    ),
    (
        r"grinding wheel",
        "Abrasives & Polishing>Bonded Abrasives>Grinding Wheels",
        "Abrasives", "Bonded Abrasives", "Grinding Wheels", "Grinding Wheel"
    ),
    (
        r"sanding sponge",
        "Abrasives & Polishing>Coated Abrasives>Sanding Sponges",
        "Abrasives", "Coated Abrasives", "Sanding Sponges", "Sanding Sponge"
    ),
    (
        r"tape",
        "Adhesives, Sealants & Tape>Tape>Specialty Tape",
        "Adhesives & Tapes", "Tape", "Specialty Tape", "Tape"
    ),
    (
        r"fitting|nipple|coupling|elbow|tee|flange",
        "Plumbing>Pipe, Tube & Hose Fittings>Fittings",
        "Plumbing", "Pipe & Tubing", "Fittings", "Fitting"
    ),
    (
        r"faucet",
        "Plumbing>Faucets & Plumbing Accessories>Faucets",
        "Plumbing", "Faucets", "Faucets", "Faucet"
    )
]

DEFAULT_CLASSIFICATION = (
    "Industrial & Commercial Supplies>Hardware>General Hardware",
    "Hardware", "General Hardware", "Hardware Accessories", "Industrial Hardware"
)

def classify_item(part_desc: str, mfr_name: str) -> Tuple[str, str, str, str, str]:
    text = (part_desc or "").lower()
    for pattern, classpath, dept, cls, fine, prod_name in CLASSIFICATION_RULES:
        if re.search(pattern, text):
            return classpath, dept, cls, fine, prod_name
    return DEFAULT_CLASSIFICATION

def run_classification() -> List[Dict[str, Any]]:
    mfr_file = os.path.join(CACHE_DIR, "mfr_brand_resolved.json")
    if not os.path.exists(mfr_file):
        import importlib
        s2 = importlib.import_module("2_manufacturer_brand")
        s2.run_manufacturer_brand_resolution()

    with open(mfr_file, "r", encoding="utf-8") as f:
        rows = json.load(f)

    classified_count = 0
    for row in rows:
        part_desc = row.get("Part_Desc") or ""
        mfr_name = row.get("MANUFACTURER_NAME") or ""

        classpath, dept, cls, fine, prod_name = classify_item(part_desc, mfr_name)

        row["Classpath"] = classpath
        row["Dept"] = dept
        row["Class"] = cls
        row["Fine"] = fine
        row["Product Name"] = prod_name
        classified_count += 1

    with open(os.path.join(CACHE_DIR, "classified_rows.json"), "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)

    print(f"[Stage 3: Classify] Assigned Classpath taxonomy to {classified_count} rows.")
    return rows

if __name__ == "__main__":
    run_classification()
