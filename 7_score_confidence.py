"""
Stage 7: Validation, Scoring & Confidence Layer
Calculates field-level and overall row confidence score (0.0 - 1.0) based on:
- Manufacturer/Brand resolution score
- Attribute extraction ratio
- Description char-limit compliance
Sets 'needs_human_review' boolean flag.
"""

import os
import json
from typing import List, Dict, Any, Tuple

CACHE_DIR = os.path.join(os.path.dirname(__file__), ".cache")

def evaluate_row_confidence(row: Dict[str, Any]) -> Tuple[float, bool]:
    # 1. Manufacturer / Brand score (0..100)
    mfr_score = row.get("mfr_brand_match_score", 50.0) / 100.0

    # 2. Attribute extraction score
    attrs_count = len(row.get("extracted_attributes", []))
    attr_score = min(1.0, attrs_count / 3.0) if attrs_count > 0 else 0.4

    # 3. Char limit compliance
    inv_desc = row.get("INVOICE_DESC") or ""
    mob_desc = row.get("MOBILE_DESC") or ""
    
    inv_ok = len(inv_desc) <= 40 and len(inv_desc) > 0
    mob_ok = len(mob_desc) <= 80 and len(mob_desc) > 0
    
    desc_compliance_score = (1.0 if inv_ok else 0.5) * 0.5 + (1.0 if mob_ok else 0.5) * 0.5

    # Overall weighted score
    overall_confidence = round(0.4 * mfr_score + 0.3 * attr_score + 0.3 * desc_compliance_score, 3)

    # Human review trigger threshold (< 0.75 or failed char limits)
    needs_review = (overall_confidence < 0.75) or (not inv_ok) or (not mob_ok)

    return overall_confidence, needs_review

def run_scoring() -> List[Dict[str, Any]]:
    described_file = os.path.join(CACHE_DIR, "described_rows.json")
    if not os.path.exists(described_file):
        import importlib
        s6 = importlib.import_module("6_describe")
        s6.run_descriptions()

    with open(described_file, "r", encoding="utf-8") as f:
        rows = json.load(f)

    review_count = 0
    for row in rows:
        mfr_score = row.get("mfr_brand_match_score", 50.0) / 100.0
        attrs_count = len(row.get("extracted_attributes", []))
        attr_score = min(1.0, attrs_count / 3.0) if attrs_count > 0 else 0.4
        
        inv_desc = row.get("INVOICE_DESC") or ""
        mob_desc = row.get("MOBILE_DESC") or ""
        inv_ok = len(inv_desc) <= 40 and len(inv_desc) > 0
        mob_ok = len(mob_desc) <= 80 and len(mob_desc) > 0
        desc_compliance_score = (1.0 if inv_ok else 0.5) * 0.5 + (1.0 if mob_ok else 0.5) * 0.5

        overall_confidence = round(0.4 * mfr_score + 0.3 * attr_score + 0.3 * desc_compliance_score, 3)
        needs_review = (overall_confidence < 0.75) or (not inv_ok) or (not mob_ok)

        row["confidence_score"] = overall_confidence
        row["needs_human_review"] = needs_review
        
        if needs_review:
            review_count += 1

    with open(os.path.join(CACHE_DIR, "scored_rows.json"), "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)

    print(f"[Stage 7: Score Confidence] Computed confidence scores. {review_count}/{len(rows)} rows flagged for human review.")
    return rows

if __name__ == "__main__":
    run_scoring()
