"""
Building Electrical Estimator
Entry point - launches the PyQt6 application.
"""

import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Building Electrical Estimator")
    app.setStyle("Fusion")  # Consistent cross-platform look

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
