"""
Stage 6: Description Building Layer
Template-first construction of standard description fields strictly from resolved structured attributes:
- INVOICE_DESC: <=40 chars, UPPERCASE
- MOBILE_DESC: 60-80 chars
- SHORT_DESC: Concise structured summary
- LONG_DESC1: Detailed specification string
- RETAIL_DESC: Marketing/retail summary
- ITEM_FEATURES_1..20: Key feature bullets
"""

import os
import json
import re
from typing import List, Dict, Any

CACHE_DIR = os.path.join(os.path.dirname(__file__), ".cache")

def build_invoice_desc(mfr_name: str, brand_name: str, prod_name: str, mpn: str, attrs: List[Dict[str, str]]) -> str:
    """
    INVOICE_DESC formula: PROD_NAME + KEY_ATTRS + MPN
    Must be <= 40 characters, ALL CAPS.
    """
    key_terms = [prod_name.upper()]
    for attr in attrs:
        val = attr.get("val", "").upper()
        uom = attr.get("uom", "").upper()
        if val:
            key_terms.append(f"{val}{uom}")
    if mpn:
        key_terms.append(mpn.upper())
        
    full_str = " ".join(key_terms)
    if len(full_str) > 40:
        # Truncate or pick highest priority terms
        short_terms = [prod_name.upper()]
        for attr in attrs[:2]:
            val = attr.get("val", "").upper()
            uom = attr.get("uom", "").upper()
            if val:
                short_terms.append(f"{val}{uom}")
        short_terms.append(mpn.upper())
        full_str = " ".join(short_terms)
        if len(full_str) > 40:
            full_str = full_str[:40].rstrip()
            
    return full_str.upper()

def build_mobile_desc(mfr_name: str, brand_name: str, prod_name: str, mpn: str, attrs: List[Dict[str, str]]) -> str:
    """
    MOBILE_DESC target length: 60-80 characters.
    Formula: MFR_NAME BRAND_NAME, PROD_NAME, SERIES/ATTR, MPN
    """
    clean_brand = brand_name.replace("®", "").replace("™", "")
    parts = []
    if mfr_name and mfr_name != clean_brand:
        parts.append(mfr_name)
    parts.append(clean_brand)
    parts.append(prod_name)
    
    series_val = next((a["val"] for a in attrs if a["label"] == "Series"), None)
    if series_val:
        parts.append(series_val)
        
    if mpn:
        parts.append(mpn)
        
    desc_str = ", ".join(parts)
    if len(desc_str) < 60 and attrs:
        extra_attrs = [f"{a['val']} {a['uom']}".strip() for a in attrs if a["label"] != "Series"]
        if extra_attrs:
            desc_str += f", {', '.join(extra_attrs[:2])}"
            
    if len(desc_str) > 80:
        desc_str = desc_str[:77] + "..."
        
    return desc_str

def build_short_desc(brand_name: str, prod_name: str, mpn: str, attrs: List[Dict[str, str]]) -> str:
    """
    SHORT_DESC formula: BRAND_NAME SERIES PROD_NAME MPN ATTRS
    """
    parts = [brand_name]
    series_val = next((a["val"] for a in attrs if a["label"] == "Series"), None)
    if series_val:
        parts.append(series_val)
        
    if mpn:
        parts.append(mpn)
        
    parts.append(prod_name)
    
    attr_strs = [f"{a['val']} {a['uom']}".strip() for a in attrs if a["label"] != "Series"]
    if attr_strs:
        parts.append(f"({', '.join(attr_strs[:4])})")
        
    return " ".join(parts)

def build_long_desc1(brand_name: str, prod_name: str, mpn: str, attrs: List[Dict[str, str]], raw_desc: str) -> str:
    """
    LONG_DESC1 formula: Comprehensive structured description
    """
    parts = [f"{brand_name} {prod_name}"]
    if mpn:
        parts.append(f"Model {mpn}")
        
    attr_list = []
    for a in attrs:
        label = a["label"]
        val = a["val"]
        uom = a.get("uom", "")
        attr_list.append(f"{label}: {val} {uom}".strip())
        
    if attr_list:
        parts.append(f"Specifications: {'; '.join(attr_list)}")
        
    return ". ".join(parts) + "."

def run_descriptions() -> List[Dict[str, Any]]:
    norm_file = os.path.join(CACHE_DIR, "normalized_rows.json")
    if not os.path.exists(norm_file):
        import importlib
        s5 = importlib.import_module("5_normalize")
        s5.run_normalization()

    with open(norm_file, "r", encoding="utf-8") as f:
        rows = json.load(f)

    for row in rows:
        mfr_name = row.get("MANUFACTURER_NAME") or ""
        brand_name = row.get("BRAND_NAME") or ""
        prod_name = row.get("Product Name") or "Product"
        mpn = row.get("Mfg_Part_Num") or ""
        raw_desc = row.get("Part_Desc") or ""

        # Collect structured attrs
        attrs = []
        for i in range(1, 51):
            lbl = row.get(f"ATTRIBUTE_LABEL {i}")
            val = row.get(f"ATTRIBUTE_VALUE {i}")
            uom = row.get(f"ATTRIBUTE_UOM {i}")
            if lbl and val:
                attrs.append({"label": lbl, "val": str(val), "uom": str(uom) if uom else ""})

        row["INVOICE_DESC"] = build_invoice_desc(mfr_name, brand_name, prod_name, mpn, attrs)
        row["MOBILE_DESC"] = build_mobile_desc(mfr_name, brand_name, prod_name, mpn, attrs)
        row["SHORT_DESC"] = build_short_desc(brand_name, prod_name, mpn, attrs)
        row["LONG_DESC1"] = build_long_desc1(brand_name, prod_name, mpn, attrs, raw_desc)
        row["RETAIL_DESC"] = f"{brand_name} {prod_name} {mpn}".strip()

    with open(os.path.join(CACHE_DIR, "described_rows.json"), "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)

    print(f"[Stage 6: Describe] Built standard descriptions for {len(rows)} rows.")
    return rows

if __name__ == "__main__":
    run_descriptions()
