# Imports
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore    import Qt, pyqtSignal
from PyQt6.QtGui     import QPixmap

# Config

class MotorFunPageWidget(QWidget):
    back_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("MotorFunPage")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        with open("Styles/styleMotorFunPage.qss", "r") as f:
            self.setStyleSheet(f.read())

        layout = QVBoxLayout(self)

        title = QLabel("More Motor Fun!", alignment=Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("Title")
        layout.addWidget(title)

        # Placeholder for the game content
        self.game_content = QLabel("Game content goes here.")
        self.game_content.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.game_content, stretch=1)

        back_btn = QPushButton("Back")
        back_btn.clicked.connect(self.back_requested.emit)
        layout.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

    def go_back(self):
        self.back_requested.emit()