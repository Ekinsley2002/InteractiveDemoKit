from pathlib import Path
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore    import Qt, QSize, pyqtSignal
from PyQt6.QtGui     import QIcon, QCursor
import serial

PROJECT_ROOT = Path(__file__).resolve().parent.parent
IMAGES_DIR   = Path("Images")
STYLES_DIR   = PROJECT_ROOT / "Styles"


class Picker(QWidget):
    """One vertical picker column with ▲ / ▼ / Add."""
    value_added = pyqtSignal(str)

    COL_W = 200

    def __init__(self, title: str, min_val: float = 0, max_val: float = 50, is_float: bool = False, parent: QWidget | None = None):
        super().__init__(parent)
        self._value = min_val
        self._min_val = min_val
        self._max_val = max_val
        self._is_float = is_float
        self._increment = 0.1 if is_float else 1

        v = QVBoxLayout(self)
        v.setSpacing(12)
        v.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        title_lbl = QLabel(title, alignment=Qt.AlignmentFlag.AlignHCenter)
        title_lbl.setObjectName("PickerTitle")
        title_lbl.setFixedWidth(self.COL_W)

        self.value_lbl = QLabel(str(self._value), alignment=Qt.AlignmentFlag.AlignHCenter)
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
        new_value = self._value + (delta * self._increment)
        if self._min_val <= new_value <= self._max_val:
            self._value = new_value
            display_text = f"{self._value:.1f}" if self._is_float else str(int(self._value))
            self.value_lbl.setText(display_text)

    def _emit_add(self):
        formatted_value = f"{self._value:.1f}" if self._is_float else str(int(self._value))
        self.value_added.emit(formatted_value)


class HapticFeedbackPageWidget(QWidget):
    """Haptic Feedback page with adjustable parameters for ticks and spring constant."""
    back_requested = pyqtSignal()

    def __init__(self, serial_connection=None, parent=None):
        super().__init__(parent)

        self.serial_connection = serial_connection

        self.setObjectName("HapticFeedbackPage")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        root = QVBoxLayout(self)

        # Add yellow title at the very top center
        title = QLabel("Haptic Feedback")
        title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        title.setObjectName("Title")
        root.addWidget(title)

        # Picker controls
        row = QHBoxLayout(); row.setSpacing(40)

        self.ticks_picker = Picker("Number of Ticks", 1, 20, is_float=False)
        self.spring_picker = Picker("Spring Constant", 0.1, 10.0, is_float=True)

        # Wire pickers to handle value changes
        self.ticks_picker.value_added.connect(self._send_num_ticks)
        self.spring_picker.value_added.connect(self._send_spring_constant)

        row.addStretch(1)
        row.addWidget(self.ticks_picker)
        row.addWidget(self.spring_picker)
        row.addStretch(1)

        root.addLayout(row, stretch=1)

        # Back button
        back_btn = QPushButton("Back")
        back_btn.setObjectName("BackBtn")
        back_btn.clicked.connect(self.go_back)
        root.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Load stylesheet
        css_file = STYLES_DIR / "styleHapticFeedbackPage.qss"
        if css_file.exists():
            self.setStyleSheet(css_file.read_text())
        else:
            # Fallback styling if CSS file doesn't exist
            self.setStyleSheet("""
                QWidget#HapticFeedbackPage {
                    background-color: #002454;
                    color: #FFFFFF;
                }
                QLabel#Title {
                    font: 600 32px 'Roboto';
                    color: #FAC01A;
                    margin: 20px 0px;
                }
                QLabel#PickerTitle {
                    font: 600 18px 'Roboto';
                    color: #FFFFFF;
                }
                QLabel#ValueDisplay {
                    font: 600 24px 'Roboto';
                    color: #FAC01A;
                    background-color: rgba(255,255,255,0.10);
                    border: 2px solid #FAC01A;
                    border-radius: 8px;
                }
                QPushButton#ArrowBtn {
                    background-color: rgba(255,255,255,0.05);
                    border: 2px solid #FAC01A;
                    border-radius: 8px;
                }
                QPushButton#ArrowBtn:hover {
                    background-color: rgba(255,255,255,0.10);
                }
                QPushButton#AddBtn {
                    font: 600 16px 'Roboto';
                    color: #FFFFFF;
                    background-color: rgba(255,255,255,0.05);
                    border: 2px solid #FAC01A;
                    border-radius: 8px;
                    padding: 8px 16px;
                }
                QPushButton#AddBtn:hover {
                    background-color: rgba(255,255,255,0.10);
                }
                QPushButton#BackBtn {
                    font: 600 18px 'Roboto';
                    color: #FFFFFF;
                    background-color: rgba(255,255,255,0.05);
                    border: 2px solid #FAC01A;
                    border-radius: 8px;
                    padding: 12px 24px;
                    min-width: 200px;
                }
                QPushButton#BackBtn:hover {
                    background-color: rgba(255,255,255,0.10);
                }
            """)

    # Serial communication helpers
    def _write(self, text: str):
        """Low-level send. Falls back to console print when no port present."""
        if self.serial_connection is None:
            print("→", text.strip())
            return
        self.serial_connection.write(text.encode())
        self.serial_connection.flush()

    def _send_num_ticks(self, value: str):
        """Send number of ticks command: n{value}"""
        self._write(f"n{value}\n")

    def _send_spring_constant(self, value: str):
        """Send spring constant command: k{value}"""
        self._write(f"k{value}\n")

    def go_back(self):
        """Emit back signal to return to main menu"""
        self.back_requested.emit()
