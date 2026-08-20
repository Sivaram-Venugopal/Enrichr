"""
Stage 2: Manufacturer & Brand Resolution Layer
Fuzzy matches Part_Manuf, brand fields, and MPN model prefixes against canonical lookup dictionary.
Resolves MANUFACTURER_NAME and BRAND_NAME (with ®/™), falling back to MANUFACTURER_NAME when no brand exists.
"""

import os
import json
import re
from typing import List, Dict, Any, Tuple
from rapidfuzz import process, fuzz

CACHE_DIR = os.path.join(os.path.dirname(__file__), ".cache")

# Built-in canonical dictionary derived from UniCat master list and ground truth data
CANONICAL_BRAND_MAP = {
    "FRIGIDAIRE": ("Rheem Manufacturing", "FRIGIDAIRE®"),
    "WHIRLPOOL": ("Whirlpool Corporation", "Whirlpool®"),
    "GE": ("General Electric Company", "GE®"),
    "GE APPLIANCES": ("General Electric Company", "GE®"),
    "LG": ("LG Electronics Inc.", "LG®"),
    "KITCHENAID": ("KitchenAid", "KitchenAid®"),
    "SPEED QUEEN": ("Alliance Laundry Systems LLC", "Speed Queen®"),
    "MILWAUKEE": ("Milwaukee Tool", "Milwaukee®"),
    "MILW": ("Milwaukee Tool", "Milwaukee®"),
    "DIABLO": ("Freud America, Inc.", "Diablo®"),
    "FREUD": ("Freud America, Inc.", "Freud®"),
    "3M": ("3M Company", "3M®"),
    "MIRKA": ("Mirka USA Inc.", "Mirka®"),
    "WERA": ("Wera Tools NA Inc.", "Wera®"),
    "EMSEAL": ("Emseal Joint Systems Ltd.", "EMSEAL®"),
    "REES": ("Rees Cast Stone Company", "Rees®"),
}

MODEL_PREFIX_MAP = {
    "PDSH": "FRIGIDAIRE",
    "WDTS": "WHIRLPOOL",
    "KDFM": "KITCHENAID",
    "KDTS": "KITCHENAID",
    "KDPS": "KITCHENAID",
    "PDT": "GE",
    "PDD": "GE",
    "LDPH": "LG",
    "DF70": "SPEED QUEEN",
    "DR70": "SPEED QUEEN",
    "DV20": "SPEED QUEEN",
    "DC50": "SPEED QUEEN",
    "FF70": "SPEED QUEEN",
    "TR70": "SPEED QUEEN",
    "TR50": "SPEED QUEEN",
    "3MABR": "3M",
    "DBD": "DIABLO",
    "DCB": "DIABLO",
    "49-94": "MILWAUKEE"
}

def clean_manuf_string(raw: str) -> str:
    if not raw:
        return ""
    cleaned = re.sub(r"\s*\([A-Za-z0-9]+\)\s*$", "", raw.strip())
    return cleaned

def resolve_mfr_brand(part_manuf: str, brand_hints: List[str], part_desc: str, mpn: str) -> Tuple[str, str, float]:
    """
    Returns (MANUFACTURER_NAME, BRAND_NAME, match_score)
    """
    clean_mfr = clean_manuf_string(part_manuf)
    mpn_upper = (mpn or "").upper()
    
    # Priority 1: MPN Model Prefix exact match
    for prefix, key in MODEL_PREFIX_MAP.items():
        if mpn_upper.startswith(prefix):
            mfr_name, brand_name = CANONICAL_BRAND_MAP[key]
            return mfr_name, brand_name, 100.0

    # Priority 2: Brand/Desc keyword match
    candidate_tokens = []
    if clean_mfr:
        candidate_tokens.append(clean_mfr)
    for b in brand_hints:
        if b:
            candidate_tokens.append(b)
            
    desc_upper = (part_desc or "").upper()

    best_match_key = None
    best_score = 0.0

    for key in CANONICAL_BRAND_MAP:
        if re.search(r'\b' + re.escape(key) + r'\b', desc_upper):
            score = 95.0
            if score > best_score:
                best_score = score
                best_match_key = key
                
        for token in candidate_tokens:
            score = fuzz.token_set_ratio(key, token.upper())
            if score > best_score and score >= 70.0:
                best_score = score
                best_match_key = key

    if best_match_key:
        mfr_name, brand_name = CANONICAL_BRAND_MAP[best_match_key]
        return mfr_name, brand_name, best_score
    else:
        mfr_name = clean_mfr if clean_mfr else "Generic Manufacturer"
        brand_name = mfr_name
        return mfr_name, brand_name, 50.0

def run_manufacturer_brand_resolution() -> List[Dict[str, Any]]:
    deduped_file = os.path.join(CACHE_DIR, "deduped_rows.json")
    if not os.path.exists(deduped_file):
        import importlib
        s1 = importlib.import_module("1_dedup")
        s1.run_dedup()

    with open(deduped_file, "r", encoding="utf-8") as f:
        rows = json.load(f)

    resolved_count = 0
    for row in rows:
        part_manuf = row.get("Part_Manuf") or ""
        brand_hints = [row.get("E1_Brand"), row.get("Unilog_Brand"), row.get("DIB_Brand")]
        part_desc = row.get("Part_Desc") or ""
        mpn = row.get("Mfg_Part_Num") or ""

        mfr_name, brand_name, score = resolve_mfr_brand(part_manuf, brand_hints, part_desc, mpn)

        row["MANUFACTURER_NAME"] = mfr_name
        row["BRAND_NAME"] = brand_name
        row["mfr_brand_match_score"] = score
        resolved_count += 1

    with open(os.path.join(CACHE_DIR, "mfr_brand_resolved.json"), "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)

    print(f"[Stage 2: Mfr/Brand] Successfully resolved manufacturer & brand for {resolved_count} rows.")
    return rows

if __name__ == "__main__":
    run_manufacturer_brand_resolution()
