from PyQt6.QtWidgets import QTextEdit, QWidget, QVBoxLayout, QSizePolicy
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QTextCursor, QColor, QTextCharFormat, QFont
from config import TYPEWRITER_DELAY_MS
import re


class NarrativePanel(QWidget):
    """
    Scrolling narrative display with typewriter character-by-character effect.
    """

    typing_finished = pyqtSignal()   # emitted when typewriter buffer is empty

    # Role → colour mapping
    ROLE_COLOURS = {
        "narrator": "#e2e8f0",
        "player":   "#c9a84c",
        "system":   "#8b949e",
        "combat":   "#f87171",
        "quest":    "#4ade80", # Green for quests
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._queue:  list[tuple[str, str]] = []   # (role, text)
        self._tokens: list[str]             = []   # word/chunk buffer
        self._cur_role: str                 = "narrator"
        self._typing:   bool                = False

        self._build_ui()
        self._timer = QTimer(self)
        self._timer.setInterval(25)  # Faster "word" based pacing
        self._timer.timeout.connect(self._type_next_chunk)

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
        self._tokens = []
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
        
        # Robust Markdown to HTML conversion
        import re
        processed = text.replace("\n\n", "<br><br>")
        processed = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", processed)
        processed = re.sub(r"\*(.*?)\*", r"<i>\1</i>", processed)
        
        # Split into chunks (keeping tags together)
        # Regex to split by spaces but keep HTML tags attached to words or as separate tokens
        self._tokens = re.findall(r'<[^>]+>|[^ <]+|[ ]', processed)
        
        self._typing = True
        self._timer.start()

    def _type_next_chunk(self):
        if not self._tokens:
            self._timer.stop()
            # Add a bit of padding between turns
            self._append_html("<br>", self._cur_role)
            self._start_next()
            return
        
        chunk = self._tokens.pop(0)
        self._append_html(chunk, self._cur_role)
        
        # Scroll logic
        if "\n" in chunk or "<br>" in chunk or "." in chunk:
            self._scroll_to_bottom()

    def _append_html(self, html_chunk: str, role: str):
        cursor = self.display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        colour = self.ROLE_COLOURS.get(role, "#c9d1d9")
        # Wrap the chunk in a span with the role color
        styled_html = f'<span style="color:{colour};">{html_chunk}</span>'
        
        if role == "player":
             styled_html = f'<b>{styled_html}</b>'
             
        cursor.insertHtml(styled_html)

    def _insert_paragraph(self, text: str, role: str):
        """Used for history loading."""
        import re
        processed = text.replace("\n\n", "<br><br>")
        processed = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", processed)
        processed = re.sub(r"\*(.*?)\*", r"<i>\1</i>", processed)
        
        colour = self.ROLE_COLOURS.get(role, "#c9d1d9")
        styled_html = f'<div style="color:{colour}; margin-bottom:10px;">{processed}</div>'
        
        cursor = self.display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertHtml(styled_html)

    def _flush_buffer(self):
        if self._tokens:
            self._insert_paragraph(" ".join(self._tokens).strip(), self._cur_role)
            self._tokens = []
        self._timer.stop()
        self._typing = False

    def _scroll_to_bottom(self):
        sb = self.display.verticalScrollBar()
        sb.setValue(sb.maximum())
