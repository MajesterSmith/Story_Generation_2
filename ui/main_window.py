from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLineEdit, QPushButton, QLabel,
    QSplitter, QFrame, QMessageBox, QSizePolicy, QTextEdit,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject, QTimer, QSettings
from PyQt6.QtGui import QFont, QKeySequence, QShortcut

from ui.narrative_panel import NarrativePanel
from ui.sidebar         import SidebarWidget
from ui.graph_tab       import GraphTab
from ui.combat_widget   import CombatWidget
from ui.trade_dialog    import TradeDialog
from ui.world_select    import WorldSelectDialog
from ui.choice_bar      import ChoiceBar
from ui.action_chips    import ActionChips
from ui.tutorial_overlay import TutorialOverlay
from ui.map_tab         import MapTab
from ui.quest_tab       import QuestTab

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
        self._pre_turn_player: dict | None = None
        self._pre_turn_inventory: dict[str, int] = {}
        self._tutorial_seen_this_session = False

        # Services
        self.client   = OllamaClient()
        self.sm       = StateManager()
        self.w_engine = WorldEngine(self.client)
        self.n_engine = NarrativeEngine(self.client, self.sm)
        self.c_engine = CombatEngine(self.client, self.sm)
        self.q_engine = QuestEngine(self.client)
        self.settings = QSettings("Chronos", "ChronosRPG")

        self._placeholder_examples = [
            "Talk to the nearest guard about rumors",
            "Inspect the area for clues",
            "Travel to a connected location",
            "Rest briefly to recover",
        ]
        self._placeholder_idx = 0
        self._placeholder_timer = QTimer(self)
        self._placeholder_timer.setInterval(4500)
        self._placeholder_timer.timeout.connect(self._rotate_input_placeholder)

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
        topbar.setStyleSheet("background:#1b2a42; border-bottom:1px solid #4f6a91;")
        tl = QHBoxLayout(topbar)
        tl.setContentsMargins(16, 0, 16, 0)
        lbl = QLabel("⧖  CHRONOS")
        lbl.setStyleSheet("color:#ffd166; font-size:15px; font-weight:bold; letter-spacing:3px;")
        self.lbl_world_name = QLabel("")
        self.lbl_world_name.setStyleSheet("color:#d6e3f7; font-size:11px;")
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

        # Area info card
        area_card = QFrame()
        area_card.setObjectName("card")
        area_card.setStyleSheet("QFrame { border-radius: 0; }")
        area_layout = QVBoxLayout(area_card)
        area_layout.setContentsMargins(12, 8, 12, 8)
        area_layout.setSpacing(4)
        self.lbl_area_location = QLabel("Location: —")
        self.lbl_area_location.setStyleSheet("font-weight:bold;")
        self.lbl_area_npcs = QLabel("NPCs around: —")
        self.lbl_area_npcs.setWordWrap(True)
        self.lbl_area_exits = QLabel("You can go to: —")
        self.lbl_area_exits.setWordWrap(True)
        area_layout.addWidget(self.lbl_area_location)
        area_layout.addWidget(self.lbl_area_npcs)
        area_layout.addWidget(self.lbl_area_exits)
        left_layout.addWidget(area_card)

        self.narrative   = NarrativePanel()
        self.combat_widget = CombatWidget()
        self.combat_widget.quick_action.connect(self._on_quick_action)
        left_layout.addWidget(self.narrative)
        left_layout.addWidget(self.combat_widget)

        self.sidebar = SidebarWidget()
        splitter.addWidget(self.sidebar)
        splitter.addWidget(left_widget)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 3)
        sl.addWidget(splitter)

        # Choice bar (scrollable)
        self.choice_bar = ChoiceBar()
        self.choice_bar.choice_selected.connect(self._on_quick_action)
        sl.addWidget(self.choice_bar)

        # Fixed quick action chips
        self.action_chips = ActionChips()
        self.action_chips.action_selected.connect(self._on_quick_action)
        sl.addWidget(self.action_chips)

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

        # ── Tab 3: World Map
        self.map_tab = MapTab()
        self.map_tab.location_selected.connect(self._on_quick_action)
        self.tabs.addTab(self.map_tab, "🗺  World Map")

        # ── Tab 4: Quest Log
        self.quest_tab = QuestTab()
        self.tabs.addTab(self.quest_tab, "📜  Quest Log")

        # ── Tab 5: Turn Summary
        summary_tab = QWidget()
        summary_layout = QVBoxLayout(summary_tab)
        summary_layout.setContentsMargins(8, 8, 8, 8)
        summary_layout.setSpacing(6)
        self.turn_summary_log = QTextEdit()
        self.turn_summary_log.setReadOnly(True)
        self.turn_summary_log.setPlaceholderText("Turn summaries will appear here as you play.")
        summary_layout.addWidget(self.turn_summary_log)
        self.tabs.addTab(summary_tab, "🧾  Turn Summary")

        # Status bar
        self.statusBar().setStyleSheet("color:#e2ecfa; font-size:10px; background:#1b2a42;")
        self.statusBar().showMessage("Welcome to Chronos.  Select or generate a world to begin.")
        self._placeholder_timer.start()

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
        self.map_tab.set_world(world_id, player["current_location"])
        self.quest_tab.set_player_context(world_id, self.player_id)
        self._update_input_examples()
        self._update_next_steps(quest_repo.get_active_quest(self.world_id, self.player_id), None)
        self._maybe_show_tutorial()
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
        self.map_tab.set_world(world_id, world.get("starting_location", ""))
        self.quest_tab.set_player_context(world_id, player_id)
        self._update_input_examples()
        self._update_next_steps(quest_repo.get_active_quest(self.world_id, self.player_id), None)
        self._maybe_show_tutorial()
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
        self._capture_pre_turn_state()
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
        self._update_turn_summary(response)
        
        # Refresh tabs
        self.quest_tab.refresh()
        player = player_repo.get_player(self.player_id)
        if player:
            self.map_tab.set_world(self.world_id, player["current_location"])

        active_q = quest_repo.get_active_quest(self.world_id, self.player_id)
        self._update_input_examples(active_q)
        self._update_next_steps(active_q, response)

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
        self._refresh_ui()

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
        known_npcs = world_repo.get_known_npcs(self.world_id)
        self.sidebar.refresh(player, quest, inventory, relationships=known_npcs)
        self._update_area_info(player, known_npcs)

    def _set_busy(self, busy: bool, msg: str = ""):
        self.action_input.setEnabled(not busy)
        self.btn_act.setEnabled(not busy)
        if msg:
            self.statusBar().showMessage(msg)

    def _capture_pre_turn_state(self):
        if self.player_id is None:
            return
        self._pre_turn_player = player_repo.get_player(self.player_id) or {}
        inventory = player_repo.get_inventory(self.player_id)
        self._pre_turn_inventory = {
            item.get("item_name", ""): int(item.get("quantity", 0))
            for item in inventory
        }

    def _update_turn_summary(self, response):
        if self.player_id is None:
            return

        lines: list[str] = []
        now_player = player_repo.get_player(self.player_id) or {}
        before = self._pre_turn_player or {}

        for key, label in (("health", "HP"), ("gold", "Gold"), ("strength", "STR"), ("intelligence", "INT"), ("agility", "AGI")):
            if key in before and key in now_player:
                delta = int(now_player[key]) - int(before[key])
                if delta != 0:
                    sign = "+" if delta > 0 else ""
                    lines.append(f"{label}: {sign}{delta}")

        inv_now = {
            item.get("item_name", ""): int(item.get("quantity", 0))
            for item in player_repo.get_inventory(self.player_id)
        }
        all_items = sorted(set(self._pre_turn_inventory) | set(inv_now))
        for item_name in all_items:
            prev_q = self._pre_turn_inventory.get(item_name, 0)
            now_q = inv_now.get(item_name, 0)
            diff = now_q - prev_q
            if diff == 0:
                continue
            sign = "+" if diff > 0 else ""
            lines.append(f"Item {item_name}: {sign}{diff}")

        for qu in response.state_update.quest_updates:
            if isinstance(qu, str):
                lines.append(f"Quest: {qu}")
            elif isinstance(qu, dict) and qu.get("status"):
                lines.append(f"Quest status: {qu.get('status')}")

        if response.state_update.relationship_changes:
            lines.append(f"Relationships changed: {len(response.state_update.relationship_changes)}")

        if not lines:
            lines = ["No major state change this turn."]
        turn_number = max(1, story_repo.get_next_turn_number(self.world_id) - 1)
        block = [f"Turn {turn_number}"] + [f"- {line}" for line in lines]
        existing = self.turn_summary_log.toPlainText().strip()
        updated = (existing + "\n\n" + "\n".join(block)).strip() if existing else "\n".join(block)
        self.turn_summary_log.setPlainText(updated)
        self.turn_summary_log.verticalScrollBar().setValue(self.turn_summary_log.verticalScrollBar().maximum())

    def _update_area_info(self, player: dict | None, known_npcs: list[dict] | None = None):
        if not player or self.world_id is None:
            self.lbl_area_location.setText("Location: —")
            self.lbl_area_npcs.setText("NPCs around: —")
            self.lbl_area_exits.setText("You can go to: —")
            return

        current_location = player.get("current_location", "Unknown")
        self.lbl_area_location.setText(f"Location: {current_location}")

        npcs_here = world_repo.get_npcs_at_location(self.world_id, current_location)
        npc_names = [n.get("name", "?") for n in npcs_here[:6]]
        self.lbl_area_npcs.setText(
            "NPCs around: " + (", ".join(npc_names) if npc_names else "No NPCs currently at this location")
        )

        exits = set()
        for conn in world_repo.get_connections(self.world_id):
            frm = conn.get("from_name", "")
            to = conn.get("to_name", "")
            if frm == current_location and to:
                exits.add(to)
            elif to == current_location and frm:
                exits.add(frm)

        if exits:
            self.lbl_area_exits.setText("You can go to: " + ", ".join(sorted(exits)))
        else:
            self.lbl_area_exits.setText("You can go to: No connected locations found")

    def _update_input_examples(self, active_quest: dict | None = None):
        examples = [
            "Talk to the nearest guard about rumors",
            "Inspect the surroundings for clues",
            "Travel to a connected location",
            "Rest briefly and recover",
        ]
        if active_quest:
            title = active_quest.get("title", "the quest")
            objective = active_quest.get("objective", "")
            examples = [
                f"Ask someone about '{title}'",
                f"Take a step toward: {objective[:42]}" + ("..." if len(objective) > 42 else ""),
                "Search the area for quest clues",
                "Talk to an NPC connected to the quest",
            ]
        self._placeholder_examples = examples
        self._placeholder_idx = 0
        self._rotate_input_placeholder(force=True)

    def _rotate_input_placeholder(self, force: bool = False):
        if not force and (self.action_input.hasFocus() or self.action_input.text().strip()):
            return
        if not self._placeholder_examples:
            self.action_input.setPlaceholderText("What do you do?  (Press Enter to act)")
            return
        example = self._placeholder_examples[self._placeholder_idx % len(self._placeholder_examples)]
        self._placeholder_idx += 1
        self.action_input.setPlaceholderText(f"Try: {example}")

    def _update_next_steps(self, active_quest: dict | None, response=None):
        objective = "No active quest. Explore and gather leads."
        lead = "Ask around or inspect your surroundings."
        moves: list[str] = [
            "Talk to a nearby NPC",
            "Explore the current location",
            "Open the world map and travel",
        ]

        if active_quest:
            objective = active_quest.get("objective") or objective
            hints = active_quest.get("hints", [])
            if hints:
                lead = hints[-1]

        if response is not None:
            if getattr(response, "important_beat", None):
                lead = response.important_beat
            if response.suggested_choices:
                moves = response.suggested_choices[:3]

        self.sidebar.update_guidance(objective, lead, moves)

    def _maybe_show_tutorial(self):
        if self._tutorial_seen_this_session:
            return
        disabled = self.settings.value("ui/tutorial_dont_show", False, type=bool)
        if disabled:
            return

        self._tutorial_seen_this_session = True
        dlg = TutorialOverlay(self)
        result = dlg.exec()
        if dlg.dont_show_again():
            self.settings.setValue("ui/tutorial_dont_show", True)
        elif result == 0:
            self.settings.setValue("ui/tutorial_dont_show", False)
