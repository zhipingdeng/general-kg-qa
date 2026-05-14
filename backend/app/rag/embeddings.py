import httpx
import hashlib
import struct


class EmbeddingService:
    def __init__(self, base_url: str, model: str = "bge-m3"):
        self.base_url = base_url
        self.model = model
        self.dim = 1024

    async def embed(self, text: str) -> list[float]:
        if not text.strip():
            return self._fallback_embedding(text)
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    f"{self.base_url}/api/embeddings",
                    json={"model": self.model, "prompt": text},
                )
                resp.raise_for_status()
                return resp.json()["embedding"]
        except Exception:
            return self._fallback_embedding(text)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        results = []
        for text in texts:
            vec = await self.embed(text)
            results.append(vec)
        return results

    def _fallback_embedding(self, text: str) -> list[float]:
        hash_bytes = hashlib.sha512(text.encode()).digest()
        floats = struct.unpack(
            f"{len(hash_bytes) // 4}f",
            hash_bytes[: len(hash_bytes) // 4 * 4],
        )
        result = list(floats)
        while len(result) < self.dim:
            result.extend(result[: self.dim - len(result)])
        return result[: self.dim]
