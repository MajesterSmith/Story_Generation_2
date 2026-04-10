from PyQt6.QtWidgets import QTextEdit, QWidget, QVBoxLayout, QSizePolicy
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QTextCursor, QColor, QTextCharFormat, QFont
from config import TYPEWRITER_DELAY_MS


class NarrativePanel(QWidget):
    """
    Scrolling narrative display with typewriter character-by-character effect.
    """

    typing_finished = pyqtSignal()   # emitted when typewriter buffer is empty

    # Role → colour mapping
    ROLE_COLOURS = {
        "narrator": "#e2e8f0",
        "player":   "#c9a84c",
        "system":   "#6e7681",
        "combat":   "#f87171",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._queue:  list[tuple[str, str]] = []   # (role, text)
        self._buffer: str                   = ""
        self._cur_role: str                 = "narrator"
        self._typing:   bool                = False

        self._build_ui()
        self._timer = QTimer(self)
        self._timer.setInterval(TYPEWRITER_DELAY_MS)
        self._timer.timeout.connect(self._type_next_char)

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.display = QTextEdit()
        self.display.setObjectName("narrative_display")
        self.display.setReadOnly(True)
        self.display.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.display)

    # ── Public API ────────────────────────────────────────────────────────────

    def append_text(self, text: str, role: str = "narrator"):
        """Queue text for typewriter display."""
        self._queue.append((role, text))
        if not self._typing:
            self._start_next()

    def append_instant(self, text: str, role: str = "system"):
        """Add text immediately (no typewriter) — used for boot logs."""
        self._flush_buffer()
        self._insert_paragraph(text, role)
        self._scroll_to_bottom()

    def clear_display(self):
        self._queue.clear()
        self._buffer = ""
        self._typing = False
        self._timer.stop()
        self.display.clear()

    def load_history(self, logs: list[dict]):
        """Populate the display from saved story_logs on world load."""
        self.clear_display()
        for log in logs:
            self._insert_paragraph(log["content"], log["role"])
        self._scroll_to_bottom()

    # ── Internal ──────────────────────────────────────────────────────────────

    def _start_next(self):
        if not self._queue:
            self._typing = False
            self.typing_finished.emit()
            return
        role, text = self._queue.pop(0)
        self._cur_role = role
        self._buffer   = "\n" + text + "\n"
        self._typing   = True
        self._timer.start()

    def _type_next_char(self):
        if not self._buffer:
            self._timer.stop()
            self._start_next()
            return
        char = self._buffer[0]
        self._buffer = self._buffer[1:]
        self._append_char(char, self._cur_role)
        if char in (".", "!", "?", "\n"):
            self._scroll_to_bottom()

    def _append_char(self, char: str, role: str):
        cursor = self.display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        fmt = QTextCharFormat()
        colour = self.ROLE_COLOURS.get(role, "#c9d1d9")
        fmt.setForeground(QColor(colour))
        if role == "player":
            fmt.setFontWeight(QFont.Weight.Bold)
        cursor.insertText(char, fmt)

    def _insert_paragraph(self, text: str, role: str):
        cursor = self.display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        fmt = QTextCharFormat()
        colour = self.ROLE_COLOURS.get(role, "#c9d1d9")
        fmt.setForeground(QColor(colour))
        if role == "player":
            fmt.setFontWeight(QFont.Weight.Bold)
        cursor.insertText("\n" + text + "\n", fmt)

    def _flush_buffer(self):
        if self._buffer:
            self._insert_paragraph(self._buffer.strip(), self._cur_role)
            self._buffer = ""
        self._timer.stop()
        self._typing = False

    def _scroll_to_bottom(self):
        sb = self.display.verticalScrollBar()
        sb.setValue(sb.maximum())
