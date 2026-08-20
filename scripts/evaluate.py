"""
Standalone Re-runnable Evaluation Script
Scores pipeline output against Ground Truth (Unihack_ Expected Output - Delivery Format.csv).
Calculates:
- Field-level exact match rate (%)
- Field-level fuzzy match rate (%)
- Character-limit compliance rate (%)
- Overall quality score
"""

import os
import json
import csv
from rapidfuzz import fuzz

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_CSV = os.path.join(BASE_DIR, "output", "enriched_products_delivery_format.csv")
EXPECTED_OUTPUT_CSV = os.path.join(BASE_DIR, "Unihack_ Expected Output - Delivery Format.csv")

EVAL_FIELDS = [
    "MANUFACTURER_NAME",
    "BRAND_NAME",
    "Classpath",
    "INVOICE_DESC",
    "MOBILE_DESC",
    "SHORT_DESC",
    "LONG_DESC1",
    "RETAIL_DESC",
    "Dept",
    "Class",
    "Fine",
    "Product Name"
]

def load_csv(path: str):
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f)
        return list(reader)

def main():
    print("=" * 70)
    print("UNIHACK PIPELINE EVALUATION REPORT")
    print("=" * 70)

    gt_rows = load_csv(EXPECTED_OUTPUT_CSV)
    pred_rows = load_csv(OUTPUT_CSV)

    print(f"Loaded Ground Truth: {len(gt_rows)} rows")
    print(f"Loaded Pipeline Output: {len(pred_rows)} rows\n")

    # Match rows by Mfg_Part_Num
    gt_map = {row.get("Mfg_Part_Num", "").strip(): row for row in gt_rows if row.get("Mfg_Part_Num")}
    
    field_stats = {f: {"exact_matches": 0, "fuzzy_scores": [], "total_eval": 0} for f in EVAL_FIELDS}

    inv_desc_compliance = 0
    mob_desc_compliance = 0
    total_evaluated_skus = 0

    for pred in pred_rows:
        mpn = pred.get("Mfg_Part_Num", "").strip()
        if not mpn or mpn not in gt_map:
            continue

        gt = gt_map[mpn]
        total_evaluated_skus += 1

        # Check character limit compliance
        inv_d = pred.get("INVOICE_DESC", "")
        mob_d = pred.get("MOBILE_DESC", "")
        if len(inv_d) <= 40 and len(inv_d) > 0:
            inv_desc_compliance += 1
        if len(mob_d) <= 80 and len(mob_d) > 0:
            mob_desc_compliance += 1

        # Evaluate each field
        for field in EVAL_FIELDS:
            gt_val = (gt.get(field) or "").strip()
            pred_val = (pred.get(field) or "").strip()

            if not gt_val:
                continue  # Skip unpopulated ground truth fields

            field_stats[field]["total_eval"] += 1
            
            # Exact match check
            if gt_val.lower() == pred_val.lower():
                field_stats[field]["exact_matches"] += 1

            # Fuzzy match check
            fuzzy = fuzz.token_set_ratio(gt_val, pred_val) if pred_val else 0.0
            field_stats[field]["fuzzy_scores"].append(fuzzy)

    print(f"{'Field Name':<25} | {'Evaluated':<10} | {'Exact Match %':<15} | {'Avg Fuzzy Score %':<18}")
    print("-" * 75)

    total_fuzzy_sum = 0
    total_eval_count = 0

    for field, stats in field_stats.items():
        total = stats["total_eval"]
        if total == 0:
            print(f"{field:<25} | {0:<10} | {'N/A':<15} | {'N/A':<18}")
            continue

        exact_pct = (stats["exact_matches"] / total) * 100.0
        avg_fuzzy = (sum(stats["fuzzy_scores"]) / total) if stats["fuzzy_scores"] else 0.0
        
        total_fuzzy_sum += sum(stats["fuzzy_scores"])
        total_eval_count += total

        print(f"{field:<25} | {total:<10} | {exact_pct:>13.1f}% | {avg_fuzzy:>16.1f}%")

    print("-" * 75)

    inv_pct = (inv_desc_compliance / max(1, total_evaluated_skus)) * 100.0
    mob_pct = (mob_desc_compliance / max(1, total_evaluated_skus)) * 100.0
    overall_accuracy = (total_fuzzy_sum / max(1, total_eval_count)) if total_eval_count > 0 else 0.0

    print("\n" + "=" * 70)
    print("COMPLIANCE & SUMMARY METRICS")
    print("=" * 70)
    print(f"INVOICE_DESC (<=40 Chars) Compliance Rate : {inv_pct:.1f}%")
    print(f"MOBILE_DESC  (<=80 Chars) Compliance Rate : {mob_pct:.1f}%")
    print(f"Overall Pipeline Field Accuracy (Fuzzy Score): {overall_accuracy:.1f}%")
    print("=" * 70)

if __name__ == "__main__":
    main()
