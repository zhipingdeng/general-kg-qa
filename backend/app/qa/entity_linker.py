"""Entity Linker - Extract known entities from questions using longest-match strategy."""


class EntityLinker:
    def __init__(self, mock_entities: list[str] | None = None):
        self._known_entities = mock_entities or []

    def load_from_neo4j(self, entities: list[str]) -> None:
        """Load known entity list (e.g. from Neo4j)."""
        self._known_entities = entities

    def extract_entities(self, question: str) -> list[str]:
        """Extract entities from question using longest-match strategy.

        For each known entity, find if it appears in the question.
        Sort matches by length descending so longer matches take priority.
        Non-overlapping greedy selection ensures no substring conflicts.
        """
        matches: list[tuple[int, str]] = []
        for entity in self._known_entities:
            idx = question.find(entity)
            if idx != -1:
                matches.append((len(entity), entity))

        matches.sort(reverse=True)

        result = []
        seen_positions: set[int] = set()
        for length, entity in matches:
            pos = question.find(entity)
            if all(p not in range(pos, pos + length) for p in seen_positions):
                result.append(entity)
                seen_positions.update(range(pos, pos + length))
        return result
