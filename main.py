import sys
from PySide6.QtWidgets import QApplication

from application_window import ApplicationWindow

if __name__ == '__main__':
    """Exécuter l'application."""
    app = QApplication(sys.argv)
    ex = ApplicationWindow()
    ex.show()
    sys.exit(app.exec())
