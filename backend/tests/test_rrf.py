from backend.app.rag.rrf import RRF


def test_rrf_merge_two_lists():
    rrf = RRF(k=60)
    list_a = [{"id": 1}, {"id": 2}, {"id": 3}]
    list_b = [{"id": 2}, {"id": 4}, {"id": 1}]
    merged = rrf.merge([list_a, list_b], top_k=3)
    ids = [d["id"] for d in merged]
    assert 2 in ids
    assert merged[0]["id"] == 2  # appears in both


def test_rrf_empty():
    rrf = RRF()
    merged = rrf.merge([[], [{"id": 1}]], top_k=5)
    assert len(merged) == 1
