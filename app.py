"""
Advanced Industry-Standard Streamlit UI for Unihack Product Intelligence Pipeline
Custom glassmorphic aesthetic, dark-mode styling, stage journey timelines, and audit inspector.
"""

import os
import json
import streamlit as st
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_CSV = os.path.join(BASE_DIR, "output", "enriched_products_delivery_format.csv")
AUDIT_JSONL = os.path.join(BASE_DIR, "output", "per_sku_audit_trail.jsonl")

# Page Config
st.set_page_config(
    page_title="Unilog Enterprise Product Intelligence Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Advanced Industry-Standard Custom CSS
st.markdown("""
<style>
    /* Global Styling */
    .stApp {
        background-color: #0b0f19;
        color: #e2e8f0;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    
    /* Header Banner */
    .hero-banner {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 24px 32px;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
    }
    .hero-title {
        font-size: 28px;
        font-weight: 800;
        background: linear-gradient(90deg, #38bdf8 0%, #818cf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0 0 8px 0;
    }
    .hero-subtitle {
        color: #94a3b8;
        font-size: 14px;
        margin: 0;
    }
    
    /* Metric Cards */
    .metric-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 16px 20px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.3);
    }
    .metric-label {
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #94a3b8;
        margin-bottom: 6px;
    }
    .metric-value-green {
        font-size: 26px;
        font-weight: 700;
        color: #34d399;
    }
    .metric-value-blue {
        font-size: 26px;
        font-weight: 700;
        color: #38bdf8;
    }
    .metric-value-amber {
        font-size: 26px;
        font-weight: 700;
        color: #fbbf24;
    }
    
    /* Badge Pills */
    .badge-pill {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 12px;
        font-weight: 600;
    }
    .badge-clean {
        background-color: rgba(52, 211, 153, 0.15);
        color: #34d399;
        border: 1px solid rgba(52, 211, 153, 0.3);
    }
    .badge-review {
        background-color: rgba(251, 191, 36, 0.15);
        color: #fbbf24;
        border: 1px solid rgba(251, 191, 36, 0.3);
    }
    
    /* Stage Timeline Card */
    .stage-card {
        background: #0f172a;
        border-left: 4px solid #38bdf8;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .stage-title {
        font-size: 14px;
        font-weight: 700;
        color: #f8fafc;
    }
</style>
""", unsafe_allow_html=True)

# Header Banner
st.markdown("""
<div class="hero-banner">
    <div class="hero-title">⚡ Unilog Enterprise Product Data Intelligence Engine</div>
    <div class="hero-subtitle">High-Speed Zero-OOM Product Data Enrichment Pipeline | 252-Column Unilog Delivery Schema</div>
</div>
""", unsafe_allow_html=True)

if not os.path.exists(AUDIT_JSONL):
    st.error("❌ Audit trail file not found. Please run `python run_pipeline.py` first.")
    st.stop()

# Load audit trail
@st.cache_data
def load_data():
    entries = []
    with open(AUDIT_JSONL, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))
    df_out = pd.read_csv(OUTPUT_CSV) if os.path.exists(OUTPUT_CSV) else None
    return entries, df_out

audit_entries, df_delivery = load_data()

# Global Overview Metrics Top Row
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Total SKUs Processed</div>
        <div class="metric-value-blue">{len(audit_entries)}</div>
    </div>
    """, unsafe_allow_html=True)

with m2:
    avg_conf = sum(e["stages"]["7_score_confidence"]["confidence_score"] for e in audit_entries) / max(1, len(audit_entries))
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Avg Confidence Score</div>
        <div class="metric-value-green">{avg_conf * 100:.1f}%</div>
    </div>
    """, unsafe_allow_html=True)

