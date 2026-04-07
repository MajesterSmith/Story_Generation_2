from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QTextBrowser, QFrame, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from db import quest_repo


class QuestTab(QWidget):
    """
    Shows a complete history of quests (Active, Completed, Failed).
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._world_id:  int | None = None
        self._player_id: int | None = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left side: Quest List
        self.list_container = QWidget()
        self.ll = QVBoxLayout(self.list_container)
        
        lbl_list = QLabel("JOURNAL ARCHIVE")
        lbl_list.setObjectName("lbl_section")
        self.ll.addWidget(lbl_list)
        
        self.quest_list = QListWidget()
        self.quest_list.itemClicked.connect(self._on_quest_selected)
        self.ll.addWidget(self.quest_list)
        
        self.splitter.addWidget(self.list_container)

        # Right side: Quest Details
        self.detail_container = QWidget()
        self.dl = QVBoxLayout(self.detail_container)
        self.dl.setContentsMargins(20, 20, 20, 20)
        
        self.lbl_title = QLabel("Select a quest to view details")
        self.lbl_title.setStyleSheet("font-size:18px; font-weight:bold; color:#c9a84c;")
        self.lbl_title.setWordWrap(True)
        self.dl.addWidget(self.lbl_title)
        
        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("font-size:11px; text-transform:uppercase; letter-spacing:1px;")
        self.dl.addWidget(self.lbl_status)
        
        self.line = QFrame()
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)
        self.dl.addWidget(self.line)

        self.txt_details = QTextBrowser()
        self.txt_details.setStyleSheet("background:transparent; border:none; font-size:14px; line-height:1.6;")
        self.dl.addWidget(self.txt_details)
        
        self.splitter.addWidget(self.detail_container)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 2)
        
        layout.addWidget(self.splitter)

    # ── Public API ────────────────────────────────────────────────────────────

    def set_player_context(self, world_id: int, player_id: int):
        self._world_id  = world_id
        self._player_id = player_id
        self.refresh()

    def refresh(self):
        if self._world_id is None or self._player_id is None:
            return
        
        # Save current selection
        current_selection = self.quest_list.currentRow()
        
        self.quest_list.clear()
        quests = quest_repo.get_all_quests(self._world_id, self._player_id)
        
        for q in quests:
            item = QListWidgetItem()
            status_icon = "⧖" if q["status"] == "ACTIVE" else "✓" if q["status"] == "COMPLETED" else "✗"
            item.setText(f"{status_icon}   {q['title']}")
            item.setData(Qt.ItemDataRole.UserRole, q)
            
            # Colour coding
            if q["status"] == "ACTIVE":
                item.setForeground(Qt.GlobalColor.white)
            elif q["status"] == "COMPLETED":
                item.setForeground(Qt.GlobalColor.gray)
            else:
                item.setForeground(Qt.GlobalColor.red)
            
            self.quest_list.addItem(item)
            
        # Restore selection
        if current_selection >= 0 and current_selection < self.quest_list.count():
            self.quest_list.setCurrentRow(current_selection)
            self._on_quest_selected(self.quest_list.item(current_selection))

    # ── Interaction ───────────────────────────────────────────────────────────

    def _on_quest_selected(self, item):
        q = item.data(Qt.ItemDataRole.UserRole)
        self.lbl_title.setText(q["title"])
        self.lbl_status.setText(f"Status: {q['status']}")
        
        # Build detailed HTML
        html = f"""
        <div style="color:#c9d1d9;">
            <p><b>Background:</b><br/>{q['description']}</p>
            <p><b>Objective:</b><br/><i>{q['objective']}</i></p>
            <hr/>
            <p style="color:#8b949e; font-size:12px;"><b>Rewards:</b> {q['reward_gold']} Gold, {', '.join(q['reward_items']) if q['reward_items'] else 'None'}</p>
        </div>
        """
        
        if q["hints"]:
            html += '<p style="color:#c9a84c;"><b>Unlocked Intelligence:</b></p><ul>'
            for hint in q["hints"]:
                html += f'<li>{hint}</li>'
            html += '</ul>'
            
        self.txt_details.setHtml(html)
