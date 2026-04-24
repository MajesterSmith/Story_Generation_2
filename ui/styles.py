DARK_STYLESHEET = """
/* ═══════════════════════════════════════════════════════
   CHRONOS — Dark Mode QSS Stylesheet
═══════════════════════════════════════════════════════ */

QWidget {
    background-color: #151d2b;
    color: #edf3ff;
    font-family: 'Segoe UI', 'Inter', sans-serif;
    font-size: 13px;
}

/* ── Main Window ────────────────────────────────────── */
QMainWindow {
    background-color: #151d2b;
}

/* ── Tab Bar ────────────────────────────────────────── */
QTabWidget::pane {
    border: 1px solid #3a4b63;
    background-color: #151d2b;
}
QTabBar::tab {
    background: #233146;
    color: #bfd0ea;
    padding: 8px 22px;
    border: 1px solid #21262d;
    border-bottom: none;
    border-radius: 4px 4px 0 0;
    font-size: 12px;
    letter-spacing: 0.5px;
}
QTabBar::tab:selected {
    background: #2f4361;
    color: #ffe08a;
    border-color: #7ca4d8;
}
QTabBar::tab:hover:!selected {
    background: #2a3a54;
    color: #eaf2ff;
}

/* ── Scroll Area ────────────────────────────────────── */
QScrollArea {
    border: none;
    background: transparent;
}
QScrollBar:vertical {
    background: #1f2b40;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #7f97b8;
    border-radius: 4px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background: #c9a84c;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal {
    background: #1f2b40;
    height: 6px;
    border-radius: 3px;
}
QScrollBar::handle:horizontal {
    background: #7f97b8;
    border-radius: 3px;
    min-width: 20px;
}
QScrollBar::handle:horizontal:hover {
    background: #c9a84c;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

/* ── Text Edit (Narrative) ──────────────────────────── */
QTextEdit#narrative_display {
    background-color: #182236;
    color: #f3f7ff;
    border: none;
    border-right: 1px solid #3a4b63;
    font-family: 'Georgia', 'Palatino Linotype', serif;
    font-size: 14px;
    line-height: 1.7;
    padding: 18px 22px;
    selection-background-color: #2d4a7a;
}

/* ── Line Edit (Input) ──────────────────────────────── */
QLineEdit#action_input {
    background-color: #24324a;
    color: #f5f9ff;
    border: 1px solid #4b6183;
    border-radius: 6px;
    padding: 10px 14px;
    font-size: 13px;
    selection-background-color: #2d4a7a;
}
QLineEdit#action_input:focus {
    border-color: #9cc2ff;
    background-color: #2a3b57;
}
QLineEdit#action_input::placeholder {
    color: #a4b7d3;
}

/* ── Buttons ────────────────────────────────────────── */
QPushButton {
    background-color: #2c3f5d;
    color: #eef4ff;
    border: 1px solid #4f6a91;
    border-radius: 6px;
    padding: 8px 18px;
    font-size: 12px;
}
QPushButton:hover {
    background-color: #395277;
    border-color: #a9c8ff;
    color: #ffffff;
}
QPushButton:pressed {
    background-color: #c9a84c;
    color: #0d0f14;
}
QPushButton#btn_act {
    background-color: #ffd166;
    color: #1b2435;
    border: none;
    font-weight: bold;
    padding: 10px 28px;
    border-radius: 6px;
    font-size: 13px;
}
QPushButton#btn_act:hover {
    background-color: #ffe08a;
}
QPushButton#btn_act:disabled {
    background-color: #5d6f8c;
    color: #d6deec;
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
    background-color: #2a3a54;
    color: #f1f6ff;
    border: 1px solid #4f6a91;
    border-radius: 14px;
    padding: 6px 16px;
    font-size: 11px;
    letter-spacing: 0.3px;
}
QPushButton#choice_btn:hover {
    border-color: #ffe08a;
    background-color: #334867;
    color: #ffffff;
}
QPushButton#choice_btn:pressed {
    background-color: #c9a84c;
    color: #0d0f14;
}

QPushButton#chip_btn {
    background-color: #2f4463;
    color: #dff0ff;
    border: 1px solid #6d92c8;
    border-radius: 12px;
    padding: 5px 12px;
    font-size: 11px;
}
QPushButton#chip_btn:hover {
    border-color: #a9ccff;
    color: #ffffff;
    background-color: #3c5680;
}
QPushButton#chip_btn:pressed {
    background-color: #60a5fa;
    color: #0b1220;
}

/* ── Labels ─────────────────────────────────────────── */
QLabel {
    color: #edf3ff;
}
QLabel#lbl_section {
    color: #ffd166;
    font-size: 10px;
    font-weight: bold;
    letter-spacing: 1.5px;
    text-transform: uppercase;
}
QLabel#lbl_world_title {
    color: #f6f9ff;
    font-size: 16px;
    font-weight: bold;
    letter-spacing: 1px;
}
QLabel#lbl_player_name {
    color: #ffd166;
    font-size: 13px;
    font-weight: bold;
}

/* ── Progress Bar (HP) ──────────────────────────────── */
QProgressBar {
    background-color: #2a3b55;
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
    background-color: #233146;
    border: 1px solid #3a4b63;
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
    background-color: #2f4361;
}

/* ── Dialog / Frame ─────────────────────────────────── */
QDialog {
    background-color: #1d2a3f;
    border: 1px solid #4f6a91;
}
QFrame#sidebar_frame {
    background-color: #182236;
    border-left: 1px solid #3a4b63;
}
QFrame#card {
    background-color: #24324a;
    border: 1px solid #3f5474;
    border-radius: 8px;
}

/* ── ComboBox ───────────────────────────────────────── */
QComboBox {
    background-color: #2c3f5d;
    color: #eef4ff;
    border: 1px solid #4f6a91;
    border-radius: 6px;
    padding: 6px 12px;
}
QComboBox:hover   { border-color: #c9a84c; }
QComboBox::drop-down { border: none; }
QComboBox QAbstractItemView {
    background-color: #233146;
    border: 1px solid #4f6a91;
    selection-background-color: #2d4a7a;
}

/* ── Separators ─────────────────────────────────────── */
QFrame[frameShape="4"], QFrame[frameShape="5"] {
    color: #3a4b63;
}

/* ── Tooltip ─────────────────────────────────────────── */
QToolTip {
    background-color: #2a3a54;
    color: #f3f7ff;
    border: 1px solid #5f7ea8;
    border-radius: 4px;
    padding: 4px 8px;
}

/* ── Choice Bar ───────────────────────────────────────── */
QScrollArea#choice_scroll_area {
    background-color: #172238;
    border-top: 1px solid #3a4b63;
    border-bottom: 1px solid #3a4b63;
}
QWidget#choice_container {
    background-color: #172238;
}

QScrollArea#chips_scroll_area {
    background-color: #1b2a42;
    border-top: 1px solid #3f5474;
    border-bottom: 1px solid #3f5474;
}
QWidget#chips_container {
    background-color: #1b2a42;
}

QFrame#turn_summary_card {
    background-color: #23344d;
    border-top: 1px solid #4f6a91;
    border-bottom: 1px solid #4f6a91;
}
QLabel#turn_summary_title {
    color: #c7e0ff;
    font-size: 10px;
    font-weight: bold;
    letter-spacing: 1px;
}
QLabel#turn_summary_body {
    color: #edf3ff;
    font-size: 11px;
}

QFrame#tutorial_card {
    background-color: #22344f;
    border: 1px solid #5f7ea8;
    border-radius: 8px;
}
QLabel#tutorial_step {
    color: #b3d4ff;
    font-size: 10px;
    font-weight: bold;
    letter-spacing: 1px;
}
QLabel#tutorial_title {
    color: #ffffff;
    font-size: 16px;
    font-weight: bold;
}
QLabel#tutorial_body {
    color: #e0ebfb;
    font-size: 12px;
}
"""

GENERATION_OVERLAY = """
QWidget#gen_overlay {
    background-color: #182236;
}
QLabel#gen_title {
    color: #ffd166;
    font-size: 22px;
    font-weight: bold;
    letter-spacing: 2px;
}
QLabel#gen_status {
    color: #d8e3f4;
    font-size: 12px;
}
"""
