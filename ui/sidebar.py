from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QFrame, QScrollArea, QSizePolicy,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


def _section_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("lbl_section")
    return lbl


def _separator() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setFrameShadow(QFrame.Shadow.Sunken)
    return f


class SidebarWidget(QWidget):
    """Right-hand sidebar showing player stats, active quest, and inventory."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar_frame")
        self.setFixedWidth(260)
        self._build_ui()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(14, 16, 14, 16)
        layout.setSpacing(12)

        # ── Player header
        self.lbl_player_name = QLabel("—")
        self.lbl_player_name.setObjectName("lbl_player_name")
        self.lbl_location    = QLabel("Unknown")
        self.lbl_location.setStyleSheet("color:#8b949e; font-size:11px;")
        layout.addWidget(self.lbl_player_name)
        layout.addWidget(self.lbl_location)
        layout.addWidget(_separator())

        # ── Stats
        layout.addWidget(_section_label("STATS"))
        stats_frame = QFrame()
        stats_frame.setObjectName("card")
        stats_l = QVBoxLayout(stats_frame)
        stats_l.setContentsMargins(10, 10, 10, 10)
        stats_l.setSpacing(8)

        # HP bar
        hp_row = QHBoxLayout()
        hp_row.addWidget(QLabel("HP"))
        self.hp_bar = QProgressBar()
        self.hp_bar.setObjectName("hp_bar")
        self.hp_bar.setRange(0, 100)
        self.hp_bar.setValue(100)
        self.hp_bar.setFixedHeight(8)
        self.hp_bar.setTextVisible(False)
        hp_row.addWidget(self.hp_bar)
        self.lbl_hp = QLabel("100 / 100")
        self.lbl_hp.setStyleSheet("color:#4ade80; font-size:11px; min-width:72px;")
        hp_row.addWidget(self.lbl_hp)
        stats_l.addLayout(hp_row)

        # STR / INT / AGI
        attr_row = QHBoxLayout()
        self.lbl_str = self._stat_pill("STR", 10)
        self.lbl_int = self._stat_pill("INT", 10)
        self.lbl_agi = self._stat_pill("AGI", 10)
        attr_row.addWidget(self.lbl_str)
        attr_row.addWidget(self.lbl_int)
        attr_row.addWidget(self.lbl_agi)
        stats_l.addLayout(attr_row)

        # Gold
        self.lbl_gold = QLabel("◈  50 gold")
        self.lbl_gold.setStyleSheet("color:#c9a84c; font-size:12px; font-weight:bold;")
        stats_l.addWidget(self.lbl_gold)

        layout.addWidget(stats_frame)
        layout.addWidget(_separator())

        # ── Quest
        layout.addWidget(_section_label("ACTIVE QUEST"))
        quest_frame = QFrame()
        quest_frame.setObjectName("card")
        quest_l = QVBoxLayout(quest_frame)
        quest_l.setContentsMargins(10, 10, 10, 10)
        quest_l.setSpacing(6)
        self.lbl_quest_title = QLabel("None")
        self.lbl_quest_title.setWordWrap(True)
        self.lbl_quest_title.setStyleSheet("color:#c9d1d9; font-weight:bold; font-size:12px;")
        self.lbl_quest_obj   = QLabel("")
        self.lbl_quest_obj.setWordWrap(True)
        self.lbl_quest_obj.setStyleSheet("color:#8b949e; font-size:11px;")
        self.lbl_quest_hint  = QLabel("")
        self.lbl_quest_hint.setWordWrap(True)
        self.lbl_quest_hint.setStyleSheet("color:#c9a84c; font-style:italic; font-size:11px;")
        quest_l.addWidget(self.lbl_quest_title)
        quest_l.addWidget(self.lbl_quest_obj)
        quest_l.addWidget(self.lbl_quest_hint)
        layout.addWidget(quest_frame)
        layout.addWidget(_separator())

        # ── Inventory
        layout.addWidget(_section_label("INVENTORY"))
        inv_frame = QFrame()
        inv_frame.setObjectName("card")
        inv_l = QVBoxLayout(inv_frame)
        inv_l.setContentsMargins(10, 10, 10, 10)
        inv_l.setSpacing(4)
        self.lbl_inventory = QLabel("Empty")
        self.lbl_inventory.setWordWrap(True)
        self.lbl_inventory.setStyleSheet("color:#8b949e; font-size:11px;")
        inv_l.addWidget(self.lbl_inventory)
        layout.addWidget(inv_frame)
        layout.addWidget(_separator())

        # ── Relationships
        layout.addWidget(_section_label("RELATIONSHIPS"))
        rel_frame = QFrame()
        rel_frame.setObjectName("card")
        self.rel_l = QVBoxLayout(rel_frame)
        self.rel_l.setContentsMargins(10, 10, 10, 10)
        self.rel_l.setSpacing(6)
        layout.addWidget(rel_frame)

        layout.addStretch()

    def _stat_pill(self, name: str, value: int) -> QLabel:
        lbl = QLabel(f"{name}\n{value}")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(
            "background:#21262d; border:1px solid #30363d; border-radius:6px;"
            "color:#c9d1d9; font-size:11px; padding:4px 8px;"
        )
        lbl.setFixedWidth(64)
        return lbl

    # ── Public refresh ────────────────────────────────────────────────────────

    def refresh(self, player: dict, quest: dict | None, inventory: list[dict], relationships: list[dict] = None):
        if not player:
            return

        self.lbl_player_name.setText(player.get("name", "—"))
        self.lbl_location.setText(f"📍 {player.get('current_location', '?')}")

        hp     = player.get("health",    100)
        max_hp = player.get("max_health",100)
        self.hp_bar.setMaximum(max(max_hp, 1))
        self.hp_bar.setValue(max(0, hp))
        self.lbl_hp.setText(f"{hp} / {max_hp}")

        self.lbl_str.setText(f"STR\n{player.get('strength',    10)}")
        self.lbl_int.setText(f"INT\n{player.get('intelligence',10)}")
        self.lbl_agi.setText(f"AGI\n{player.get('agility',     10)}")
        self.lbl_gold.setText(f"◈  {player.get('gold', 0)} gold")

        if quest:
            self.lbl_quest_title.setText(quest.get("title", ""))
            self.lbl_quest_obj.setText(quest.get("objective", ""))
            hints = quest.get("hints", [])
            self.lbl_quest_hint.setText(f"Hint: {hints[-1]}" if hints else "")
        else:
            self.lbl_quest_title.setText("No active quest")
            self.lbl_quest_obj.setText("")
            self.lbl_quest_hint.setText("")

        if inventory:
            lines = []
            for item in inventory:
                qty  = item.get("quantity", 1)
                name = item.get("item_name", "?")
                lines.append(f"• {name}" + (f" ×{qty}" if qty > 1 else ""))
            self.lbl_inventory.setText("\n".join(lines))
        else:
            self.lbl_inventory.setText("Empty")

        # ── Relationships update
        # Clear old items
        while self.rel_l.count():
            child = self.rel_l.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if relationships:
            for npc in relationships:
                row = QWidget()
                rl  = QHBoxLayout(row)
                rl.setContentsMargins(0, 0, 0, 0)
                
                name_lbl = QLabel(npc["name"])
                name_lbl.setStyleSheet("color:#e2e8f0; font-size:11px; font-weight:bold;")
                
                score = npc.get("relationship_score", 0)
                tier_name, color = self._get_tier_style(score)
                
                status_lbl = QLabel(f"{tier_name} ({'+' if score > 0 else ''}{score})")
                status_lbl.setStyleSheet(f"color:{color}; font-size:10px; font-weight:bold; text-transform:uppercase;")
                
                rl.addWidget(name_lbl)
                rl.addStretch()
                rl.addWidget(status_lbl)
                self.rel_l.addWidget(row)
        else:
            no_rels = QLabel("No known allies or enemies.")
            no_rels.setStyleSheet("color:#4b5563; font-style:italic; font-size:11px;")
            self.rel_l.addWidget(no_rels)

    def _get_tier_style(self, score: int) -> tuple[str, str]:
        if score <= -50: return "Nemesis",      "#dc2626"
        if score <= -20: return "Hostile",      "#ef4444"
        if score <= -5:  return "Wary",         "#facc15"
        if score <= 5:   return "Neutral",      "#94a3b8"
        if score <= 20:  return "Friendly",     "#22c55e"
        if score <= 50:  return "Ally",         "#3b82f6"
        return "Kin/Soulmate", "#a855f7"
