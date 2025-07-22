# Imports
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton
)
from PyQt6.QtCore    import Qt, pyqtSignal, QSize
from PyQt6.QtGui     import QIcon, QCursor


class PowerPongPageWidget(QWidget):
    back_requested = pyqtSignal()
    valueChanged   = pyqtSignal(int)          # emits on every bump

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        # give QSS something to target
        self.setObjectName("PowerPongPage")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        # GLOBAL PAGE LAYOUT ─────────────────────────────────────────
        layout = QVBoxLayout(self)
        layout.setSpacing(24)

        title = QLabel("Power Pong Game", alignment=Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("Title")
        layout.addWidget(title)

        # VALUE PICKER ───────────────────────────────────────────────
        picker_layout = QVBoxLayout()
        picker_layout.setSpacing(8)
        picker_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        # internal state
        self._value, self._min, self._max, self._step = 0, 0, 99, 1

        # numeric display
        self.display = QLabel(str(self._value), alignment=Qt.AlignmentFlag.AlignCenter)
        self.display.setObjectName("ValueDisplay")
        self.display.setFixedWidth(90)

        # helper: arrow button factory
        def make_arrow(path: str, obj_name: str) -> QPushButton:
            btn = QPushButton()
            btn.setObjectName(obj_name)                # ArrowBtn
            btn.setIcon(QIcon(path))
            btn.setIconSize(QSize(40, 40))
            btn.setFixedSize(64, 64)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            return btn

        up_btn   = make_arrow("images/arrow_up.png",   "ArrowBtn")
        down_btn = make_arrow("images/arrow_down.png", "ArrowBtn")

        up_btn.clicked.connect(lambda: self._bump(+self._step))
        down_btn.clicked.connect(lambda: self._bump(-self._step))

        picker_layout.addWidget(up_btn)
        picker_layout.addWidget(self.display)
        picker_layout.addWidget(down_btn)
        layout.addLayout(picker_layout, stretch=1)


        # ── FORE! button (does nothing for now) ─────────────────────
        fore_btn = QPushButton("FORE!")
        fore_btn.setObjectName("ForeBtn")
        # you can connect later:  fore_btn.clicked.connect(self.some_slot)
        layout.addWidget(fore_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        # ── back button ─────────────────────────────────────────────
        back_btn = QPushButton("Back")

        # BACK BUTTON ────────────────────────────────────────────────
        back_btn = QPushButton("Back")
        back_btn.setObjectName("BackBtn")
        back_btn.clicked.connect(self.back_requested.emit)
        layout.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        # finally load QSS for this page
        with open("Styles/stylePowerPongPage.qss") as f:
            self.setStyleSheet(f.read())

    # ---------------------------------------------------------------
    # helpers
    def _bump(self, delta: int):
        new_val = self._value + delta
        if self._min <= new_val <= self._max:
            self._value = new_val
            self.display.setText(str(self._value))
            self.valueChanged.emit(self._value)

    def value(self) -> int:
        return self._value
