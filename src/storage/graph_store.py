"""
graph_store.py
--------------
Builds and manages a lightweight knowledge / evidence graph using NetworkX.
Nodes represent content chunks; edges represent semantic relationships.
The graph is persisted as JSON to graph/evidence_graph.json.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

import networkx as nx

from src.models.schemas import EvidenceGraph, GraphEdge, GraphNode, ModalityType

logger = logging.getLogger(__name__)

DEFAULT_GRAPH_PATH = "graph/evidence_graph.json"


class GraphStore:
    """
    In-memory graph built on top of NetworkX, serialised to/from JSON.

    Relationships captured:
    - 'follows'       — sequential chunks (e.g. transcript segments)
    - 'co_occurring'  — content sharing named entities or keywords
    - 'derived_from'  — frame description derived from a specific video frame
    """

    def __init__(self, graph_path: str = DEFAULT_GRAPH_PATH) -> None:
        self.graph_path = Path(graph_path)
        self.graph_path.parent.mkdir(parents=True, exist_ok=True)
        self._graph: nx.DiGraph = nx.DiGraph()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self) -> None:
        """Serialise the graph to JSON."""
        data = nx.node_link_data(self._graph)
        self.graph_path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        logger.info(
            "Graph saved → %s (%d nodes, %d edges)",
            self.graph_path, self._graph.number_of_nodes(), self._graph.number_of_edges(),
        )

    def load(self) -> None:
        """Load the graph from JSON (if it exists)."""
        if not self.graph_path.exists():
            logger.info("No existing graph found at %s — starting fresh.", self.graph_path)
            return
        data = json.loads(self.graph_path.read_text(encoding="utf-8"))
        self._graph = nx.node_link_graph(data, directed=True)
        logger.info(
            "Graph loaded ← %s (%d nodes, %d edges)",
            self.graph_path, self._graph.number_of_nodes(), self._graph.number_of_edges(),
        )

    # ------------------------------------------------------------------
    # Graph construction
    # ------------------------------------------------------------------

    def add_node(self, node: GraphNode) -> None:
        """Add or update a node in the graph."""
        self._graph.add_node(
            node.node_id,
            label=node.label,
            modality=node.modality,
            content_summary=node.content_summary,
            **node.metadata,
        )

    def add_edge(self, edge: GraphEdge) -> None:
        """Add or update a directed edge in the graph."""
        self._graph.add_edge(
            edge.source_id,
            edge.target_id,
            edge_id=edge.edge_id,
            relation=edge.relation,
            weight=edge.weight,
        )

    def link_sequential(self, node_ids: List[str], relation: str = "follows") -> None:
        """Link a list of node IDs in sequence (n → n+1)."""
        for i in range(len(node_ids) - 1):
            self._graph.add_edge(
                node_ids[i], node_ids[i + 1],
                relation=relation, weight=1.0,
            )

    # ------------------------------------------------------------------
    # Querying
    # ------------------------------------------------------------------

    def get_neighbors(
        self,
        node_id: str,
        depth: int = 1,
        relation_filter: Optional[str] = None,
    ) -> List[Dict]:
        """
        Return all neighbors of a node up to `depth` hops away.

        Parameters
        ----------
        node_id : str
            Starting node.
        depth : int
            BFS depth limit.
        relation_filter : str, optional
            If set, only traverse edges with this relation type.

        Returns
        -------
        List[Dict]
            List of neighbor node attribute dicts.
        """
        if node_id not in self._graph:
            return []

        visited = set()
        frontier = {node_id}
        for _ in range(depth):
            next_frontier = set()
            for nid in frontier:
                for successor in self._graph.successors(nid):
                    edge_data = self._graph.get_edge_data(nid, successor, default={})
                    if relation_filter and edge_data.get("relation") != relation_filter:
                        continue
                    if successor not in visited:
                        next_frontier.add(successor)
            visited.update(next_frontier)
            frontier = next_frontier

        return [
            {"node_id": n, **self._graph.nodes[n]}
            for n in visited
            if n in self._graph.nodes
        ]

    def to_schema(self) -> EvidenceGraph:
        """Export the graph as a validated EvidenceGraph schema object."""
        nodes = [
            GraphNode(
                node_id=nid,
                label=data.get("label", nid),
                modality=data.get("modality", ModalityType.TEXT),
                content_summary=data.get("content_summary", ""),
                metadata={k: v for k, v in data.items() if k not in {"label", "modality", "content_summary"}},
            )
            for nid, data in self._graph.nodes(data=True)
        ]
        edges = [
            GraphEdge(
                source_id=u,
                target_id=v,
                relation=data.get("relation", "related"),
                weight=data.get("weight", 1.0),
            )
            for u, v, data in self._graph.edges(data=True)
        ]
        return EvidenceGraph(nodes=nodes, edges=edges)

    @property
    def node_count(self) -> int:
        return self._graph.number_of_nodes()

    @property
    def edge_count(self) -> int:
        return self._graph.number_of_edges()
