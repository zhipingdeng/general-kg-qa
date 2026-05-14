from fastapi import APIRouter, Depends, Request
from app.api.v1.auth import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/knowledge/graph")
async def get_knowledge_graph(
    request: Request,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
):
    """Return nodes and edges for D3 visualization."""
    neo4j = request.app.state.neo4j
    
    # Get nodes
    nodes_result = await neo4j.execute(
        "MATCH (n:Entity {source: 'ownthink'}) "
        "RETURN n.name AS name, n.描述 AS desc, n.标签 AS tag "
        "LIMIT $limit",
        limit=limit,
    )
    nodes = [
        {"id": r["name"], "name": r["name"], "desc": r.get("desc", ""), "tag": r.get("tag", "")}
        for r in nodes_result
    ]

    # Get edges (relationships between these nodes)
    names = [n["name"] for n in nodes]
    edges_result = await neo4j.execute(
        "MATCH (a:Entity)-[r]->(b:Entity) "
        "WHERE a.name IN $names AND b.name IN $names "
        "RETURN a.name AS source, b.name AS target, type(r) AS rel_type "
        "LIMIT 500",
        names=names,
    )
    edges = [
        {"source": r["source"], "target": r["target"], "type": r["rel_type"]}
        for r in edges_result
    ]

    return {"nodes": nodes, "edges": edges}
