"""
Stage 1: Deduplication Layer
Detects exact key duplicates and near-duplicate SKUs based on Mfg_Part_Num and Part_Desc.
Uses RapidFuzz for fuzzy string similarity comparison.
"""

import os
import json
from typing import List, Dict, Any
from rapidfuzz import fuzz

CACHE_DIR = os.path.join(os.path.dirname(__file__), ".cache")

def run_dedup(similarity_threshold: float = 90.0) -> List[Dict[str, Any]]:
    ingested_file = os.path.join(CACHE_DIR, "ingested_raw.json")
    if not os.path.exists(ingested_file):
        import importlib
        s0 = importlib.import_module("0_ingest")
        s0.run_ingest()
        
    with open(ingested_file, "r", encoding="utf-8") as f:
        rows = json.load(f)

    # Step 1: Exact key map
    mpn_map: Dict[str, List[int]] = {}
    for idx, row in enumerate(rows):
        mpn = row.get("Mfg_Part_Num")
        if mpn:
            mpn_clean = str(mpn).strip().upper()
            mpn_map.setdefault(mpn_clean, []).append(idx)

    # Step 2: Near-duplicate detection using Part_Desc similarity
    clusters: List[List[int]] = []
    visited = set()

    for i in range(len(rows)):
        if i in visited:
            continue

        row_i = rows[i]
        desc_i = (row_i.get("Part_Desc") or "").strip().lower()
        mpn_i = (row_i.get("Mfg_Part_Num") or "").strip().upper()
        
        current_cluster = [i]
        visited.add(i)

        # Check exact MPN duplicates first
        if mpn_i and len(mpn_map.get(mpn_i, [])) > 1:
            for other_idx in mpn_map[mpn_i]:
                if other_idx not in visited:
                    current_cluster.append(other_idx)
                    visited.add(other_idx)

        # Check fuzzy description similarity for close matches
        if desc_i and len(desc_i) > 5:
            for j in range(i + 1, len(rows)):
                if j in visited:
                    continue
                desc_j = (rows[j].get("Part_Desc") or "").strip().lower()
                if desc_j:
                    ratio = fuzz.token_sort_ratio(desc_i, desc_j)
                    if ratio >= similarity_threshold:
                        current_cluster.append(j)
                        visited.add(j)

        clusters.append(current_cluster)

    # Assign metadata
    duplicate_count = 0
    for cluster_id, cluster_indices in enumerate(clusters):
        is_dup = len(cluster_indices) > 1
        if is_dup:
            duplicate_count += len(cluster_indices) - 1
            
        for primary_flag, idx in enumerate(cluster_indices):
            rows[idx]["dedup_cluster_id"] = cluster_id
            rows[idx]["is_duplicate"] = is_dup
            rows[idx]["is_cluster_primary"] = (primary_flag == 0)

    with open(os.path.join(CACHE_DIR, "deduped_rows.json"), "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)

    print(f"[Stage 1: Dedup] Analyzed {len(rows)} items. Formed {len(clusters)} clusters ({duplicate_count} duplicates identified).")
    return rows

if __name__ == "__main__":
    run_dedup()
