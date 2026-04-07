from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QScrollArea, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal


class ChoiceBar(QWidget):
    """
    An interactive, scrollable bar that displays suggested actions as buttons.
    Emits choice_selected(text) when a button is clicked.
    """

    choice_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(48)
        self._build_ui()
        self.hide()  # hidden by default

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Scroll Area for horizontal scrolling
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setObjectName("choice_scroll_area")

        # Container for buttons
        self.container = QWidget()
        self.container.setObjectName("choice_container")
        self.container_layout = QHBoxLayout(self.container)
        self.container_layout.setContentsMargins(12, 6, 12, 6)
        self.container_layout.setSpacing(12)
        self.container_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll)

    def set_choices(self, choices: list[str]):
        """Clear old choices and populate with new ones."""
        self.clear_choices()
        if not choices:
            self.hide()
            return

        for choice in choices:
            btn = QPushButton(choice)
            btn.setObjectName("choice_btn")
            btn.clicked.connect(lambda checked, c=choice: self.choice_selected.emit(c))
            self.container_layout.addWidget(btn)

        self.show()

    def clear_choices(self):
        """Remove all choice buttons."""
        while self.container_layout.count():
            item = self.container_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.hide()
