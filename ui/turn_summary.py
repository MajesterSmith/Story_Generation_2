from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame


class TurnSummaryWidget(QWidget):
    """Compact summary of what changed this turn."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self.hide()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        card = QFrame()
        card.setObjectName("turn_summary_card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        self.lbl_title = QLabel("TURN SUMMARY")
        self.lbl_title.setObjectName("turn_summary_title")
        self.lbl_body = QLabel("")
        self.lbl_body.setWordWrap(True)
        self.lbl_body.setObjectName("turn_summary_body")

        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_body)
        root.addWidget(card)

    def set_lines(self, lines: list[str]):
        text = "\n".join(lines[:6]) if lines else "No major state change this turn."
        self.lbl_body.setText(text)
        self.show()
