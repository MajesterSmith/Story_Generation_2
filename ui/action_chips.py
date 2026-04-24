from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal


class ActionChips(QWidget):
    """Fixed quick-intent chips to reduce typing friction."""

    action_selected = pyqtSignal(str)

    DEFAULT_ACTIONS = [
        "Talk to nearby NPC",
        "Explore nearby area",
        "Travel to a connected location",
        "Check inventory",
        "Rest for a while",
        "Ask around for clues",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(46)
        self._build_ui()
        self.set_actions(self.DEFAULT_ACTIONS)

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setObjectName("chips_scroll_area")

        self.container = QWidget()
        self.container.setObjectName("chips_container")
        self.container_layout = QHBoxLayout(self.container)
        self.container_layout.setContentsMargins(12, 6, 12, 6)
        self.container_layout.setSpacing(8)
        self.container_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll)

    def set_actions(self, actions: list[str]):
        while self.container_layout.count():
            item = self.container_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        for action in actions:
            btn = QPushButton(action)
            btn.setObjectName("chip_btn")
            btn.clicked.connect(lambda checked, a=action: self.action_selected.emit(a))
            self.container_layout.addWidget(btn)
