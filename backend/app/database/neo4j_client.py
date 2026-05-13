from neo4j import AsyncGraphDatabase
from typing import Any


class Neo4jClient:
    def __init__(self, uri: str, user: str, password: str):
        self._uri = uri
        self._user = user
        self._password = password
        self._driver = None

    async def connect(self) -> None:
        self._driver = AsyncGraphDatabase.driver(self._uri, auth=(self._user, self._password))
        await self._driver.verify_connectivity()

    async def close(self) -> None:
        if self._driver:
            await self._driver.close()
            self._driver = None

    async def execute(self, query: str, **params: Any) -> list[dict[str, Any]]:
        if not self._driver:
            raise RuntimeError("Not connected. Call connect() first.")
        async with self._driver.session() as session:
            result = await session.run(query, **params)
            return await result.data()
