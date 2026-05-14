"""Evaluation dataset - load and filter KgCLUE test data matching OwnThink entities."""

import json
from dataclasses import dataclass


@dataclass
class EvalSample:
    """Single evaluation sample."""
    question: str
    entity: str
    relation: str
    reference_answer: str


def load_kgclue_dataset(
    kgclue_path: str,
    entity_names: set[str] | None = None,
    max_samples: int = 200,
) -> list[EvalSample]:
    """Load KgCLUE test data, optionally filtering to known entities.

    KgCLUE format:
        {"id": 0, "question": "...", "answer": "实体 ||| 关系 ||| 答案"}

    Args:
        kgclue_path: Path to KgCLUE test_public.json.
        entity_names: Set of known entity names to filter. If None, load all.
        max_samples: Maximum number of samples to return.

    Returns:
        List of EvalSample.
    """
    samples = []
    with open(kgclue_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue

            answer_str = row.get("answer", "")
            parts = [p.strip() for p in answer_str.split("|||")]
            if len(parts) < 3:
                continue

            entity, relation, answer = parts[0], parts[1], parts[2]

            # Filter to known entities
            if entity_names and entity not in entity_names:
                continue

            samples.append(EvalSample(
                question=row["question"],
                entity=entity,
                relation=relation,
                reference_answer=answer,
            ))

            if len(samples) >= max_samples:
                break

    return samples


def load_ownthink_entity_names(neo4j_client) -> set[str]:
    """Load all entity names from Neo4j OwnThink data."""
    import asyncio

    async def _fetch():
        result = await neo4j_client.execute(
            "MATCH (n:Entity {source: 'ownthink'}) RETURN n.name AS name"
        )
        return {r["name"] for r in result if r.get("name")}

    return asyncio.run(_fetch())
