from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLineEdit, QPushButton, QLabel,
    QSplitter, QFrame, QMessageBox, QSizePolicy,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QKeySequence, QShortcut

from ui.narrative_panel import NarrativePanel
from ui.sidebar         import SidebarWidget
from ui.graph_tab       import GraphTab
from ui.combat_widget   import CombatWidget
from ui.trade_dialog    import TradeDialog
from ui.world_select    import WorldSelectDialog
from ui.choice_bar      import ChoiceBar

from engine.world_engine    import WorldEngine
from engine.narrative_engine import NarrativeEngine
from engine.combat_engine   import CombatEngine
from engine.quest_engine    import QuestEngine
from engine.state_manager   import StateManager

from llm.ollama_client import OllamaClient

from db import world_repo, player_repo, quest_repo, story_repo
from db.database import init_db


# ── Background worker threads ─────────────────────────────────────────────────

class GenerationWorker(QObject):
    finished = pyqtSignal(int, int)     # world_id, player_id
    error    = pyqtSignal(str)

    def __init__(self, engine: WorldEngine, name, theme, scale, player, prompt):
        super().__init__()
        self.engine = engine
        self.args   = (name, theme, scale, player, prompt)

    def run(self):
        try:
            wid, pid = self.engine.generate_world(*self.args)
            self.finished.emit(wid, pid)
        except Exception as e:
            self.error.emit(str(e))


class TurnWorker(QObject):
    finished = pyqtSignal(object)   # LLMResponse
    error    = pyqtSignal(str)

    def __init__(self, engine, world_id, player_id, action, combat_engine=None):
        super().__init__()
        self.engine        = engine
        self.world_id      = world_id
        self.player_id     = player_id
        self.action        = action
        self.combat_engine = combat_engine

    def run(self):
        try:
            if self.combat_engine and self.combat_engine.in_combat:
                response, ended = self.combat_engine.process_combat_turn(
                    self.world_id, self.player_id, self.action
                )
                response._combat_ended = ended
            else:
                response = self.engine.process_turn(
                    self.world_id, self.player_id, self.action
                )
                response._combat_ended = False
            self.finished.emit(response)
        except Exception as e:
            self.error.emit(str(e))


# ── Main Window ───────────────────────────────────────────────────────────────

class ChronosWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("⧖ Chronos — Symbolic RPG Engine")
        self.resize(1200, 780)

        # State
        self.world_id:  int | None = None
        self.player_id: int | None = None
        self._thread:   QThread | None = None

        # Services
        self.client   = OllamaClient()
        self.sm       = StateManager()
        self.w_engine = WorldEngine(self.client)
        self.n_engine = NarrativeEngine(self.client, self.sm)
        self.c_engine = CombatEngine(self.client, self.sm)
        self.q_engine = QuestEngine(self.client)

        init_db()
        self._build_ui()
        self._show_world_select()

    # ── UI Build ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Top bar
        topbar = QWidget()
        topbar.setFixedHeight(42)
        topbar.setStyleSheet("background:#0d0f14; border-bottom:1px solid #21262d;")
        tl = QHBoxLayout(topbar)
        tl.setContentsMargins(16, 0, 16, 0)
        lbl = QLabel("⧖  CHRONOS")
        lbl.setStyleSheet("color:#c9a84c; font-size:15px; font-weight:bold; letter-spacing:3px;")
        self.lbl_world_name = QLabel("")
        self.lbl_world_name.setStyleSheet("color:#6b7280; font-size:11px;")
        self.btn_menu = QPushButton("≡ Menu")
        self.btn_menu.setFixedWidth(80)
        self.btn_menu.clicked.connect(self._show_world_select)
        tl.addWidget(lbl)
        tl.addWidget(self.lbl_world_name)
        tl.addStretch()
        tl.addWidget(self.btn_menu)
        root.addWidget(topbar)

        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        root.addWidget(self.tabs)

        # ── Tab 1: Story
        story_tab = QWidget()
        sl = QVBoxLayout(story_tab)
        sl.setContentsMargins(0, 0, 0, 0)
        sl.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Narrative + combat stack
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        self.narrative   = NarrativePanel()
        self.combat_widget = CombatWidget()
        self.combat_widget.quick_action.connect(self._on_quick_action)
        left_layout.addWidget(self.narrative)
        left_layout.addWidget(self.combat_widget)

        splitter.addWidget(left_widget)
        self.sidebar = SidebarWidget()
        splitter.addWidget(self.sidebar)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 0)
        sl.addWidget(splitter)

        # Choice bar (scrollable)
        self.choice_bar = ChoiceBar()
        self.choice_bar.choice_selected.connect(self._on_quick_action)
        sl.addWidget(self.choice_bar)

        # Input bar
        input_bar = QWidget()
        input_bar.setFixedHeight(56)
        input_bar.setStyleSheet("background:#0f1319; border-top:1px solid #21262d;")
        il = QHBoxLayout(input_bar)
        il.setContentsMargins(12, 8, 12, 8)
        il.setSpacing(10)
        self.action_input = QLineEdit()
        self.action_input.setObjectName("action_input")
        self.action_input.setPlaceholderText("What do you do?  (Press Enter to act)")
        self.action_input.returnPressed.connect(self._submit_action)
        self.action_input.setEnabled(False)
        self.btn_act = QPushButton("Act")
        self.btn_act.setObjectName("btn_act")
        self.btn_act.setFixedWidth(76)
        self.btn_act.clicked.connect(self._submit_action)
        self.btn_act.setEnabled(False)
        il.addWidget(self.action_input)
        il.addWidget(self.btn_act)
        sl.addWidget(input_bar)

        self.tabs.addTab(story_tab, "📖  Story")

        # ── Tab 2: Relationships
        self.graph_tab = GraphTab()
        self.tabs.addTab(self.graph_tab, "🕸  Relationships")

        # Status bar
        self.statusBar().setStyleSheet("color:#6b7280; font-size:10px; background:#0d0f14;")
        self.statusBar().showMessage("Welcome to Chronos.  Select or generate a world to begin.")

    # ── World Select / Load ───────────────────────────────────────────────────

    def _show_world_select(self):
        worlds = world_repo.get_all_worlds()
        dlg    = WorldSelectDialog(worlds, self)
        dlg.world_selected.connect(self._load_world)
        dlg.new_world_requested.connect(self._generate_world)
        dlg.exec()

    def _load_world(self, world_id: int):
        world, player = self.w_engine.load_world(world_id)
        if not world or not player:
            QMessageBox.critical(self, "Error", "Failed to load world data.")
            return
        self.world_id  = world_id
        self.player_id = player["id"]
        self.lbl_world_name.setText(f"·  {world['name']}  [{world['scale']}]")
        # Load history
        logs = story_repo.get_all_display_logs(world_id)
        self.narrative.load_history(logs)
        self._refresh_ui()
        self.action_input.setEnabled(True)
        self.btn_act.setEnabled(True)
        self.graph_tab.set_world(world_id)
        self.statusBar().showMessage(f"World '{world['name']}' loaded.  Begin your adventure.")

    # ── Generation ────────────────────────────────────────────────────────────

    def _generate_world(self, name: str, theme: str, scale: str, player: str, prompt: str):
        self._set_busy(True, f"Generating world '{name}'…  This may take 30–60s.")
        self.narrative.clear_display()
        self.narrative.append_instant(
            f"⧖  Forging world '{name}' ({scale} · {theme})…\n"
            f"The LLM is building lore, factions, NPCs, and quests.\n"
            f"Please wait…",
            role="system",
        )

        worker = GenerationWorker(self.w_engine, name, theme, scale, player, prompt)
        self._thread = QThread()
        worker.moveToThread(self._thread)
        self._thread.started.connect(worker.run)
        worker.finished.connect(self._on_world_generated)
        worker.error.connect(self._on_generation_error)
        worker.finished.connect(self._thread.quit)
        worker.error.connect(self._thread.quit)
        
        # Store references to prevent garbage collection
        self._current_worker = worker
        self._current_thread = self._thread
        
        self._thread.start()

    def _on_world_generated(self, world_id: int, player_id: int):
        self._set_busy(False)
        self.world_id  = world_id
        self.player_id = player_id

        world  = world_repo.get_world(world_id)
        self.lbl_world_name.setText(f"·  {world['name']}  [{world['scale']}]")

        logs = story_repo.get_all_display_logs(world_id)
        self.narrative.clear_display()
        self.narrative.load_history(logs)
        self._refresh_ui()

        self.action_input.setEnabled(True)
        self.btn_act.setEnabled(True)
        self.graph_tab.set_world(world_id)
        self.statusBar().showMessage(
            f"✓ World '{world['name']}' generated.  Your adventure begins…"
        )

    def _on_generation_error(self, error: str):
        self._set_busy(False)
        QMessageBox.critical(self, "Generation Error",
                             f"World generation failed:\n{error}")
        self.statusBar().showMessage("Generation failed — check Ollama is running.")

    # ── Turn Loop ─────────────────────────────────────────────────────────────

    def _submit_action(self):
        text = self.action_input.text().strip()
        if not text or self.world_id is None:
            return
        self.action_input.clear()
        self.choice_bar.clear_choices()

        # Detect trade intent
        if self._detect_trade(text):
            return

        # Show player action in narrative
        self.narrative.append_text(f"» {text}", role="player")
        self._set_busy(True, "Narrating…")

        worker = TurnWorker(self.n_engine, self.world_id, self.player_id, text,
                            self.c_engine if self.c_engine.in_combat else None)
        self._thread = QThread()
        worker.moveToThread(self._thread)
        self._thread.started.connect(worker.run)
        worker.finished.connect(self._on_turn_complete)
        worker.error.connect(self._on_turn_error)
        worker.finished.connect(self._thread.quit)
        worker.error.connect(self._thread.quit)
        
        # Store references to prevent garbage collection
        self._current_worker = worker
        self._current_thread = self._thread
        
        self._thread.start()

    def _on_turn_complete(self, response):
        self._set_busy(False)
        self.narrative.append_text(response.narrative, role="narrator")

        if response.suggested_choices:
            self.choice_bar.set_choices(response.suggested_choices)

        # NPC dialogue
        if response.npc_dialogue:
            self.narrative.append_text(f"💬 {response.npc_dialogue}", role="system")

        # Combat start detection
        if response.combat_outcome and not self.c_engine.in_combat:
            self._try_start_combat(response)

        # Combat ended
        if getattr(response, "_combat_ended", False):
            self.combat_widget.end_combat()

        # Update combat HP if in combat
        if self.c_engine.in_combat and self.c_engine.combat_state:
            cs = self.c_engine.combat_state
            self.combat_widget.update_enemy_hp(cs.npc_health, cs.npc_max_hp)

        self._refresh_ui()
        # Refresh graph only if relationships changed
        if response.state_update.relationship_changes:
            self.graph_tab.refresh()

    def _on_turn_error(self, error: str):
        self._set_busy(False)
        self.narrative.append_instant(f"[Error: {error}]", role="system")
        self.statusBar().showMessage(f"Error: {error}")

    def _on_quick_action(self, action: str):
        self.action_input.setText(action)
        self._submit_action()

    # ── Trade Detection ───────────────────────────────────────────────────────

    def _detect_trade(self, text: str) -> bool:
        trade_kws = ("trade", "buy", "sell", "shop")
        if not any(kw in text.lower() for kw in trade_kws):
            return False
        # Try to find NPC by name in text
        npcs = world_repo.get_all_npcs(self.world_id)
        for npc in npcs:
            if npc["name"].lower() in text.lower():
                self._open_trade(npc)
                return True
        # Open with first NPC that has shop items
        for npc in npcs:
            if npc.get("shop_items"):
                self._open_trade(npc)
                return True
        return False

    def _open_trade(self, npc: dict):
        dlg = TradeDialog(npc, self.player_id, self)
        dlg.trade_complete.connect(self._refresh_ui)
        dlg.exec()

    # ── Combat ────────────────────────────────────────────────────────────────

    def _try_start_combat(self, response):
        npcs = world_repo.get_all_npcs(self.world_id)
        for npc in npcs:
            if npc["name"].lower() in response.narrative.lower():
                msg = self.c_engine.start_combat(npc)
                self.combat_widget.start_combat(
                    npc["name"], npc["health"], npc.get("max_health", npc["health"])
                )
                self.narrative.append_instant(msg, role="combat")
                return

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _refresh_ui(self):
        if self.world_id is None or self.player_id is None:
            return
        player    = player_repo.get_player(self.player_id)
        quest     = quest_repo.get_active_quest(self.world_id, self.player_id)
        inventory = player_repo.get_inventory(self.player_id)
        self.sidebar.refresh(player, quest, inventory)

    def _set_busy(self, busy: bool, msg: str = ""):
        self.action_input.setEnabled(not busy)
        self.btn_act.setEnabled(not busy)
        if msg:
            self.statusBar().showMessage(msg)
