"""Query rewriter - reformulate questions for better retrieval."""

import httpx
from app.config import get_settings


class QueryRewriter:
    def __init__(self, model_name: str = "", base_url: str = "", api_key: str = ""):
        settings = get_settings()
        self.model = model_name or settings.llm_model_name
        self.base_url = base_url or settings.llm_base_url
        self.api_key = api_key or settings.llm_api_key

    async def rewrite(self, question: str) -> list[str]:
        """Rewrite a question into multiple variants for retrieval.

        Returns the original question plus 1-2 rewritten variants.
        """
        prompt = f"""请将以下问题改写为2个不同表述方式，每行一个，只输出改写后的问题，不要编号：

原问题：{question}

改写："""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.5,
                        "max_tokens": 256,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                msg = data["choices"][0]["message"]
                text = (msg.get("content") or msg.get("reasoning") or "").strip()
                # Remove thinking tags if present
                if "<think>" in text:
                    import re
                    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
                variants = [
                    line.strip()
                    for line in text.split("\n")
                    if line.strip() and line.strip() != question
                ]
                return [question] + variants[:2]
        except Exception:
            return [question]
