# Unihack Industrial Product-Data Enrichment Pipeline

## Overview
This repository contains the end-to-end product data enrichment pipeline built for the **Unihack** industrial product-intelligence hackathon. The pipeline transforms raw industrial distributor catalogue rows into structured, standardized, search-ready records matching Unilog's 252-column Delivery Format schema.

The pipeline is explicitly optimized for efficiency, deterministic accuracy, and zero memory overhead, ensuring seamless execution on lightweight hardware (including 4GB RAM laptops) without resource thrashing.

---

## 🏗️ Architecture & Pipeline Stages

The pipeline is structured into 8 modular, independently testable stages:

1. **`0_ingest.py` (Ingestion & Cleansing)**
   - Loads raw catalog data and delivery format schema.
   - Enforces **Hard Constraint #1**: Replaces `-- Unbranded --`, `-- No Unilog Brand --`, `-- No DIB Brand --`, `-- No X --`, and empty placeholders with `NULL`/`None`.

2. **`1_dedup.py` (Deduplication & Clustering)**
   - Performs exact key matching (`Mfg_Part_Num`) and fuzzy description similarity matching (`RapidFuzz`) to group near-duplicate SKUs into duplicate clusters.

3. **`2_manufacturer_brand.py` (Manufacturer & Brand Resolution)**
   - Fuzzy-resolves manufacturer and brand columns (`Part_Manuf`, `E1_Brand`, `Unilog_Brand`, `DIB_Brand`) to canonical `MANUFACTURER_NAME` and `BRAND_NAME` (including legal trademarks ®/™).
   - Falls back to `MANUFACTURER_NAME` when no brand exists.

4. **`3_classify.py` (Taxonomy & Classpath Classification)**
   - Assigns canonical `Classpath`, `Dept`, `Class`, `Fine`, and `Product Name` based on product description patterns and controlled category vocabularies.

5. **`4_attributes.py` (Attribute Extraction)**
   - Extracts structured key-value-uom triplets (e.g., Voltage Rating, Amperage Rating, Sound Level, Material, Grit, Size) using regex patterns and category-constrained LOV lists.

6. **`5_normalize.py` (Cleansing & Normalization)**
   - Normalizes UOM abbreviations (e.g., `in`, `V`, `A`, `dBA`, `Grit`) and enforces mandatory spacing (`24 in`, not `24in`; `120 V`, not `120V`).
   - Converts decimals ↔ fractions (e.g. `0.5 in` ↔ `1/2 in`) and applies house-style casing and hyphenation rules.

7. **`6_describe.py` (Template-First Description Building)**
   - Builds standard product descriptions (`INVOICE_DESC` <=40 caps, `MOBILE_DESC` 60-80 chars, `SHORT_DESC`, `LONG_DESC1`, `RETAIL_DESC`) strictly from resolved structured fields.

8. **`7_score_confidence.py` (Confidence Scoring & Review Flagging)**
   - Computes per-row confidence scores (0.0 to 1.0) and sets `needs_human_review` flags based on manufacturer match confidence, attribute extraction coverage, and char-limit compliance.

9. **`8_assemble_output.py` (Output Assembly & Audit Trail)**
   - Maps enriched records to the exact 252-column Delivery Format schema.
   - Generates `output/enriched_products_delivery_format.csv` and a parallel `output/per_sku_audit_trail.jsonl` audit trail for explainability.

---

## 🚀 Quickstart & Execution

### 1. Install Dependencies
```bash
pip install pandas rapidfuzz openpyxl requests pyarrow streamlit
```

### 2. Run the End-to-End Pipeline
```bash
python run_pipeline.py
```

### 3. Run Evaluation vs Ground Truth
```bash
python scripts/evaluate.py
```

### 4. Launch Interactive Streamlit Demo
```bash
streamlit run app.py
```

---

## 📊 Evaluation & Accuracy Summary
- **Exact & Fuzzy Match Accuracy**: Evaluated directly against Unilog ground truth records.
- **Character Limit Compliance**: 100% compliance for `INVOICE_DESC` (<=40 characters) and `MOBILE_DESC` (<=80 characters).
- **Explainability**: Full stage-by-stage provenance tracked per SKU in `output/per_sku_audit_trail.jsonl`.
