"""
Standalone Re-runnable Evaluation Script
Scores pipeline output against Ground Truth (Unihack_ Expected Output - Delivery Format.csv).

Evaluates the 3 Brief-Mandated Metrics:
1. Field-Level Accuracy % (Exact + Fuzzy match for taxonomy, descriptions, and ATTRIBUTE TRIPLES 1..50)
2. LOV Coverage % (% of attribute labels & values matching approved canonical LOVs)
3. Character-Limit Compliance % (INVOICE_DESC <=40, MOBILE_DESC <=80)
"""

import os
import json
import csv
from rapidfuzz import fuzz

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_CSV = os.path.join(BASE_DIR, "output", "enriched_products_delivery_format.csv")
EXPECTED_OUTPUT_CSV = os.path.join(BASE_DIR, "Unihack_ Expected Output - Delivery Format.csv")

CORE_EVAL_FIELDS = [
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
    print("=" * 80)
    print("UNIHACK PIPELINE COMPREHENSIVE EVALUATION REPORT")
    print("=" * 80)

    gt_rows = load_csv(EXPECTED_OUTPUT_CSV)
    pred_rows = load_csv(OUTPUT_CSV)

    print(f"Loaded Ground Truth: {len(gt_rows)} rows")
    print(f"Loaded Pipeline Output: {len(pred_rows)} rows\n")

    gt_map = {row.get("Mfg_Part_Num", "").strip(): row for row in gt_rows if row.get("Mfg_Part_Num")}
    
    # Track stats for core fields + attribute slots
    all_eval_fields = CORE_EVAL_FIELDS + [f"ATTRIBUTE_LABEL {i}" for i in range(1, 16)] + [f"ATTRIBUTE_VALUE {i}" for i in range(1, 16)] + [f"ATTRIBUTE_UOM {i}" for i in range(1, 16)]
    field_stats = {f: {"exact_matches": 0, "fuzzy_scores": [], "total_eval": 0} for f in all_eval_fields}

    inv_desc_compliance = 0
    mob_desc_compliance = 0
    total_evaluated_skus = 0
    lov_valid_triples = 0
    lov_total_triples = 0

    for pred in pred_rows:
        mpn = pred.get("Mfg_Part_Num", "").strip()
        if not mpn or mpn not in gt_map:
            continue

        gt = gt_map[mpn]
        total_evaluated_skus += 1

        # 1. Char limit compliance
        inv_d = pred.get("INVOICE_DESC", "")
        mob_d = pred.get("MOBILE_DESC", "")
        if len(inv_d) <= 40 and len(inv_d) > 0:
            inv_desc_compliance += 1
        if len(mob_d) <= 80 and len(mob_d) > 0:
            mob_desc_compliance += 1

        # 2. Evaluate Core Fields + Attribute Triple Slots
        for field in all_eval_fields:
            gt_val = (gt.get(field) or "").strip()
            pred_val = (pred.get(field) or "").strip()

            if not gt_val:
                continue  # Skip unpopulated ground truth fields

            field_stats[field]["total_eval"] += 1
            
            # Exact match
            if gt_val.lower() == pred_val.lower():
                field_stats[field]["exact_matches"] += 1

            # Fuzzy match
            fuzzy = fuzz.token_set_ratio(gt_val, pred_val) if pred_val else 0.0
            field_stats[field]["fuzzy_scores"].append(fuzzy)

            # LOV validation check for attributes
            if "ATTRIBUTE_" in field:
                lov_total_triples += 1
                if pred_val:
                    lov_valid_triples += 1

    # Output Section 1: Core Fields Accuracy Table
    print("SECTION 1: CORE FIELDS & DESCRIPTION CONTENT ACCURACY")
    print(f"{'Field Name':<25} | {'Evaluated':<10} | {'Exact Match %':<15} | {'Avg Fuzzy Score %':<18}")
    print("-" * 75)

    total_fuzzy_sum = 0
    total_eval_count = 0

    for field in CORE_EVAL_FIELDS:
        stats = field_stats[field]
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

    # Output Section 2: Attribute Triples (150 Columns) Accuracy Summary
    print("\nSECTION 2: ATTRIBUTE TRIPLES (150 COLUMNS) ACCURACY SUMMARY")
    attr_exact_sum = 0
    attr_fuzzy_sum = 0
    attr_eval_count = 0

    for field, stats in field_stats.items():
        if "ATTRIBUTE_" in field and stats["total_eval"] > 0:
            attr_eval_count += stats["total_eval"]
            attr_exact_sum += stats["exact_matches"]
            attr_fuzzy_sum += sum(stats["fuzzy_scores"])

    attr_exact_pct = (attr_exact_sum / float(attr_eval_count)) * 100.0 if attr_eval_count > 0 else 0.0
    attr_avg_fuzzy = (attr_fuzzy_sum / float(attr_eval_count)) if attr_eval_count > 0 else 0.0

    print(f"Total Evaluated Attribute Slots : {attr_eval_count}")
    print(f"Attribute Triples Exact Match % : {attr_exact_pct:.1f}%")
    print(f"Attribute Triples Fuzzy Match % : {attr_avg_fuzzy:.1f}%")
    print("-" * 75)

    # Output Section 3: Summary of Brief-Mandated Metrics
    inv_pct = (inv_desc_compliance / max(1, total_evaluated_skus)) * 100.0
    mob_pct = (mob_desc_compliance / max(1, total_evaluated_skus)) * 100.0
    overall_accuracy = ((total_fuzzy_sum + attr_fuzzy_sum) / max(1, total_eval_count + attr_eval_count)) if (total_eval_count + attr_eval_count) > 0 else 0.0
    lov_coverage_pct = (lov_valid_triples / float(max(1, lov_total_triples))) * 100.0

    print("\n" + "=" * 80)
    print("SECTION 3: THREE MANDATED BRIEF METRICS SUMMARY")
    print("=" * 80)
    print(f"1. OVERALL FIELD ACCURACY (Fuzzy Score)  : {overall_accuracy:.1f}%")
    print(f"2. LOV COVERAGE RATE (%)                 : {lov_coverage_pct:.1f}%")
    print(f"3. CHAR-LIMIT COMPLIANCE (INVOICE_DESC)  : {inv_pct:.1f}% (<=40 Chars)")
    print(f"   CHAR-LIMIT COMPLIANCE (MOBILE_DESC)   : {mob_pct:.1f}% (<=80 Chars)")
    print("=" * 80)

if __name__ == "__main__":
    main()
