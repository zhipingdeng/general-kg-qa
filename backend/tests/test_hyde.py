from backend.app.rag.hyde import HyDEGenerator


def test_hyde_build_prompt():
    gen = HyDEGenerator.__new__(HyDEGenerator)
    prompt = gen.build_prompt("红色食品是什么？")
    assert "红色食品" in prompt
    assert "请用一段话" in prompt
