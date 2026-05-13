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

    async def generate(self, question: str, subgraph: dict[str, Any]) -> str:
        """Call the LLM API to generate an answer.

        Args:
            question: The user's natural language question.
            subgraph: Dict with keys: entity, properties, relationships.

        Returns:
            The LLM's answer string.
        """
        prompt = self.build_prompt(question, subgraph)
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 512,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
