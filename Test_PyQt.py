import sys
import numpy as np
import matplotlib

# Use the Qt backend explicitly
matplotlib.use("QtAgg")

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PyQt6 Test")

        # Central widget
        central = QWidget(self)
        layout = QVBoxLayout(central)

        # Matplotlib figure
        fig = Figure(figsize=(5, 4))
        canvas = FigureCanvasQTAgg(fig)
        ax = fig.add_subplot(111)

        x = np.linspace(0, 2 * np.pi, 200)
        ax.plot(x, np.sin(x))
        ax.set_title("PyQt6 + Matplotlib works")

        layout.addWidget(canvas)
        self.setCentralWidget(central)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(600, 400)
    window.show()
    sys.exit(app.exec())
