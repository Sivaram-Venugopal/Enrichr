"""
Streamlit Interactive Demo App for Unihack Product Data Enrichment Pipeline
Shows step-by-step row journey across all 8 pipeline stages for live demonstration.
"""

import os
import json
import streamlit as st
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, ".cache")
OUTPUT_CSV = os.path.join(BASE_DIR, "output", "enriched_products_delivery_format.csv")
AUDIT_JSONL = os.path.join(BASE_DIR, "output", "per_sku_audit_trail.jsonl")

st.set_page_config(page_title="Unihack Product Intelligence Pipeline", layout="wide")

st.title("🏭 Unihack Product Data Enrichment Pipeline")
st.caption("Industrial Product Intelligence Hackathon - Unilog 252-Column Data Pipeline Demo")

if not os.path.exists(AUDIT_JSONL):
    st.warning("Audit trail file not found. Please run `python run_pipeline.py` first.")
    st.stop()

# Load audit trail
audit_entries = []
with open(AUDIT_JSONL, "r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            audit_entries.append(json.loads(line))

st.sidebar.header("Navigation & Inspection")
sku_options = [f"Row {e['sku_index']}: {e['mfg_part_num']} - {(e['raw_part_desc'] or '')[:40]}" for e in audit_entries]
selected_sku_idx = st.sidebar.selectbox("Select SKU / Item", range(len(sku_options)), format_func=lambda i: sku_options[i])

entry = audit_entries[selected_sku_idx]
stages = entry["stages"]

st.subheader(f"📦 Selected SKU: {entry['mfg_part_num']}")
st.text(f"Raw Description: {entry['raw_part_desc']}")
st.text(f"Raw Manufacturer: {entry['raw_part_manuf']}")

st.divider()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Confidence Score", f"{stages['7_score_confidence']['confidence_score'] * 100:.1f}%")
with col2:
    need_rev = stages['7_score_confidence']['needs_human_review']
    st.metric("Human Review Flag", "🚩 Needed" if need_rev else "✅ Clean")
with col3:
    st.metric("Attributes Extracted", stages['4_attributes']['extracted_count'])

st.divider()
st.subheader("🔄 Stage-by-Stage Processing Journey")

tab0, tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "0. Ingest", "1. Dedup", "2. Mfr/Brand", "3. Taxonomy",
    "4. Attributes", "5. Normalize", "6. Describe", "7. Score & Audit"
])

with tab0:
    st.json(stages["0_ingest"])

with tab1:
    st.json(stages["1_dedup"])

with tab2:
    st.json(stages["2_mfr_brand"])

with tab3:
    st.json(stages["3_classify"])

with tab4:
    st.json(stages["4_attributes"])

with tab5:
    st.json(stages["5_normalize"])

with tab6:
    st.json(stages["6_describe"])

with tab7:
    st.json(stages["7_score_confidence"])

st.divider()
st.subheader("📄 Enriched 252-Column Delivery Record")
if os.path.exists(OUTPUT_CSV):
    df = pd.read_csv(OUTPUT_CSV)
    st.dataframe(df.iloc[[selected_sku_idx]])
