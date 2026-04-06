from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QFrame, QWidget, QProgressBar,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor


class CombatWidget(QWidget):
    """
    Compact combat overlay shown at the bottom of the story tab during combat.
    Displays enemy health bar and 3 quick-action buttons.
    """

    quick_action = pyqtSignal(str)    # emitted when a quick-action button is clicked

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setMaximumHeight(130)
        self._build_ui()
        self.hide()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        # Enemy header
        header = QHBoxLayout()
        self.lbl_enemy = QLabel("⚔  Enemy")
        self.lbl_enemy.setStyleSheet("color:#ef4444; font-weight:bold; font-size:13px;")
        header.addWidget(self.lbl_enemy)
        header.addStretch()
        self.lbl_enemy_hp = QLabel("50 / 50")
        self.lbl_enemy_hp.setStyleSheet("color:#f87171; font-size:11px;")
        header.addWidget(self.lbl_enemy_hp)
        layout.addLayout(header)

        # Enemy HP bar
        self.enemy_hp_bar = QProgressBar()
        self.enemy_hp_bar.setRange(0, 100)
        self.enemy_hp_bar.setValue(100)
        self.enemy_hp_bar.setFixedHeight(8)
        self.enemy_hp_bar.setTextVisible(False)
        self.enemy_hp_bar.setStyleSheet(
            "QProgressBar { background:#21262d; border:none; border-radius:4px; }"
            "QProgressBar::chunk { background:#ef4444; border-radius:4px; }"
        )
        layout.addWidget(self.enemy_hp_bar)

        # Quick-action buttons
        btns = QHBoxLayout()
        for label in ("⚔ Attack", "🛡 Defend", "🏃 Flee"):
            btn = QPushButton(label)
            btn.setFixedHeight(32)
            btn.clicked.connect(lambda _, l=label: self.quick_action.emit(l.split(" ", 1)[1]))
            btns.addWidget(btn)
        layout.addLayout(btns)

    # ── Public ────────────────────────────────────────────────────────────────

    def start_combat(self, npc_name: str, npc_hp: int, npc_max_hp: int):
        self.lbl_enemy.setText(f"⚔  {npc_name}")
        self._update_hp(npc_hp, npc_max_hp)
        self.show()

    def update_enemy_hp(self, hp: int, max_hp: int):
        self._update_hp(hp, max_hp)

    def end_combat(self):
        self.hide()

    def _update_hp(self, hp: int, max_hp: int):
        self.enemy_hp_bar.setMaximum(max(max_hp, 1))
        self.enemy_hp_bar.setValue(max(0, hp))
        self.lbl_enemy_hp.setText(f"{hp} / {max_hp}")
