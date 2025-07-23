# power_pong_page.py  – full path-safe version
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui  import QIcon, QCursor


# -------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent   # …/InteractiveDemoKitV2-1
IMAGES_DIR   = PROJECT_ROOT / "images"
STYLES_DIR   = PROJECT_ROOT / "Styles"


# ────────────────────────────────────────────────────────────────
class Picker(QWidget):
    """One vertical picker column with ▲ / ▼ / Add."""
    value_added = pyqtSignal(int)

    COL_W = 200

    def __init__(self, title: str, parent: QWidget | None = None):
        super().__init__(parent)
        self._value = 0

        v = QVBoxLayout(self)
        v.setSpacing(12)
        v.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        title_lbl = QLabel(title, alignment=Qt.AlignmentFlag.AlignCenter)
        title_lbl.setObjectName("PickerTitle")
        title_lbl.setFixedWidth(self.COL_W)

        self.value_lbl = QLabel("0", alignment=Qt.AlignmentFlag.AlignCenter)
        self.value_lbl.setObjectName("ValueDisplay")
        self.value_lbl.setFixedSize(self.COL_W, 64)

        up_btn   = self._make_arrow("arrow_up.png",   +1)
        down_btn = self._make_arrow("arrow_down.png", -1)

        add_btn  = QPushButton("Add")
        add_btn.setObjectName("AddBtn")
        add_btn.setFixedSize(120, 44)
        add_btn.clicked.connect(self._emit_add)

        v.addWidget(title_lbl)
        v.addWidget(up_btn)
        v.addWidget(self.value_lbl)
        v.addWidget(down_btn)
        v.addStretch(1)
        v.addWidget(add_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

    # helpers ------------------------------------------------------
    def _make_arrow(self, filename: str, delta: int) -> QPushButton:
        path = IMAGES_DIR / filename
        btn  = QPushButton()
        btn.setObjectName("ArrowBtn")
        btn.setIcon(QIcon(str(path)))
        btn.setIconSize(QSize(40, 40))
        btn.setFixedSize(self.COL_W, 64)
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.clicked.connect(lambda: self._bump(delta))
        return btn

    def _bump(self, delta: int):
        self._value += delta
        self.value_lbl.setText(str(self._value))

    def _emit_add(self):
        self.value_added.emit(self._value)


# ────────────────────────────────────────────────────────────────
class PowerPongPageWidget(QWidget):
    back_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self.setObjectName("PowerPongPage")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        root = QVBoxLayout(self)

        title = QLabel("Power Pong Game", alignment=Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("Title")
        root.addWidget(title)

        # ───────── PICKERS + FORE ROW ─────────
        row = QHBoxLayout()
        row.setSpacing(40)

        self.speed_picker  = Picker("Speed")
        self.offset_picker = Picker("Offset")

        self.speed_picker.value_added.connect(lambda v: print("Speed added:",  v))
        self.offset_picker.value_added.connect(lambda v: print("Offset added:", v))

        row.addStretch(1)
        row.addWidget(self.speed_picker)
        row.addWidget(self.offset_picker)
        row.addStretch(1)

        fore_btn = QPushButton("FORE!")
        fore_btn.setObjectName("ForeBtn")
        row.addWidget(fore_btn)

        row.addStretch(1)
        root.addLayout(row, stretch=1)

        # ───────── BACK ─────────
        back_btn = QPushButton("Back")
        back_btn.setObjectName("BackBtn")
        back_btn.clicked.connect(self.back_requested.emit)
        root.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        # ───────── QSS ─────────
        css_file = STYLES_DIR / "stylePowerPongPage.qss"
        self.setStyleSheet(css_file.read_text())
