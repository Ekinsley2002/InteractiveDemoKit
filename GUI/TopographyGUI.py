import os
import numpy as np
import pyqtgraph as pg
import matplotlib.cm as cm
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import pyqtSignal, Qt

TRIAL_FILE = "trials.txt"
MAX_VALUES_PER_TRIAL = 100
MAX_TRIALS = 4


class TopographyPageWidget(QWidget):
    back_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setObjectName("TopographyPage")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        with open("Styles/styleTopographyPage.qss", "r") as f:
            self.setStyleSheet(f.read())

        layout = QVBoxLayout(self)
        title = QLabel("Topographic Map")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self.graph = pg.GraphicsLayoutWidget()
        layout.addWidget(self.graph, stretch=1)

        self.plot = self.graph.addPlot()
        self.img_item = pg.ImageItem()
        self.plot.addItem(self.img_item)

        # Axis labels
        self.plot.setLabel("bottom", "Trial Data Over 10 Seconds")
        self.plot.setLabel("left",   "Index Layer")

        self.plot.invertY(True)      # Keep row-0 at the top

        back_btn = QPushButton("Back")
        back_btn.clicked.connect(self.back_requested.emit)
        layout.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Color map setup
        cmap = cm.get_cmap("Greens")
        self.green_lut = (cmap(np.linspace(0, 1, 256)) * 255).astype(np.ubyte)

        self._set_trial_ticks()
        self.load_data()

    def load_data(self):
        try:
            if not os.path.exists(TRIAL_FILE):
                raise FileNotFoundError("trials.txt not found")

            arr = np.genfromtxt(TRIAL_FILE, delimiter=",", dtype=float,
                                filling_values=np.nan)

            if arr.size == 0 or np.isnan(arr).all():
                raise ValueError("No valid numbers in trials.txt")

            if arr.ndim == 1:
                arr = arr.reshape(1, -1)

            # Crop/pad to fixed frame
            arr = arr[:MAX_TRIALS, :MAX_VALUES_PER_TRIAL]
            if arr.shape[1] < MAX_VALUES_PER_TRIAL:
                pad = MAX_VALUES_PER_TRIAL - arr.shape[1]
                arr = np.hstack([arr, np.full((arr.shape[0], pad), np.nan)])
            if arr.shape[0] < MAX_TRIALS:
                pad = MAX_TRIALS - arr.shape[0]
                arr = np.vstack([arr, np.full((pad, arr.shape[1]), np.nan)])

            # Normalize data
            row_max = arr.max(axis=1, keepdims=True)
            row_max[row_max == 0] = 1.0
            norm = arr / row_max

            # rotate so trials run along X
            img = norm.T                         # shape (100, 4)
            self.img_item.setLookupTable(self.green_lut)
            self.img_item.setImage(img, autoLevels=False, levels=(0, 1))

            # Display image
            self.img_item.setLookupTable(self.green_lut)
            self.img_item.setImage(img, autoLevels=True)

        except Exception:
            pass

    def _set_trial_ticks(self):
        """
        Put one major tick in the middle of every trial stripe and
        label them 1 … MAX_TRIALS (instead of the default 0,0.5,1…).
        """
        axis = self.plot.getAxis("left")          # y-axis
        ticks = [[(i + 0.5, str(i + 1))            # centre of each row
                for i in range(MAX_TRIALS)]]
        axis.setTicks(ticks)
        axis.setTickSpacing(1, 1)

    def refresh(self):
        self.load_data()
