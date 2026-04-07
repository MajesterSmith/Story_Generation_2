import networkx as nx
import matplotlib
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QToolTip
from PyQt6.QtCore import pyqtSignal, QPoint

from db import world_repo

# Location type → colour & shape
# Options for shape: 'o' (circle), 's' (square), 'h' (hexagon), '^' (triangle), 'p' (pentagon)
TYPE_STYLES = {
    "settlement": {"color": "#3b82f6", "shape": "s", "size": 800},
    "wilderness": {"color": "#10b981", "shape": "o", "size": 600},
    "dungeon":    {"color": "#ef4444", "shape": "^", "size": 750},
    "landmark":   {"color": "#a855f7", "shape": "p", "size": 700},
}
DEFAULT_STYLE = {"color": "#6b7280", "shape": "o", "size": 600}
CURRENT_LOC_COLOR = "#facc15"  # Gold for "You Are Here"


class MapTab(QWidget):
    """
    Interactive World Map showing locations and connections.
    Supports hovering for descriptions and clicking to travel.
    """

    location_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._world_id: int | None = None
        self._current_location: str | None = None
        self._nodes_pos = {}
        self._node_artist = None
        self._locations_data = {}

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.fig, self.ax = plt.subplots(figsize=(10, 7))
        self.fig.patch.set_facecolor("#0d0f14")
        self.ax.set_facecolor("#0d0f14")

        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)

        # Connect events
        self.canvas.mpl_connect("motion_notify_event", self._on_hover)
        self.canvas.mpl_connect("button_press_event", self._on_click)

    # ── Public API ────────────────────────────────────────────────────────────

    def set_world(self, world_id: int, current_location: str = ""):
        self._world_id = world_id
        self._current_location = current_location
        self.refresh()

    def refresh(self):
        if self._world_id is None:
            return
        
        # 1. Fetch data
        locations   = world_repo.get_all_locations(self._world_id)
        connections = world_repo.get_connections(self._world_id)
        
        self._locations_data = {loc["name"]: loc for loc in locations}
        self._draw(locations, connections)

    # ── Internal Drawing ──────────────────────────────────────────────────────

    def _draw(self, locations: list[dict], connections: list[dict]):
        self.ax.clear()
        self.ax.axis("off")

        if not locations:
            self.ax.text(0.5, 0.5, "World has no mapped locations",
                         ha="center", va="center", color="#6b7280",
                         transform=self.ax.transAxes, fontsize=14)
            self.canvas.draw()
            return

        G = nx.Graph()
        for loc in locations:
            G.add_node(loc["name"], type=loc.get("type", "settlement"))

        for conn in connections:
            G.add_edge(conn["from_name"], conn["to_name"], 
                       desc=conn.get("description", ""))

        # Stable layout (seeded)
        self._nodes_pos = nx.spring_layout(G, seed=42, k=1.5)

        # Draw Edges
        nx.draw_networkx_edges(
            G, self._nodes_pos, ax=self.ax,
            edge_color="#21262d", width=1.5, alpha=0.6
        )

        # Draw Nodes by type
        # We'll store the node artists to check for hits during hover/click
        self._node_artists = []
        for loc_type, style in TYPE_STYLES.items():
            nodelist = [n for n, d in G.nodes(data=True) if d["type"] == loc_type]
            if not nodelist: continue
            
            # Highlight current location if it matches this type
            node_colors = []
            for n in nodelist:
                if n == self._current_location:
                    node_colors.append(CURRENT_LOC_COLOR)
                else:
                    node_colors.append(style["color"])

            artist = nx.draw_networkx_nodes(
                G, self._nodes_pos, nodelist=nodelist, ax=self.ax,
                node_color=node_colors,
                node_size=style["size"],
                node_shape=style["shape"],
                edgecolors="#0d0f14", linewidths=1
            )
            self._node_artists.append(artist)

        # Labels
        nx.draw_networkx_labels(
            G, self._nodes_pos, ax=self.ax,
            font_color="#8b949e", font_size=9, font_weight="bold",
            verticalalignment="bottom"
        )

        # Legend
        legend_items = [
            plt.scatter([], [], c=s["color"], s=60, marker=s["shape"], label=t.capitalize())
            for t, s in TYPE_STYLES.items()
        ]
        legend_items.append(plt.scatter([], [], c=CURRENT_LOC_COLOR, s=80, marker="o", label="Current Location"))
        
        self.ax.legend(
            handles=legend_items, loc="upper right",
            facecolor="#161b22", edgecolor="#30363d",
            labelcolor="#c9d1d9", fontsize=8
        )

        self.fig.tight_layout()
        self.canvas.draw()

    # ── Interaction ───────────────────────────────────────────────────────────

    def _on_hover(self, event):
        """Show location description on hover."""
        if event.inaxes != self.ax:
            return

        # Find which node is under the mouse
        label = self._get_node_at_pos(event.xdata, event.ydata)
        if label:
            loc = self._locations_data.get(label)
            if loc:
                text = f"<b>{label}</b><br/>Type: {loc['type']}<br/>Danger: {loc['danger_level']}<hr/>{loc['description']}"
                QToolTip.showText(self.canvas.mapToGlobal(QPoint(int(event.x), int(self.canvas.height() - event.y))), text)
        else:
            QToolTip.hideText()

    def _on_click(self, event):
        """Emit signal to travel to location."""
        if event.inaxes != self.ax or event.button != 1:
            return

        label = self._get_node_at_pos(event.xdata, event.ydata)
        if label and label != self._current_location:
            self.location_selected.emit(label)

    def _get_node_at_pos(self, x, y):
        """Helper to find the node label at a given canvas coordinate."""
        if x is None or y is None: return None
        
        threshold = 0.1  # Detection radius
        for label, pos in self._nodes_pos.items():
            dx = pos[0] - x
            dy = pos[1] - y
            if (dx*dx + dy*dy)**0.5 < threshold:
                return label
        return None
