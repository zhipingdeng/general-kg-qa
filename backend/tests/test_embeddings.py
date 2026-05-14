import pytest
from app.rag.embeddings import EmbeddingService


@pytest.fixture
async def svc():
    from app.config import get_settings
    s = get_settings()
    return EmbeddingService(base_url=s.embedding_base_url, model=s.embedding_model)


async def test_single_embedding(svc):
    vec = await svc.embed("测试文本")
    assert len(vec) == 1024
    assert all(isinstance(v, float) for v in vec)


async def test_batch_embedding(svc):
    vecs = await svc.embed_batch(["文本1", "文本2", "文本3"])
    assert len(vecs) == 3
    assert all(len(v) == 1024 for v in vecs)


async def test_empty_text(svc):
    vec = await svc.embed("")
    assert len(vec) == 1024  # fallback
