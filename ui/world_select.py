from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QFrame, QWidget, QLineEdit,
    QComboBox, QFormLayout, QMessageBox, QSizePolicy, QPlainTextEdit,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class WorldSelectDialog(QDialog):
    """
    Startup world selection screen.
    Shows saved worlds and allows creation of a new world.
    Emits world_selected(world_id) or new_world_requested(name, theme, scale, player).
    """

    world_selected     = pyqtSignal(int)          # load existing world
    new_world_requested = pyqtSignal(str, str, str, str, str)  # name, theme, scale, player, prompt

    def __init__(self, worlds: list[dict], parent=None):
        super().__init__(parent)
        self.worlds = worlds
        self.setWindowTitle("Chronos — World Select")
        self.setMinimumSize(560, 400)
        self.setModal(True)
        self._build_ui()
        self._populate(worlds)

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # Title
        title = QLabel("⧖  CHRONOS")
        title.setObjectName("lbl_world_title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Choose a world or forge a new one")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color:#6b7280; font-size:11px; letter-spacing:1px;")
        layout.addWidget(subtitle)

        # World list
        self.world_list = QListWidget()
        self.world_list.setMinimumHeight(160)
        self.world_list.doubleClicked.connect(self._load_selected)
        layout.addWidget(self.world_list)

        # Buttons row
        btn_row = QHBoxLayout()
        self.btn_load = QPushButton("▶  Load World")
        self.btn_load.setObjectName("btn_act")
        self.btn_load.clicked.connect(self._load_selected)
        self.btn_delete = QPushButton("Delete")
        self.btn_delete.setObjectName("btn_danger")
        self.btn_delete.clicked.connect(self._delete_world)
        btn_row.addWidget(self.btn_load)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_delete)
        layout.addLayout(btn_row)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(sep)

        # ── New World form
        form_lbl = QLabel("Create New World")
        form_lbl.setObjectName("lbl_section")
        layout.addWidget(form_lbl)

        form = QFormLayout()
        form.setSpacing(10)

        self.inp_world_name  = QLineEdit()
        self.inp_world_name.setPlaceholderText("e.g. Aethoria")
        self.inp_world_name.setObjectName("action_input")

        self.inp_theme = QLineEdit()
        self.inp_theme.setPlaceholderText("e.g. Dark Fantasy, Steampunk, Post-Apocalyptic")
        self.inp_theme.setObjectName("action_input")

        self.cmb_scale = QComboBox()
        self.cmb_scale.addItems(["Small", "Medium", "Large"])
        self.cmb_scale.setCurrentIndex(1)

        self.inp_player = QLineEdit()
        self.inp_player.setPlaceholderText("Your character's name")
        self.inp_player.setObjectName("action_input")

        self.inp_details = QPlainTextEdit()
        self.inp_details.setPlaceholderText("Anything else? (e.g. \"The world is built on a giant turtle\", \"Low magic\")")
        self.inp_details.setMaximumHeight(80)
        self.inp_details.setObjectName("action_input")

        form.addRow("World Name:",   self.inp_world_name)
        form.addRow("Theme:",        self.inp_theme)
        form.addRow("Scale:",        self.cmb_scale)
        form.addRow("Player Name:",  self.inp_player)
        form.addRow("World Details:", self.inp_details)
        layout.addLayout(form)

        btn_create = QPushButton("✦  Generate New World")
        btn_create.setObjectName("btn_act")
        btn_create.clicked.connect(self._create_world)
        layout.addWidget(btn_create)

    def _populate(self, worlds: list[dict]):
        self.world_list.clear()
        if not worlds:
            placeholder = QListWidgetItem("No saved worlds — create one below")
            placeholder.setFlags(Qt.ItemFlag.NoItemFlags)
            placeholder.setForeground(Qt.GlobalColor.gray)
            self.world_list.addItem(placeholder)
            return
        for w in worlds:
            text = f"{w['name']}   [{w['theme']} · {w['scale']}]   {w['created_at'][:10]}"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, w["id"])
            self.world_list.addItem(item)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _load_selected(self):
        item = self.world_list.currentItem()
        if not item:
            return
        wid = item.data(Qt.ItemDataRole.UserRole)
        if wid:
            self.world_selected.emit(wid)
            self.accept()

    def _delete_world(self):
        item = self.world_list.currentItem()
        if not item:
            return
        wid = item.data(Qt.ItemDataRole.UserRole)
        if not wid:
            return
        reply = QMessageBox.question(
            self, "Delete World",
            "Permanently delete this world and all its data?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            from db import world_repo
            world_repo.delete_world(wid)
            self.worlds = [w for w in self.worlds if w["id"] != wid]
            self._populate(self.worlds)

    def _create_world(self):
        name   = self.inp_world_name.text().strip()
        theme  = self.inp_theme.text().strip()
        scale  = self.cmb_scale.currentText()
        player = self.inp_player.text().strip()
        prompt = self.inp_details.toPlainText().strip()

        if not name:
            QMessageBox.warning(self, "Required", "Please enter a world name.")
            return
        if not theme:
            QMessageBox.warning(self, "Required", "Please enter a theme.")
            return
        if not player:
            QMessageBox.warning(self, "Required", "Please enter your character's name.")
            return

        self.new_world_requested.emit(name, theme, scale, player, prompt)
        self.accept()
