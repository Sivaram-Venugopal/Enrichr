"""
Stage 7: Validation, Scoring & Confidence Layer
Calculates field-level and overall row confidence score (0.0 - 1.0) based on:
- Manufacturer/Brand resolution score (0..100)
- Attribute LOV validation & coverage ratio (%)
- Description char-limit compliance (INVOICE_DESC <=40, MOBILE_DESC <=80)
Sets 'needs_human_review' boolean flag.
"""

import os
import json
from typing import List, Dict, Any, Tuple

CACHE_DIR = os.path.join(os.path.dirname(__file__), ".cache")

KNOWN_LOV_LABELS = {
    "Series", "Model", "Number of Wash Cycles", "Voltage Rating", "Amperage Rating",
    "Mounting Type", "Plug Type", "Size", "Depth With Door Open", "Minimum Height",
    "Maximum Height", "Sound Level", "Material", "Color", "Additional Information",
    "Grit", "Outer Diameter", "Thickness", "Arbor Size", "Abrasive Material",
    "Package Quantity", "Fitting Type", "Connection Type", "Nominal Size", "Width", "Length"
}

def evaluate_lov_coverage(row: Dict[str, Any]) -> float:
    extracted = row.get("extracted_attributes", [])
    if not extracted:
        return 0.0
        
    valid_count = 0
    total_count = len(extracted)
    
    for item in extracted:
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            lbl, val = item[0], item[1]
            if lbl in KNOWN_LOV_LABELS:
                valid_count += 1
            elif val and len(str(val)) > 0:
                valid_count += 0.5
                
    return round(valid_count / float(total_count), 3) if total_count > 0 else 0.0

def evaluate_row_confidence(row: Dict[str, Any]) -> Tuple[float, float, bool]:
    # 1. Manufacturer / Brand score (0..100)
    mfr_score = row.get("mfr_brand_match_score", 50.0) / 100.0

    # 2. LOV Coverage score (0..1.0)
    lov_score = evaluate_lov_coverage(row)

    # 3. Char limit compliance
    inv_desc = row.get("INVOICE_DESC") or ""
    mob_desc = row.get("MOBILE_DESC") or ""
    
    inv_ok = len(inv_desc) <= 40 and len(inv_desc) > 0
    mob_ok = len(mob_desc) <= 80 and len(mob_desc) > 0
    desc_compliance_score = (1.0 if inv_ok else 0.5) * 0.5 + (1.0 if mob_ok else 0.5) * 0.5

    # Overall weighted confidence score
    overall_confidence = round(0.35 * mfr_score + 0.40 * lov_score + 0.25 * desc_compliance_score, 3)

    # Human review trigger threshold (< 0.85 or failed char limits)
    needs_review = (overall_confidence < 0.85) or (not inv_ok) or (not mob_ok)

    return overall_confidence, lov_score, needs_review

def run_scoring() -> List[Dict[str, Any]]:
    described_file = os.path.join(CACHE_DIR, "described_rows.json")
    if not os.path.exists(described_file):
        import importlib
        s6 = importlib.import_module("6_describe")
        s6.run_descriptions()

    with open(described_file, "r", encoding="utf-8") as f:
        rows = json.load(f)

    review_count = 0
    total_lov_scores = []

    for row in rows:
        overall_confidence, lov_score, needs_review = evaluate_row_confidence(row)

        row["confidence_score"] = overall_confidence
        row["lov_coverage_score"] = lov_score
        row["needs_human_review"] = needs_review
        
        total_lov_scores.append(lov_score)
        if needs_review:
            review_count += 1

    avg_lov_coverage = (sum(total_lov_scores) / float(len(total_lov_scores))) * 100.0 if total_lov_scores else 0.0

    with open(os.path.join(CACHE_DIR, "scored_rows.json"), "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)

    print(f"[Stage 7: Score Confidence] Computed confidence scores. LOV Coverage: {avg_lov_coverage:.1f}%. {review_count}/{len(rows)} rows flagged for human review.")
    return rows

if __name__ == "__main__":
    run_scoring()