with m3:
    clean_count = sum(1 for e in audit_entries if not e["stages"]["7_score_confidence"]["needs_human_review"])
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Automated Clean SKUs</div>
        <div class="metric-value-green">{clean_count} ({clean_count/len(audit_entries)*100:.1f}%)</div>
    </div>
    """, unsafe_allow_html=True)

with m4:
    review_count = len(audit_entries) - clean_count
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Human Review Queue</div>
        <div class="metric-value-amber">{review_count} ({review_count/len(audit_entries)*100:.1f}%)</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# Sidebar Navigation & Search
st.sidebar.markdown("### 🔎 SKU Inspector Controls")
search_term = st.sidebar.text_input("Search MPN / Keyword", "")

filtered_indices = []
for idx, entry in enumerate(audit_entries):
    mpn = str(entry.get("mfg_part_num") or "")
    desc = str(entry.get("raw_part_desc") or "")
    if search_term.lower() in mpn.lower() or search_term.lower() in desc.lower():
        filtered_indices.append(idx)

if not filtered_indices:
    st.sidebar.warning("No matching SKUs found.")
    filtered_indices = list(range(len(audit_entries)))

selected_sku_idx = st.sidebar.selectbox(
    "Select SKU to Inspect",
    filtered_indices,
    format_func=lambda i: f"SKU #{i}: {audit_entries[i]['mfg_part_num']} | {(audit_entries[i]['raw_part_desc'] or '')[:30]}"
)

entry = audit_entries[selected_sku_idx]
stages = entry["stages"]

# Main Content Layout: Selected SKU Details
st.markdown(f"### 📦 Product Record Details: `{entry['mfg_part_num']}`")
c_left, c_right = st.columns([2, 1])

with c_left:
    st.markdown(f"**Raw Part Description**: `{entry['raw_part_desc']}`")
    st.markdown(f"**Raw Manufacturer Tag**: `{entry['raw_part_manuf']}`")
    st.markdown(f"**Assigned Classpath**: `{stages['3_classify']['classpath']}`")

with c_right:
    conf = stages["7_score_confidence"]["confidence_score"]
    review = stages["7_score_confidence"]["needs_human_review"]
    st.markdown(f"**Confidence Score**: `{conf * 100:.1f}%`")
    if review:
        st.markdown('<span class="badge-pill badge-review">🚩 Needs Human Review</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge-pill badge-clean">✅ Verified Clean</span>', unsafe_allow_html=True)

st.divider()

# Tabbed Stage Inspector
st.markdown("### 🔄 8-Stage Data Enrichment Lifecycle")
tab_stage, tab_attrs, tab_desc, tab_schema, tab_audit = st.tabs([
    "📍 Lifecycle Journey", "📐 Extracted Attributes", "📝 Generated Descriptions", "📋 252-Col Delivery Schema", "📜 JSON Audit Trail"
])

with tab_stage:
    st.markdown("#### Stage-by-Stage Processing Record")
    st.markdown(f"""
    <div class="stage-card">
        <div class="stage-title">Stage 0: Ingestion & Placeholder Nulling</div>
        <p style="color:#94a3b8; font-size:13px;">Raw distributor string cleaned. Hard Constraint #1 applied: Nullified unbranded/placeholder flags.</p>
    </div>
    <div class="stage-card">
        <div class="stage-title">Stage 1: Deduplication & Near-Duplicate Clustering</div>
        <p style="color:#94a3b8; font-size:13px;">Cluster ID: <code>{stages['1_dedup']['cluster_id']}</code> | Is Duplicate: <code>{stages['1_dedup']['is_duplicate']}</code></p>
    </div>
    <div class="stage-card">
        <div class="stage-title">Stage 2: Manufacturer & Brand Resolution</div>
        <p style="color:#94a3b8; font-size:13px;">Manufacturer: <b>{stages['2_mfr_brand']['resolved_manufacturer']}</b> | Brand: <b>{stages['2_mfr_brand']['resolved_brand']}</b> (Match Confidence: {stages['2_mfr_brand']['match_score']}%)</p>
    </div>
    <div class="stage-card">
        <div class="stage-title">Stage 3: Taxonomy Classification</div>
        <p style="color:#94a3b8; font-size:13px;">Dept: <b>{stages['3_classify']['dept']}</b> → Class: <b>{stages['3_classify']['class']}</b> → Fine: <b>{stages['3_classify']['fine']}</b></p>
    </div>
    """, unsafe_allow_html=True)

with tab_attrs:
    st.markdown("#### Canonical Key-Value-UOM Attribute Triples")
    attrs = stages["4_attributes"]["attributes"]
    if attrs:
        attr_df = pd.DataFrame(attrs, columns=["Attribute Label", "Normalized Value", "Approved UOM"])
        st.table(attr_df)
    else:
        st.info("No attributes extracted for this item.")

with tab_desc:
    st.markdown("#### Standardized Template Descriptions")
    descs = stages["6_describe"]
    st.text_input("INVOICE_DESC (<=40 Caps)", descs.get("invoice_desc", ""), disabled=True)
    st.text_input("MOBILE_DESC (60-80 Chars)", descs.get("mobile_desc", ""), disabled=True)
    st.text_area("SHORT_DESC", descs.get("short_desc", ""), disabled=True)

with tab_schema:
    st.markdown("#### Complete 252-Column Unilog Delivery Record")
    if df_delivery is not None:
        st.dataframe(df_delivery.iloc[[selected_sku_idx]], use_container_width=True)

with tab_audit:
    st.markdown("#### Per-SKU Explainability JSON")
    st.json(entry)
