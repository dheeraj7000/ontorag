"""Neo4j database connection and query utilities."""

import logging
from typing import Any, Dict, List, Optional

from neo4j import AsyncDriver, AsyncGraphDatabase

from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class Neo4jConnection:
    """Async Neo4j connection manager."""

    def __init__(self):
        self._driver: Optional[AsyncDriver] = None

    async def connect(self) -> None:
        """Establish connection to Neo4j."""
        self._driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
        # Verify connectivity
        await self._driver.verify_connectivity()
        logger.info(f"Connected to Neo4j at {settings.neo4j_uri}")

    async def close(self) -> None:
        """Close the Neo4j connection."""
        if self._driver:
            await self._driver.close()
            logger.info("Neo4j connection closed")

    @property
    def driver(self) -> AsyncDriver:
        """Get the active driver instance."""
        if not self._driver:
            raise RuntimeError("Neo4j not connected. Call connect() first.")
        return self._driver

    async def execute_query(
        self, query: str, parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute a Cypher query and return results as list of dicts."""
        async with self.driver.session() as session:
            result = await session.run(query, parameters or {})
            records = await result.data()
            return records

    async def execute_write(
        self, query: str, parameters: Optional[Dict[str, Any]] = None
    ) -> None:
        """Execute a write Cypher query."""
        async with self.driver.session() as session:
            await session.run(query, parameters or {})

    async def get_node_count(self) -> int:
        """Get total number of nodes in the graph."""
        result = await self.execute_query("MATCH (n) RETURN count(n) as count")
        return result[0]["count"] if result else 0

    async def get_edge_count(self) -> int:
        """Get total number of relationships in the graph."""
        result = await self.execute_query(
            "MATCH ()-[r]->() RETURN count(r) as count"
        )
        return result[0]["count"] if result else 0

    async def health_check(self) -> bool:
        """Check if Neo4j is responsive."""
        try:
            result = await self.execute_query("RETURN 1 as ok")
            return result[0]["ok"] == 1
        except Exception as e:
            logger.error(f"Neo4j health check failed: {e}")
            return False


# Singleton instance
db = Neo4jConnection()
