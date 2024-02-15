import sys
from PySide6.QtWidgets import QApplication
from qt_material import apply_stylesheet
from application_window import ApplicationWindow

if __name__ == '__main__':
    """Exécuter l'application."""
    app = QApplication(sys.argv)
    ex = ApplicationWindow()

    # setup stylesheet
    apply_stylesheet(app, theme='dark_teal.xml')

    ex.show()
    sys.exit(app.exec())
