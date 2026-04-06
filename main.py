import sys
import os

# Allow imports from project root regardless of working directory
sys.path.insert(0, os.path.dirname(__file__))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from ui.main_window import ChronosWindow
from ui.styles import DARK_STYLESHEET


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Chronos RPG")
    app.setStyleSheet(DARK_STYLESHEET)

    window = ChronosWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
