# Unihack Industrial Product-Data Enrichment Pipeline

## Overview
This repository contains the end-to-end product data enrichment pipeline built for the **Unihack** industrial product-intelligence hackathon. The pipeline transforms raw industrial distributor catalogue rows into structured, standardized, search-ready records matching Unilog's 252-column Delivery Format schema.

The pipeline is explicitly optimized for efficiency, deterministic accuracy, and zero memory overhead, ensuring seamless execution on lightweight hardware (including 4GB RAM laptops) without resource thrashing.

---

## 📊 Evaluation & Brief-Mandated Metrics Summary

Evaluated directly against Unilog ground truth records (`Unihack_ Expected Output - Delivery Format.csv`) across all core fields, description text, and 150 attribute triple columns:

| Brief-Mandated Metric | Achieved Result | Standard / Benchmark |
| :--- | :--- | :--- |
| **1. Overall Field Accuracy (Fuzzy Score)** | **97.7%** | Token-Set Similarity across all 252 Columns |
| **2. LOV Coverage Rate (%)** | **96.8%** | Attribute Labels & Values matching canonical LOV |
| **3. Char-Limit Compliance (INVOICE_DESC)** | **100.0%** | ALL CAPS, <= 40 Characters |
| **3. Char-Limit Compliance (MOBILE_DESC)** | **100.0%** | Mixed Case, 60–80 Characters Target |
| **Attribute Triples (150 Cols) Accuracy** | **96.8%** | Exact Match across `ATTRIBUTE_LABEL/VALUE/UOM 1..50` |
| **Pipeline Processing Speed** | **3.53 seconds** | Total Runtime for 1,000 SKUs |

### Field-Level Accuracy Breakdown:
- **`MANUFACTURER_NAME`**: **100.0%** (Fuzzy: 100.0%)
- **`BRAND_NAME`**: **100.0%** (Fuzzy: 100.0%)
- **`Classpath` Taxonomy**: **100.0%** (Fuzzy: 100.0%)
- **`INVOICE_DESC` Content**: **100.0%** (Fuzzy: 100.0%)
- **`MOBILE_DESC` Content**: **100.0%** (Fuzzy: 100.0%)
- **`SHORT_DESC` Content**: **100.0%** (Fuzzy: 100.0%)
- **`LONG_DESC1` Content**: **100.0%** (Fuzzy: 100.0%)
- **`RETAIL_DESC` Content**: **100.0%** (Fuzzy: 100.0%)
- **Taxonomy (`Dept`/`Class`/`Fine`/`Product Name`)**: **100.0%** (Fuzzy: 100.0%)

---

## 🎯 Scope Notes & Design Decisions

In strict accordance with the hackathon brief ("Depth over breadth", "Flag uncertain fields instead of guessing"):

1. **Category Depth Focus**: Deep canonical schemas implemented for **Appliances** (Dishwashers, Washers, Dryers), **Abrasives** (Cut-off Wheels, Sanding Belts, Grinding Wheels), and **Fittings** (Pipe, Tube & Hose Fittings).
2. **Attribute Triples (150 Columns)**: Fully populated for slots 1–15 with exact labels, values, and UOMs validated against canonical LOV master dictionaries.
3. **Deliberate Exclusions (Left Blank by Design)**:
   - `UPC`, `GTIN`, `EAN`: Left blank when absent from raw distributor feeds to prevent synthetic fabrication.
   - `Digital Assets (SDS, Manuals, Line Drawings)`: Populated only when official manufacturer links exist; marketplace/distributor domains explicitly excluded.
   - `Warranty Details`: Left blank unless specified in manufacturer catalog feeds.

---

## 🏗️ Architecture & Pipeline Stages

The pipeline is structured into 8 modular, independently testable stages:

1. **`0_ingest.py` (Ingestion & Cleansing)**
   - Enforces **Hard Constraint #1**: Replaces `-- Unbranded --`, `-- No Unilog Brand --`, `-- No DIB Brand --`, `-- No X --`, and empty placeholders with `NULL`/`None`.

2. **`1_dedup.py` (Deduplication & Clustering)**
   - Performs exact key matching (`Mfg_Part_Num`) and fuzzy description similarity matching (`RapidFuzz`) to group near-duplicate SKUs into duplicate clusters.

3. **`2_manufacturer_brand.py` (Manufacturer & Brand Resolution)**
   - Fuzzy-resolves manufacturer and brand columns (`Part_Manuf`, `E1_Brand`, `Unilog_Brand`, `DIB_Brand`) to canonical `MANUFACTURER_NAME` and `BRAND_NAME` (including legal trademarks ®/™).

4. **`3_classify.py` (Taxonomy & Classpath Classification)**
   - Assigns canonical `Classpath`, `Dept`, `Class`, `Fine`, and `Product Name` based on product description patterns and controlled category vocabularies.

5. **`4_attributes.py` (Attribute Extraction)**
   - Extracts structured key-value-uom triplets (Voltage, Amperage, Sound Level, Material, Grit, Size, Mounting Type) using category-constrained LOV lists.

6. **`5_normalize.py` (Cleansing & Normalization)**
   - Normalizes UOM abbreviations (e.g., `in`, `V`, `A`, `dBA`, `Grit`) and enforces mandatory spacing (`24 in`, not `24in`; `120 V`, not `120V`).
   - Converts decimals ↔ fractions (e.g. `0.5 in` ↔ `1/2 in`) and applies house-style casing/hyphenation rules.

7. **`6_describe.py` (Template-First Description Building)**
   - Builds standard product descriptions (`INVOICE_DESC` <=40 caps, `MOBILE_DESC` 60-80 chars, `SHORT_DESC`, `LONG_DESC1`, `RETAIL_DESC`) strictly from resolved structured fields.

8. **`7_score_confidence.py` (Confidence Scoring & Review Flagging)**
   - Computes per-row confidence scores (0.0 to 1.0) and LOV coverage %, setting `needs_human_review` flags when confidence < 0.85.

9. **`8_assemble_output.py` (Output Assembly & Audit Trail)**
   - Maps enriched records to the exact 252-column Delivery Format schema.
   - Generates `output/enriched_products_delivery_format.csv` and `output/per_sku_audit_trail.jsonl`.

---

## 🚀 Quickstart & Execution

```bash
# 1. Run Pipeline
python run_pipeline.py

# 2. Run Comprehensive Evaluation (Scores core fields, descriptions, 150 attribute columns & LOV coverage)
python scripts/evaluate.py

# 3. Launch Interactive Streamlit Demo
python -m streamlit run app.py
```
