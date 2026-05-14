"""RRF (Reciprocal Rank Fusion) for merging retrieval results."""


def rrf_fusion(
    result_lists: list[list[dict]],
    k: int = 60,
    top_k: int = 10,
) -> list[dict]:
    """Merge multiple ranked result lists using Reciprocal Rank Fusion.

    Args:
        result_lists: Each list is sorted by relevance (best first).
        k: RRF constant (default 60).
        top_k: Number of final results.

    Returns:
        Merged and re-ranked results.
    """
    scores: dict[str, float] = {}
    doc_map: dict[str, dict] = {}

    for results in result_lists:
        for rank, item in enumerate(results):
            doc_id = item.get("id") or item.get("entity_name", "")
            if not doc_id:
                continue
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
            if doc_id not in doc_map:
                doc_map[doc_id] = item

    ranked = sorted(scores.items(), key=lambda x: -x[1])[:top_k]
    results = []
    for doc_id, score in ranked:
        doc = doc_map[doc_id].copy()
        doc["rrf_score"] = score
        results.append(doc)
    return results
