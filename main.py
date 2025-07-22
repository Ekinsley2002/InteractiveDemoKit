# main.py  –  app entry point & page router
import sys
import pathlib
from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from GUI.MainMenuGUI   import MenuPage
from GUI.AfmGUI      import AfmPageWidget
from GUI.TopographyGUI import TopographyPageWidget
from GUI.PowerPongGUI import PowerPongPageWidget
import serial, time


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.PORT = "/dev/cu.usbmodem14101" 
        self.BAUD = 115_200

        self.ser = serial.Serial(self.PORT, self.BAUD, timeout=1)

        self.setWindowTitle("Interactive Demo Kit")
        self.resize(800, 480)

        # ── stacked‑page container ──────────────────────────────────
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # page 0 → main menu
        self.menu_page = MenuPage(self.ser)
        self.stack.addWidget(self.menu_page)
        
        # page 1 → AFM live‑plot
        self.afm_page = AfmPageWidget(self.ser)
        self.stack.addWidget(self.afm_page)

        # ── navigation wiring ───────────────────────────────────────
        self.menu_page.afm_btn.clicked.connect(
            lambda: self.stack.setCurrentWidget(self.afm_page)
        )
        self.afm_page.back_requested.connect(
            lambda: self.stack.setCurrentWidget(self.menu_page)
        )

        # page 2 → Topography page
        self.topo_page = TopographyPageWidget()
        self.stack.addWidget(self.topo_page)

        # connect AfmPageWidget to TopographyPageWidget
        self.afm_page.map_requested.connect(self.topo_page.refresh)
        self.afm_page.map_requested.connect(
            lambda: self.stack.setCurrentWidget(self.topo_page)
        ) 

        # Topography back to AfmPageWidget
        self.topo_page.back_requested.connect(
            lambda: self.stack.setCurrentWidget(self.afm_page)
        )

        # page 3 → Power Pong Page
        self.power_pong_page = PowerPongPageWidget()
        self.stack.addWidget(self.power_pong_page)
        
        self.menu_page.pwrpng_btn.clicked.connect(
            lambda: self.stack.setCurrentWidget(self.power_pong_page)
        )

        self.power_pong_page.back_requested.connect(
            lambda: self.stack.setCurrentWidget(self.menu_page)
        )

        # page 4 → Fun Applications of Motors Page
        self.motor_fun_page = PowerPongPageWidget()
        self.stack.addWidget(self.motor_fun_page)
        
        self.menu_page.mtrfun_btn.clicked.connect(
            lambda: self.stack.setCurrentWidget(self.motor_fun_page)
        )

        self.motor_fun_page.back_requested.connect(
            lambda: self.stack.setCurrentWidget(self.menu_page)
        )

        # start on the menu
        self.stack.setCurrentWidget(self.menu_page)


def main():

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
