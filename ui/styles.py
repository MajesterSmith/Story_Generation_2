DARK_STYLESHEET = """
/* ═══════════════════════════════════════════════════════
   CHRONOS — Dark Mode QSS Stylesheet
═══════════════════════════════════════════════════════ */

QWidget {
    background-color: #0d0f14;
    color: #c9d1d9;
    font-family: 'Segoe UI', 'Inter', sans-serif;
    font-size: 13px;
}

/* ── Main Window ────────────────────────────────────── */
QMainWindow {
    background-color: #0d0f14;
}

/* ── Tab Bar ────────────────────────────────────────── */
QTabWidget::pane {
    border: 1px solid #21262d;
    background-color: #0d0f14;
}
QTabBar::tab {
    background: #161b22;
    color: #8b949e;
    padding: 8px 22px;
    border: 1px solid #21262d;
    border-bottom: none;
    border-radius: 4px 4px 0 0;
    font-size: 12px;
    letter-spacing: 0.5px;
}
QTabBar::tab:selected {
    background: #1f2937;
    color: #c9a84c;
    border-color: #3d4451;
}
QTabBar::tab:hover:!selected {
    background: #1c2333;
    color: #c9d1d9;
}

/* ── Scroll Area ────────────────────────────────────── */
QScrollArea {
    border: none;
    background: transparent;
}
QScrollBar:vertical {
    background: #161b22;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #3d4451;
    border-radius: 4px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background: #c9a84c;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal {
    background: #161b22;
    height: 6px;
    border-radius: 3px;
}
QScrollBar::handle:horizontal {
    background: #3d4451;
    border-radius: 3px;
    min-width: 20px;
}
QScrollBar::handle:horizontal:hover {
    background: #c9a84c;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

/* ── Text Edit (Narrative) ──────────────────────────── */
QTextEdit#narrative_display {
    background-color: #0d0f14;
    color: #e2e8f0;
    border: none;
    border-right: 1px solid #21262d;
    font-family: 'Georgia', 'Palatino Linotype', 'Times New Roman', serif;
    font-size: 15px;
    line-height: 1.8;
    padding: 24px 28px;
    selection-background-color: #2d4a7a;
}

/* ── Line Edit (Input) ──────────────────────────────── */
QLineEdit#action_input {
    background-color: #161b22;
    color: #e2e8f0;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 10px 14px;
    font-size: 13px;
    selection-background-color: #2d4a7a;
}
QLineEdit#action_input:focus {
    border-color: #c9a84c;
    background-color: #1c2333;
}
QLineEdit#action_input::placeholder {
    color: #484f58;
}

/* ── Buttons ────────────────────────────────────────── */
QPushButton {
    background-color: #21262d;
    color: #c9d1d9;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 8px 18px;
    font-size: 12px;
}
QPushButton:hover {
    background-color: #2d3748;
    border-color: #c9a84c;
    color: #f0d080;
}
QPushButton:pressed {
    background-color: #c9a84c;
    color: #0d0f14;
}
QPushButton#btn_act {
    background-color: #c9a84c;
    color: #0d0f14;
    border: none;
    font-weight: bold;
    padding: 10px 28px;
    border-radius: 6px;
    font-size: 13px;
}
QPushButton#btn_act:hover {
    background-color: #e0bf5e;
}
QPushButton#btn_act:disabled {
    background-color: #3d4451;
    color: #6e7681;
}
QPushButton#btn_danger {
    background-color: #6e1a1a;
    color: #fca5a5;
    border: 1px solid #7f1d1d;
}
QPushButton#btn_danger:hover {
    background-color: #991b1b;
}

QPushButton#choice_btn {
    background-color: #1a1d23;
    color: #e2e8f0;
    border: 1px solid #30363d;
    border-radius: 14px;
    padding: 6px 16px;
    font-size: 11px;
    letter-spacing: 0.3px;
}
QPushButton#choice_btn:hover {
    border-color: #c9a84c;
    background-color: #21262d;
    color: #f0d080;
}
QPushButton#choice_btn:pressed {
    background-color: #c9a84c;
    color: #0d0f14;
}

/* ── Labels ─────────────────────────────────────────── */
QLabel {
    color: #c9d1d9;
}
QLabel#lbl_section {
    color: #c9a84c;
    font-size: 10px;
    font-weight: bold;
    letter-spacing: 1.5px;
    text-transform: uppercase;
}
QLabel#lbl_world_title {
    color: #e2e8f0;
    font-size: 16px;
    font-weight: bold;
    letter-spacing: 1px;
}
QLabel#lbl_player_name {
    color: #c9a84c;
    font-size: 13px;
    font-weight: bold;
}

/* ── Progress Bar (HP) ──────────────────────────────── */
QProgressBar {
    background-color: #21262d;
    border: none;
    border-radius: 4px;
    height: 8px;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #dc2626, stop:0.5 #ea580c, stop:1 #16a34a);
    border-radius: 4px;
}
QProgressBar#hp_bar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #16a34a, stop:0.7 #22c55e, stop:1 #4ade80);
}

/* ── List Widget ────────────────────────────────────── */
QListWidget {
    background-color: #161b22;
    border: 1px solid #21262d;
    border-radius: 6px;
    padding: 4px;
    alternate-background-color: #1c2333;
}
QListWidget::item {
    padding: 5px 8px;
    border-radius: 4px;
}
QListWidget::item:selected {
    background-color: #2d4a7a;
    color: #e2e8f0;
}
QListWidget::item:hover {
    background-color: #21262d;
}

/* ── Dialog / Frame ─────────────────────────────────── */
QDialog {
    background-color: #161b22;
    border: 1px solid #30363d;
}
QFrame#sidebar_frame {
    background-color: #0f1319;
    border-left: 1px solid #21262d;
}
QFrame#card {
    background-color: #161b22;
    border: 1px solid #21262d;
    border-radius: 8px;
}

/* ── ComboBox ───────────────────────────────────────── */
QComboBox {
    background-color: #21262d;
    color: #c9d1d9;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 6px 12px;
}
QComboBox:hover   { border-color: #c9a84c; }
QComboBox::drop-down { border: none; }
QComboBox QAbstractItemView {
    background-color: #161b22;
    border: 1px solid #30363d;
    selection-background-color: #2d4a7a;
}

/* ── Separators ─────────────────────────────────────── */
QFrame[frameShape="4"], QFrame[frameShape="5"] {
    color: #21262d;
}

/* ── Tooltip ─────────────────────────────────────────── */
QToolTip {
    background-color: #1c2333;
    color: #c9d1d9;
    border: 1px solid #30363d;
    border-radius: 4px;
    padding: 4px 8px;
}

/* ── Choice Bar ───────────────────────────────────────── */
QScrollArea#choice_scroll_area {
    background-color: #0d0f14;
    border-top: 1px solid #21262d;
    border-bottom: 1px solid #21262d;
}
QWidget#choice_container {
    background-color: #0d0f14;
}
"""

GENERATION_OVERLAY = """
QWidget#gen_overlay {
    background-color: #0d0f14;
}
QLabel#gen_title {
    color: #c9a84c;
    font-size: 22px;
    font-weight: bold;
    letter-spacing: 2px;
}
QLabel#gen_status {
    color: #8b949e;
    font-size: 12px;
}
"""
