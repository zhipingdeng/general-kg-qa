import httpx


class HyDEGenerator:
    def __init__(self, model_name: str, base_url: str, api_key: str):
        self.model_name = model_name
        self.base_url = base_url
        self.api_key = api_key

    def build_prompt(self, question: str) -> str:
        return f"请用一段话简洁地回答以下问题（不需要标注来源，直接给出答案内容）：\n{question}\n回答："

    async def generate(self, question: str) -> str:
        prompt = self.build_prompt(question)
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": self.model_name, "messages": [{"role": "user", "content": prompt}], "temperature": 0.3, "max_tokens": 256},
            )
            resp.raise_for_status()
            msg = resp.json()["choices"][0]["message"]
            content = (msg.get("content") or "").strip()
            if not content:
                reasoning = (msg.get("reasoning") or "").strip()
                if reasoning:
                    paragraphs = [p.strip() for p in reasoning.split("\n") if p.strip()]
                    content = "\n".join(paragraphs[-2:])
            return content or question
