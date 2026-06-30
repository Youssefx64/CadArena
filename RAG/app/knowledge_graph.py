"""Lightweight SQLite-backed Knowledge Graph for GraphRAG operations in ArchChat."""
from __future__ import annotations

import logging
import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)

class KnowledgeGraph:
    """Manages nodes and edges for building entity-relationship graphs of building codes and standards."""

    def __init__(self, db_path: str | None = None) -> None:
        if db_path is None:
            # Default to RAG/data/knowledge_graph.db
            data_dir = Path(__file__).resolve().parents[1] / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(data_dir / "knowledge_graph.db")
        
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Create nodes and edges tables if they do not exist."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS nodes (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS edges (
                    source TEXT NOT NULL,
                    target TEXT NOT NULL,
                    type TEXT NOT NULL,
                    PRIMARY KEY (source, target, type),
                    FOREIGN KEY (source) REFERENCES nodes(id) ON DELETE CASCADE,
                    FOREIGN KEY (target) REFERENCES nodes(id) ON DELETE CASCADE
                )
            """)
            conn.commit()

    def add_node(self, node_id: str, name: str, node_type: str) -> None:
        """Upsert a node into the graph."""
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO nodes (id, name, type) VALUES (?, ?, ?)",
                (node_id, name, node_type)
            )
            conn.commit()

    def add_edge(self, source: str, target: str, edge_type: str) -> None:
        """Insert a relationship between two nodes, creating placeholder nodes if missing."""
        # Ensure nodes exist
        self.add_node(source, source, "Entity")
        self.add_node(target, target, "Entity")

        with self._get_connection() as conn:
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO edges (source, target, type) VALUES (?, ?, ?)",
                    (source, target, edge_type)
                )
                conn.commit()
            except sqlite3.Error as e:
                logger.error(f"Error adding edge {source} -> {target}: {e}")

    def get_neighbors(self, node_id: str) -> List[Tuple[str, str, str]]:
        """Return all outgoing edges as (target_id, target_name, edge_type)."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT edges.target, nodes.name, edges.type 
                FROM edges 
                JOIN nodes ON edges.target = nodes.id 
                WHERE edges.source = ?
            """, (node_id,))
            return [(row[0], row[1], row[2]) for row in cursor.fetchall()]

    def search_nodes(self, query: str) -> List[Dict[str, str]]:
        """Perform text matching search on node names."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT id, name, type FROM nodes WHERE name LIKE ? LIMIT 20",
                (f"%{query}%",)
            )
            return [{"id": row[0], "name": row[1], "type": row[2]} for row in cursor.fetchall()]

    def retrieve_subgraph(self, seed_keywords: List[str], max_depth: int = 1) -> List[Dict[str, Any]]:
        """Retrieve nodes and edges connected to keywords within a specific depth."""
        retrieved_nodes: Dict[str, Dict[str, str]] = {}
        retrieved_edges: List[Dict[str, str]] = []
        visited = set()

        # Find matching seed nodes
        queue = []
        with self._get_connection() as conn:
            for keyword in seed_keywords:
                cursor = conn.execute(
                    "SELECT id, name, type FROM nodes WHERE name LIKE ?",
                    (f"%{keyword}%",)
                )
                for row in cursor.fetchall():
                    node_id = row[0]
                    retrieved_nodes[node_id] = {"id": node_id, "name": row[1], "type": row[2]}
                    queue.append((node_id, 0))

        # BFS expansion
        while queue:
            node_id, depth = queue.pop(0)
            if node_id in visited or depth >= max_depth:
                continue
            visited.add(node_id)

            neighbors = self.get_neighbors(node_id)
            for target_id, target_name, edge_type in neighbors:
                # Add node
                if target_id not in retrieved_nodes:
                    with self._get_connection() as conn:
                        cursor = conn.execute("SELECT type FROM nodes WHERE id = ?", (target_id,))
                        row = cursor.fetchone()
                        t_type = row[0] if row else "Entity"
                    retrieved_nodes[target_id] = {"id": target_id, "name": target_name, "type": t_type}

                # Add edge
                retrieved_edges.append({
                    "source": node_id,
                    "target": target_id,
                    "type": edge_type
                })

                if target_id not in visited:
                    queue.append((target_id, depth + 1))

        return {
            "nodes": list(retrieved_nodes.values()),
            "edges": retrieved_edges
        }

    def clear(self) -> None:
        """Clear all nodes and edges from the database."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM edges")
            conn.execute("DELETE FROM nodes")
            conn.commit()

# Global singleton helper
_kg_instance = None

def get_knowledge_graph() -> KnowledgeGraph:
    """Return the global cached Knowledge Graph instance."""
    global _kg_instance
    if _kg_instance is None:
        _kg_instance = KnowledgeGraph()
    return _kg_instance
