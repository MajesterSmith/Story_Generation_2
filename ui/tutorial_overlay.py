from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QHBoxLayout,
    QPushButton, QCheckBox, QFrame
)
from PyQt6.QtCore import Qt


class TutorialOverlay(QDialog):
    """Simple first-run walkthrough with 4 short steps."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Quick Start")
        self.setModal(True)
        self.setMinimumWidth(520)
        self._step_idx = 0
        self._steps = [
            ("Act with confidence", "Use the input box at the bottom to type your action. Press Enter or click Act."),
            ("Use quick command chips", "Tap chips for common intents like Talk, Explore, Travel, and Rest."),
            ("Follow the main thread", "Watch the What To Do Next panel for objective, lead, and suggested next moves."),
            ("Check consequences", "After each action, Turn Summary shows what changed in stats, quest progress, or relationships."),
        ]
        self._build_ui()
        self._render_step()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        card = QFrame()
        card.setObjectName("tutorial_card")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(14, 14, 14, 14)
        cl.setSpacing(8)

        self.lbl_step = QLabel("")
        self.lbl_step.setObjectName("tutorial_step")
        self.lbl_title = QLabel("")
        self.lbl_title.setObjectName("tutorial_title")
        self.lbl_body = QLabel("")
        self.lbl_body.setWordWrap(True)
        self.lbl_body.setObjectName("tutorial_body")

        cl.addWidget(self.lbl_step)
        cl.addWidget(self.lbl_title)
        cl.addWidget(self.lbl_body)
        root.addWidget(card)

        self.chk_dont_show = QCheckBox("Do not show again")
        root.addWidget(self.chk_dont_show)

        actions = QHBoxLayout()
        actions.addStretch()
        self.btn_back = QPushButton("Back")
        self.btn_skip = QPushButton("Skip")
        self.btn_next = QPushButton("Next")
        self.btn_back.clicked.connect(self._back)
        self.btn_skip.clicked.connect(self.reject)
        self.btn_next.clicked.connect(self._next)
        actions.addWidget(self.btn_back)
        actions.addWidget(self.btn_skip)
        actions.addWidget(self.btn_next)
        root.addLayout(actions)

    def _render_step(self):
        title, body = self._steps[self._step_idx]
        self.lbl_step.setText(f"Step {self._step_idx + 1} of {len(self._steps)}")
        self.lbl_title.setText(title)
        self.lbl_body.setText(body)
        self.btn_back.setEnabled(self._step_idx > 0)
        self.btn_next.setText("Finish" if self._step_idx == len(self._steps) - 1 else "Next")

    def _next(self):
        if self._step_idx >= len(self._steps) - 1:
            self.accept()
            return
        self._step_idx += 1
        self._render_step()

    def _back(self):
        if self._step_idx <= 0:
            return
        self._step_idx -= 1
        self._render_step()

    def dont_show_again(self) -> bool:
        return self.chk_dont_show.isChecked()
