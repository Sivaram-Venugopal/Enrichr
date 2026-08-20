"""
Stage 8: Output Assembly & Audit Trail Layer
Maps enriched row records into the exact 252-column Delivery Format schema.
Generates:
1. output/enriched_products_delivery_format.csv
2. output/per_sku_audit_trail.jsonl (Explainability & provenance log)
"""

import os
import json
import csv
from typing import List, Dict, Any

CACHE_DIR = os.path.join(os.path.dirname(__file__), ".cache")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")

def run_assembly() -> Dict[str, Any]:
    scored_file = os.path.join(CACHE_DIR, "scored_rows.json")
    if not os.path.exists(scored_file):
        import importlib
        s7 = importlib.import_module("7_score_confidence")
        s7.run_scoring()

    headers_file = os.path.join(CACHE_DIR, "delivery_headers.json")
    with open(headers_file, "r", encoding="utf-8") as f:
        headers = json.load(f)

    with open(scored_file, "r", encoding="utf-8") as f:
        rows = json.load(f)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    csv_path = os.path.join(OUTPUT_DIR, "enriched_products_delivery_format.csv")
    jsonl_path = os.path.join(OUTPUT_DIR, "per_sku_audit_trail.jsonl")

    # Map each enriched row to the 252-column format
    output_rows = []
    audit_entries = []

    for idx, row in enumerate(rows):
        out_row = {}
        for col in headers:
            # Check if value exists in row dict
            val = row.get(col)
            if val is None:
                # Check mapping for standard source columns
                if col == "Mfg_Part_Num":
                    val = row.get("Mfg_Part_Num")
                elif col == "Part_Desc":
                    val = row.get("Part_Desc")
                elif col == "Part_Manuf":
                    val = row.get("Part_Manuf")
                elif col == "MANUFACTURER_PART_NUMBER":
                    val = row.get("Mfg_Part_Num")
                else:
                    val = ""
            out_row[col] = str(val) if val is not None else ""
            
        output_rows.append(out_row)

        # Audit trail entry for explainability
        audit_entry = {
            "sku_index": idx,
            "mfg_part_num": row.get("Mfg_Part_Num"),
            "raw_part_desc": row.get("Part_Desc"),
            "raw_part_manuf": row.get("Part_Manuf"),
            "stages": {
                "0_ingest": {"cleaned": True},
                "1_dedup": {
                    "cluster_id": row.get("dedup_cluster_id"),
                    "is_duplicate": row.get("is_duplicate")
                },
                "2_mfr_brand": {
                    "resolved_manufacturer": row.get("MANUFACTURER_NAME"),
                    "resolved_brand": row.get("BRAND_NAME"),
                    "match_score": row.get("mfr_brand_match_score")
                },
                "3_classify": {
                    "classpath": row.get("Classpath"),
                    "dept": row.get("Dept"),
                    "class": row.get("Class"),
                    "fine": row.get("Fine")
                },
                "4_attributes": {
                    "extracted_count": len(row.get("extracted_attributes", [])),
                    "attributes": row.get("extracted_attributes", [])
                },
                "5_normalize": {"uom_normalized": True},
                "6_describe": {
                    "invoice_desc": row.get("INVOICE_DESC"),
                    "mobile_desc": row.get("MOBILE_DESC"),
                    "short_desc": row.get("SHORT_DESC")
                },
                "7_score_confidence": {
                    "confidence_score": row.get("confidence_score"),
                    "needs_human_review": row.get("needs_human_review")
                }
            }
        }
        audit_entries.append(audit_entry)

    # Write Delivery Format CSV
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(output_rows)

    # Write Audit Trail JSONL
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for entry in audit_entries:
            f.write(json.dumps(entry) + "\n")

    print(f"[Stage 8: Assemble Output] Successfully wrote Delivery Format CSV with {len(output_rows)} rows to {csv_path}")
    print(f"[Stage 8: Assemble Output] Successfully wrote JSONL audit trail to {jsonl_path}")

    return {"csv_path": csv_path, "jsonl_path": jsonl_path, "row_count": len(output_rows)}

if __name__ == "__main__":
    run_assembly()
