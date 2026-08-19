"""
GNN Trust Scoring Model — uses Graph Attention Networks (GAT) to propagate
confidence through the knowledge graph via message passing.

Assigns trust_score (0-1) to all nodes and edges based on:
- Extraction confidence
- Number of supporting sources
- Neighborhood agreement (message passing)

Optimized for CPU (t2.micro): small hidden dims, full-batch training.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# Model save path
MODEL_PATH = Path("models/trust_gnn.pt")


class TrustFeatureExtractor:
    """Converts Neo4j graph data into feature tensors for the GNN."""

    def __init__(self):
        # Feature dimensions
        self.entity_type_map: Dict[str, int] = {}
        self.num_features = 8  # Final feature vector size per node

    def build_features(
        self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]
    ) -> Tuple[Any, Any, Any, List[str]]:
        """
        Convert graph data to PyG tensors.

        Returns: (node_features, edge_index, edge_features, node_ids)
        """
        import torch

        # Build entity type mapping
        entity_types = list(set(n.get("entity_type", "Unknown") for n in nodes))
        self.entity_type_map = {t: i for i, t in enumerate(entity_types)}

        node_ids = [n["name"] for n in nodes]
        node_id_map = {name: idx for idx, name in enumerate(node_ids)}

        # Node features: [type_onehot..., confidence, source_count, degree]
        num_nodes = len(nodes)
        features = np.zeros((num_nodes, self.num_features), dtype=np.float32)

        for i, node in enumerate(nodes):
            # One-hot entity type (use modulo if more types than feature slots)
            type_idx = self.entity_type_map.get(node.get("entity_type", ""), 0)
            features[i, type_idx % 4] = 1.0  # First 4 dims for type

            # Extraction confidence
            features[i, 4] = float(node.get("extraction_confidence", 0.5))

            # Source count (normalized)
            features[i, 5] = min(float(node.get("source_count", 1)) / 5.0, 1.0)

            # Current trust score (if exists)
            features[i, 6] = float(node.get("trust_score", 0.5))

            # Placeholder for degree (computed below)
            features[i, 7] = 0.0

        # Build edge index
        src_indices = []
        tgt_indices = []
        edge_features_list = []

        for edge in edges:
            src_name = edge.get("source_name", "")
            tgt_name = edge.get("target_name", "")

            if src_name in node_id_map and tgt_name in node_id_map:
                src_idx = node_id_map[src_name]
                tgt_idx = node_id_map[tgt_name]

                # Bidirectional edges for message passing
                src_indices.extend([src_idx, tgt_idx])
                tgt_indices.extend([tgt_idx, src_idx])

                conf = float(edge.get("extraction_confidence", 0.5))
                edge_features_list.extend([conf, conf])

        # Compute degree feature
        for idx in src_indices + tgt_indices:
            features[idx, 7] = min(features[idx, 7] + 1.0 / 10.0, 1.0)

        edge_index = torch.tensor([src_indices, tgt_indices], dtype=torch.long)
        node_features = torch.tensor(features, dtype=torch.float)
        edge_feat = torch.tensor(edge_features_list, dtype=torch.float).unsqueeze(1)

        return node_features, edge_index, edge_feat, node_ids


class TrustGNN:
    """
    Graph Attention Network for trust scoring.

    Architecture:
    - 2-layer GAT (Graph Attention Network)
    - Hidden dim: 32 (CPU-optimized for small graphs)
    - Output: trust score per node [0, 1]
    """

    def __init__(self, in_features: int = 8, hidden_dim: int = 32):
        self.in_features = in_features
        self.hidden_dim = hidden_dim
        self.model = None
        self._build_model()

    def _build_model(self):
        """Build the GAT model."""
        try:
            import torch.nn as nn
            import torch.nn.functional as functional
            from torch_geometric.nn import GATConv

            class GATTrustModel(nn.Module):
                def __init__(self, in_features, hidden_dim):
                    super().__init__()
                    self.conv1 = GATConv(in_features, hidden_dim, heads=2, concat=True)
                    self.conv2 = GATConv(hidden_dim * 2, hidden_dim, heads=1, concat=False)
                    self.classifier = nn.Sequential(
                        nn.Linear(hidden_dim, 16),
                        nn.ReLU(),
                        nn.Linear(16, 1),
                        nn.Sigmoid(),
                    )

                def forward(self, x, edge_index):
                    x = functional.elu(self.conv1(x, edge_index))
                    x = functional.dropout(x, p=0.3, training=self.training)
                    x = functional.elu(self.conv2(x, edge_index))
                    return self.classifier(x).squeeze(-1)

            self.model = GATTrustModel(self.in_features, self.hidden_dim)
            logger.info("GNN Trust model built (GAT 2-layer)")

        except ImportError:
            logger.warning(
                "PyTorch Geometric not available. GNN trust scoring disabled. "
                "Install: pip install torch torch-geometric"
            )
            self.model = None

    def train_model(
        self,
        node_features,
        edge_index,
        pseudo_labels,
        epochs: int = 200,
        lr: float = 0.01,
    ) -> Dict[str, float]:
        """
        Train the GNN using pseudo-labels (heuristic-based).

        Pseudo-labels are generated from:
        - extraction_confidence (high = trusted)
        - number of sources (more = trusted)
        - consistency with neighbors

        Returns training metrics.
        """
        if self.model is None:
            return {"error": "Model not available"}

        import torch
        import torch.nn.functional as functional

        # Set CPU threading limit for t2.micro
        torch.set_num_threads(2)

        optimizer = torch.optim.Adam(self.model.parameters(), lr=lr, weight_decay=5e-4)
        self.model.train()

        best_loss = float("inf")
        for epoch in range(epochs):
            optimizer.zero_grad()
            out = self.model(node_features, edge_index)
            loss = functional.binary_cross_entropy(out, pseudo_labels)
            loss.backward()
            optimizer.step()

            if loss.item() < best_loss:
                best_loss = loss.item()

            if (epoch + 1) % 50 == 0:
                logger.info(f"GNN Training epoch {epoch + 1}/{epochs}, loss: {loss.item():.4f}")

        return {"final_loss": loss.item(), "best_loss": best_loss, "epochs": epochs}

    def predict(self, node_features, edge_index) -> Optional[List[float]]:
        """Predict trust scores for all nodes."""
        if self.model is None:
            return None

        import torch

        self.model.eval()
        with torch.no_grad():
            scores = self.model(node_features, edge_index)
            return scores.numpy().tolist()

    def save(self, path: Optional[Path] = None):
        """Save model weights."""
        if self.model is None:
            return

        import torch

        save_path = path or MODEL_PATH
        save_path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(self.model.state_dict(), save_path)
        logger.info(f"GNN model saved to {save_path}")

    def load(self, path: Optional[Path] = None) -> bool:
        """Load model weights. Returns True if successful."""
        if self.model is None:
            return False

        import torch

        load_path = path or MODEL_PATH
        if not load_path.exists():
            logger.warning(f"No saved model at {load_path}")
            return False

        self.model.load_state_dict(torch.load(load_path, map_location="cpu"))
        logger.info(f"GNN model loaded from {load_path}")
        return True


def generate_pseudo_labels(nodes: List[Dict[str, Any]]) -> Any:
    """
    Generate pseudo-labels for GNN training based on heuristics.

    Heuristics:
    - High extraction confidence → high trust
    - Multiple source documents → high trust
    - Consistent with neighbors → high trust
    """
    import torch

    labels = []
    for node in nodes:
        confidence = float(node.get("extraction_confidence", 0.5))
        source_count = float(node.get("source_count", 1))

        # Heuristic trust score
        score = (
            0.6 * confidence  # Primary: extraction confidence
            + 0.3 * min(source_count / 3.0, 1.0)  # Bonus for multiple sources
            + 0.1 * 0.5  # Base prior
        )
        labels.append(min(max(score, 0.0), 1.0))

    return torch.tensor(labels, dtype=torch.float)


class TrustScoringPipeline:
    """
    Full pipeline: fetch graph from Neo4j → compute features → train/predict → update scores.
    """

    def __init__(self):
        self.feature_extractor = TrustFeatureExtractor()
        self.gnn = TrustGNN()

    async def update_trust_scores(self, db) -> Dict[str, Any]:
        """
        Fetch the graph, train GNN, and update trust scores in Neo4j.

        Returns pipeline metrics.
        """
        # Fetch all entities and relations from Neo4j
        nodes = await db.execute_query(
            "MATCH (n:Entity) "
            "RETURN n.name as name, n.entity_type as entity_type, "
            "n.extraction_confidence as extraction_confidence, "
            "n.trust_score as trust_score, "
            "size([(n)<-[:EXTRACTED_FROM]-() | 1]) as source_count"
        )

        edges = await db.execute_query(
            "MATCH (src:Entity)-[r]->(tgt:Entity) "
            "RETURN src.name as source_name, tgt.name as target_name, "
            "r.extraction_confidence as extraction_confidence, "
            "type(r) as relation_type"
        )

        if len(nodes) < 3:
            return {"status": "skipped", "reason": "Too few nodes for GNN training"}

        # Build features
        node_features, edge_index, edge_feat, node_ids = (
            self.feature_extractor.build_features(nodes, edges)
        )

        # Generate pseudo-labels and train
        pseudo_labels = generate_pseudo_labels(nodes)
        metrics = self.gnn.train_model(node_features, edge_index, pseudo_labels)

        # Predict trust scores
        scores = self.gnn.predict(node_features, edge_index)
        if scores is None:
            return {"status": "error", "reason": "Prediction failed"}

        # Update Neo4j with new trust scores
        updated = 0
        for node_name, score in zip(node_ids, scores):
            await db.execute_write(
                "MATCH (n:Entity {name: $name}) SET n.trust_score = $score",
                {"name": node_name, "score": float(score)},
            )
            updated += 1

        # Save model
        self.gnn.save()

        return {
            "status": "completed",
            "nodes_scored": updated,
            "training_metrics": metrics,
            "score_range": {
                "min": round(min(scores), 3),
                "max": round(max(scores), 3),
                "mean": round(sum(scores) / len(scores), 3),
            },
        }
