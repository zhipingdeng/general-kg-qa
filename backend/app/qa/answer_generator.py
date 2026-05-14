"""Answer Generator - Build prompts and call LLM to generate answers."""

import httpx
from typing import Any


class AnswerGenerator:
    def __init__(self, model_name: str, base_url: str, api_key: str):
        self.model_name = model_name
        self.base_url = base_url
        self.api_key = api_key

    def build_prompt(self, question: str, subgraph: dict[str, Any]) -> str:
        """Build a prompt from the question and retrieved subgraph context.

        Args:
            question: The user's natural language question.
            subgraph: Dict with keys: entity, properties, relationships.

        Returns:
            A formatted prompt string for the LLM.
        """
        entity = subgraph["entity"]
        props = subgraph.get("properties", {})
        rels = subgraph.get("relationships", [])

        context_parts = [f"实体: {entity}"]
        if props:
            for k, v in props.items():
                context_parts.append(f"  {k}: {v}")
        if rels:
            context_parts.append("  关系:")
            for r in rels:
                context_parts.append(
                    f"    {entity} --[{r['relation']}]--> {r['target']}"
                )

        context = "\n".join(context_parts)
        return f"""基于以下知识图谱信息回答用户问题。如果信息不足以回答，请说明。

知识图谱信息:
{context}

用户问题: {question}

请用简洁的中文回答:"""

    async def generate_with_context(self, question: str, context: str) -> str:
        """Generate answer using retrieved context documents."""
        prompt = f"""基于以下检索到的文档信息回答用户问题。引用具体文档编号如 [1] [2]。
如果信息不足，请说明。

检索到的文档:
{context}

用户问题: {question}

请用简洁的中文回答:"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": self.model_name, "messages": [{"role": "user", "content": prompt}], "temperature": 0.3, "max_tokens": 2048},
            )
            response.raise_for_status()
            msg = response.json()["choices"][0]["message"]
            content = (msg.get("content") or "").strip()
            if not content:
                reasoning = (msg.get("reasoning") or "").strip()
                if reasoning:
                    paragraphs = [p.strip() for p in reasoning.split("\n") if p.strip()]
                    content = "\n".join(paragraphs[-3:])
            return content or "抱歉，LLM 未能生成回答。"

    async def generate(self, question: str, subgraph: dict[str, Any]) -> str:
        """Call the LLM API to generate an answer.

        Handles thinking models (e.g. Qwen3) that put the answer in
        the ``reasoning`` field when ``content`` is empty.

        Args:
            question: The user's natural language question.
            subgraph: Dict with keys: entity, properties, relationships.

        Returns:
            The LLM's answer string.
        """
        prompt = self.build_prompt(question, subgraph)
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 2048,
                },
            )
            response.raise_for_status()
            data = response.json()
            msg = data["choices"][0]["message"]

            # Prefer content; fall back to reasoning (thinking models)
            content = (msg.get("content") or "").strip()
            if not content:
                reasoning = (msg.get("reasoning") or "").strip()
                if reasoning:
                    # Extract the last paragraph as the actual answer
                    # (thinking models put reasoning first, answer last)
                    paragraphs = [p.strip() for p in reasoning.split("\n") if p.strip()]
                    # Take last 1-3 paragraphs as the answer
                    answer_start = max(0, len(paragraphs) - 3)
                    content = "\n".join(paragraphs[answer_start:])

            return content or "抱歉，LLM 未能生成回答。"
