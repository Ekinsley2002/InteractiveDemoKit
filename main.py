# main.py  –  app entry point & page router
import os, sys, pathlib, serial, time
import Config

# ── HARD-CODED DPI / SCALE SETTINGS ────────────────────────────────────
#
#  ⚠️  These three env-vars must be set *before* the QApplication exists.
#      They turn off every automatic scaling feature Qt knows about.
#
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
os.environ["QT_SCALE_FACTOR"]            = "1"
os.environ["QT_ENABLE_HIGHDPI_SCALING"]  = "0"

from PyQt6.QtCore import Qt, QCoreApplication
from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PyQt6.QtGui import QCursor

# ── IMPORT GUI PAGES AFTER SCALE SETTINGS ─────────────────────────────
from GUI.MainMenuGUI   import MenuPage
from GUI.AfmGUI        import AfmPageWidget
from GUI.TopographyGUI import TopographyPageWidget
from GUI.PowerPongGUI  import PowerPongPageWidget
from GUI.MotorFunGUI    import MotorFunPageWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.BAUD = 115_200
        
        # Check to see which device to use
        if Config.DEVICE == "Mac":
            self.PORT = "/dev/cu.usbmodem14101"

        elif Config.DEVICE == "Linux":
            self.PORT = "/dev/ttyACM0"
            self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
            self.showFullScreen()
            self.setCursor(QCursor(Qt.CursorShape.BlankCursor))

        # Check to see if using board, if not, set up fake serial
        if Config.BOARDLESS:
            self.ser = serial.serial_for_url("loop://", timeout=1)
        else:
            self.ser  = serial.Serial(self.PORT, self.BAUD, timeout=1)

        self.setWindowTitle("Interactive Demo Kit")

        # ▸ Fix the window at EXACTLY 800×480 and remove the maximise box
        self.setFixedSize(800, 480)
        self.setWindowFlag(Qt.WindowType.WindowMinimizeButtonHint, False)
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, False)

        # ── stacked-page container ──────────────────────────────────
        self.stack = QStackedWidget(self)
        self.setCentralWidget(self.stack)

        # page 0 → main menu
        self.menu_page = MenuPage(self.ser)
        self.stack.addWidget(self.menu_page)

        # page 1 → AFM live-plot
        self.afm_page = AfmPageWidget(self.ser)
        self.stack.addWidget(self.afm_page)

        # navigation wiring
        self.menu_page.afm_btn.clicked.connect(
            lambda: self.stack.setCurrentWidget(self.afm_page)
        )
        self.afm_page.back_requested.connect(
            lambda: self.stack.setCurrentWidget(self.menu_page)
        )

        # page 2 → Topography
        self.topo_page = TopographyPageWidget()
        self.stack.addWidget(self.topo_page)
        self.afm_page.map_requested.connect(self.topo_page.refresh)
        self.afm_page.map_requested.connect(
            lambda: self.stack.setCurrentWidget(self.topo_page)
        )
        self.topo_page.back_requested.connect(
            lambda: self.stack.setCurrentWidget(self.afm_page)
        )

        # page 3 → Power-Pong
        self.power_pong_page = PowerPongPageWidget(self.ser)
        self.stack.addWidget(self.power_pong_page)
        self.menu_page.pwrpng_btn.clicked.connect(
            lambda: self.stack.setCurrentWidget(self.power_pong_page)
        )
        self.power_pong_page.back_requested.connect(
            lambda: self.stack.setCurrentWidget(self.menu_page)
        )

        # page 4 → Fun-with-Motors (re-uses PowerPong widget for now)
        self.motor_fun_page = MotorFunPageWidget()
        self.stack.addWidget(self.motor_fun_page)
        self.menu_page.mtrfun_btn.clicked.connect(
            lambda: self.stack.setCurrentWidget(self.motor_fun_page)
        )
        self.motor_fun_page.back_requested.connect(
            lambda: self.stack.setCurrentWidget(self.menu_page)
        )

        # show the main menu first
        self.stack.setCurrentWidget(self.menu_page)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()                 # or window.showFullScreen() as noted
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
