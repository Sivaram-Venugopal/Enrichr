"""
Master End-to-End Pipeline Execution Script
Runs Stages 0 through 8 sequentially:
0_ingest -> 1_dedup -> 2_manufacturer_brand -> 3_classify -> 4_attributes -> 5_normalize -> 6_describe -> 7_score_confidence -> 8_assemble_output
"""

import time
import importlib

def main():
    print("=" * 60)
    print("Starting Unihack Product Data Enrichment Pipeline")
    print("=" * 60)
    start_time = time.time()

    print("\n--- Running Stage 0: Ingestion & Placeholder Nulling ---")
    s0 = importlib.import_module("0_ingest")
    s0.run_ingest()

    print("\n--- Running Stage 1: Deduplication & Clustering ---")
    s1 = importlib.import_module("1_dedup")
    s1.run_dedup()

    print("\n--- Running Stage 2: Manufacturer & Brand Resolution ---")
    s2 = importlib.import_module("2_manufacturer_brand")
    s2.run_manufacturer_brand_resolution()

    print("\n--- Running Stage 3: Taxonomy & Classpath Classification ---")
    s3 = importlib.import_module("3_classify")
    s3.run_classification()

    print("\n--- Running Stage 4: Structured Attribute Extraction ---")
    s4 = importlib.import_module("4_attributes")
    s4.run_attribute_extraction()

    print("\n--- Running Stage 5: Cleansing & Normalization ---")
    s5 = importlib.import_module("5_normalize")
    s5.run_normalization()

    print("\n--- Running Stage 6: Template Description Building ---")
    s6 = importlib.import_module("6_describe")
    s6.run_descriptions()

    print("\n--- Running Stage 7: Confidence Scoring & Review Flagging ---")
    s7 = importlib.import_module("7_score_confidence")
    s7.run_scoring()

    print("\n--- Running Stage 8: Output Assembly & Audit Trail ---")
    s8 = importlib.import_module("8_assemble_output")
    result = s8.run_assembly()

    elapsed = time.time() - start_time
    print("=" * 60)
    print(f"Pipeline Execution Complete in {elapsed:.2f} seconds.")
    print(f"Deliverable CSV: {result['csv_path']}")
    print(f"Audit JSONL:    {result['jsonl_path']}")
    print("=" * 60)

if __name__ == "__main__":
    main()
