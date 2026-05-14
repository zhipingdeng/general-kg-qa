class RRF:
    def __init__(self, k: int = 60):
        self.k = k

    def merge(self, result_lists: list[list[dict]], top_k: int = 10) -> list[dict]:
        scores: dict = {}
        for result_list in result_lists:
            for rank, doc in enumerate(result_list):
                doc_id = doc.get("id") or doc.get("entity_name", "")
                if doc_id:
                    scores[doc_id] = scores.get(doc_id, 0) + 1 / (self.k + rank + 1)
        sorted_ids = sorted(scores, key=lambda x: scores[x], reverse=True)[:top_k]
        doc_map = {}
        for rl in result_lists:
            for d in rl:
                did = d.get("id") or d.get("entity_name", "")
                if did:
                    doc_map[did] = d
        result = []
        for doc_id in sorted_ids:
            doc = doc_map[doc_id].copy()
            doc["rrf_score"] = scores[doc_id]
            result.append(doc)
        return result
