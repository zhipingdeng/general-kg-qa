from backend.app.rag.bm25_retriever import BM25Retriever


def test_bm25_build_and_search():
    docs = [
        {"text": "红色食品是指红色的食品", "entity_name": "红色食品", "id": 1},
        {"text": "大龙湫位于温州雁荡山", "entity_name": "大龙湫", "id": 2},
        {"text": "奥林匹克精神是团结", "entity_name": "奥林匹克精神", "id": 3},
    ]
    retriever = BM25Retriever()
    retriever.build_index(docs)
    results = retriever.search("红色食品", top_k=2)
    assert len(results) > 0
    assert results[0]["entity_name"] == "红色食品"


def test_bm25_empty():
    retriever = BM25Retriever()
    results = retriever.search("test", top_k=5)
    assert results == []
