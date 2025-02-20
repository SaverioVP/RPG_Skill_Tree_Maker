import sys
from PyQt5.QtWidgets import QApplication
from main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)  # Creates the main application instance
    window = MainWindow()  # Creates an instance of the custom main window class
    window.show()  # Without this, the application would run but remain hidden.
    # Starts the PyQt event loop (exec_()).
    # The event loop keeps the GUI running and listens for user interactions (mouse clicks, key presses, etc.).
    # sys.exit(...) ensures that when the application closes, Python exits cleanly.
    sys.exit(app.exec_())
