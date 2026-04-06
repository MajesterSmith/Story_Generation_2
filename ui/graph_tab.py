import networkx as nx
import matplotlib
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtWidgets import QWidget, QVBoxLayout

from db import graph_repo


# Relationship → edge colour
REL_COLOURS = {
    "Ally":    "#22c55e",
    "Enemy":   "#ef4444",
    "Neutral": "#6b7280",
    "Fears":   "#a855f7",
    "Serves":  "#3b82f6",
    "Rivals":  "#f97316",
}
DEFAULT_EDGE_COLOUR = "#6b7280"

# Node type → colour & shape
NODE_COLOURS = {
    "faction": "#3b82f6",
    "npc":     "#c9a84c",
}


class GraphTab(QWidget):
    """Live-updating NetworkX relationship map embedded as a matplotlib canvas."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._world_id: int | None = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.fig, self.ax = plt.subplots(figsize=(10, 7))
        self.fig.patch.set_facecolor("#0d0f14")
        self.ax.set_facecolor("#0d0f14")

        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)

    # ── Public API ────────────────────────────────────────────────────────────

    def set_world(self, world_id: int):
        self._world_id = world_id
        self.refresh()

    def refresh(self):
        if self._world_id is None:
            return
        nodes = graph_repo.get_nodes(self._world_id)
        edges = graph_repo.get_edges(self._world_id)
        self._draw(nodes, edges)

    # ── Drawing ───────────────────────────────────────────────────────────────

    def _draw(self, nodes: list[dict], edges: list[dict]):
        self.ax.clear()
        self.ax.set_facecolor("#0d0f14")
        self.ax.axis("off")

        if not nodes:
            self.ax.text(
                0.5, 0.5, "No relationship data",
                ha="center", va="center", color="#6b7280",
                transform=self.ax.transAxes, fontsize=14,
            )
            self.canvas.draw()
            return

        G = nx.DiGraph()

        for n in nodes:
            G.add_node(n["label"], node_type=n["node_type"])

        edge_colours  = []
        edge_widths   = []
        edge_labels   = {}
        for e in edges:
            sl = e["source_label"]
            tl = e["target_label"]
            rel = e["relationship"]
            w   = float(e.get("weight", 0.5))
            G.add_edge(sl, tl, relationship=rel, weight=w)
            edge_colours.append(REL_COLOURS.get(rel, DEFAULT_EDGE_COLOUR))
            edge_widths.append(1.0 + w * 2.0)
            edge_labels[(sl, tl)] = rel

        # Layout
        try:
            pos = nx.spring_layout(G, seed=42, k=2.5)
        except Exception:
            pos = nx.circular_layout(G)

        # Draw edges
        nx.draw_networkx_edges(
            G, pos, ax=self.ax,
            edge_color=edge_colours,
            width=edge_widths,
            arrows=True,
            arrowsize=15,
            connectionstyle="arc3,rad=0.1",
        )

        # Separate faction vs NPC nodes
        f_nodes = [n["label"] for n in nodes if n["node_type"] == "faction"]
        p_nodes = [n["label"] for n in nodes if n["node_type"] == "npc"]

        if f_nodes:
            nx.draw_networkx_nodes(
                G, pos, nodelist=f_nodes, ax=self.ax,
                node_color=NODE_COLOURS["faction"],
                node_size=900, node_shape="h",
            )
        if p_nodes:
            nx.draw_networkx_nodes(
                G, pos, nodelist=p_nodes, ax=self.ax,
                node_color=NODE_COLOURS["npc"],
                node_size=550, node_shape="o",
            )

        # Labels
        nx.draw_networkx_labels(
            G, pos, ax=self.ax,
            font_color="#e2e8f0", font_size=8, font_weight="bold",
        )
        nx.draw_networkx_edge_labels(
            G, pos, edge_labels=edge_labels, ax=self.ax,
            font_color="#9ca3af", font_size=6.5,
            bbox=dict(boxstyle="round,pad=0.2", fc="#161b22", ec="none", alpha=0.7),
        )

        # Legend
        legend_items = [
            plt.Line2D([0], [0], color=c, linewidth=2.5, label=r)
            for r, c in REL_COLOURS.items()
        ]
        legend_items += [
            plt.scatter([], [], c=NODE_COLOURS["faction"], s=80,
                        marker="h", label="Faction"),
            plt.scatter([], [], c=NODE_COLOURS["npc"], s=60,
                        marker="o", label="NPC"),
        ]
        self.ax.legend(
            handles=legend_items, loc="lower left",
            facecolor="#161b22", edgecolor="#30363d",
            labelcolor="#c9d1d9", fontsize=7.5,
        )

        self.fig.tight_layout()
        self.canvas.draw()
