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

from PyQt6.QtCore import Qt, QCoreApplication, pyqtSignal
from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PyQt6.QtGui import QCursor

# ── IMPORT GUI PAGES AFTER SCALE SETTINGS ─────────────────────────────
from GUI.MainMenuGUI   import MenuPage
from GUI.AfmGUI        import AfmPageWidget
from GUI.TopographyGUI import TopographyPageWidget
from GUI.PowerPongGUI  import PowerPongPageWidget
from GUI.MotorFunGUI    import MotorFunPageWidget
from Animation.StartupAnimation import StartupAnimation
from Animation.GraphingLineAnimation import GraphingLineAnimation
from Animation.PowerPongTransitionAnimation import PowerPongTransitionAnimation


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

        elif Config.DEVICE == "Windows":
            self.PORT = "COM3"

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
        
        # Set the main window background to blue
        self.setStyleSheet("""
            QMainWindow {
                background-color: #002454;
            }
        """)
        
        # Start with startup animation as the central widget
        self.startup_animation = StartupAnimation()
        self.startup_animation.animation_complete.connect(self.transition_to_main_menu)
        self.setCentralWidget(self.startup_animation)
        
        # Start the startup animation
        self.startup_animation.start_animation()

        # Don't create main menu pages yet - wait until startup animation completes
        # This prevents the white circle and other elements from bleeding through
        self.menu_page = None
        self.afm_page = None
        self.topo_page = None
        self.power_pong_page = None
        self.motor_fun_page = None

        # Don't show the main menu immediately - wait for startup animation
        # self.stack.setCurrentWidget(self.menu_page)  # Commented out

    def transition_to_main_menu(self):
        """Seamlessly transition from startup animation to main menu"""
        # Create all main menu pages now (after startup animation completes)
        self.create_main_menu_pages()
        
        # Replace the startup animation with the main menu stack
        self.setCentralWidget(self.stack)
        self.stack.setCurrentWidget(self.menu_page)
        
        # Start the yellow circle shrinking animation (coming from startup)
        self.menu_page.start_yellow_circle_animation()
    
    def create_main_menu_pages(self):
        """Create all main menu pages and set up navigation"""
        # page 0 → main menu
        self.menu_page = MenuPage(self.ser, self)  # Pass self (MainWindow) as parent
        self.stack.addWidget(self.menu_page)

        # page 1 → AFM live-plot
        self.afm_page = AfmPageWidget(self.ser)
        self.stack.addWidget(self.afm_page)

        # navigation wiring
        self.menu_page.afm_btn.clicked.connect(self.show_afm_transition)
        self.menu_page.pwrpng_btn.clicked.connect(self.show_power_pong_transition)
        self.afm_page.back_requested.connect(
            lambda: self.complete_afm_back_transition()
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
        
    def show_afm_transition(self):
        """Show AFM transition animation before switching to AFM page"""
        
        # Send AFM command to Arduino immediately (1 = AFM mode)
        self.ser.write(b"\x01")
        self.ser.flush()
        
        # Create graphing line animation
        self.afm_transition = GraphingLineAnimation()
        
        self.afm_transition.animation_complete.connect(self.complete_afm_transition)
        
        # Show animation as overlay
        self.afm_transition.setParent(self.stack)
        self.afm_transition.raise_()
        self.afm_transition.show()
        
        # Start animation
        self.afm_transition.start_animation()
        
    def complete_afm_transition(self):
        """Called when AFM transition animation completes"""
        
        # Hide the transition animation
        if hasattr(self, 'afm_transition'):
            self.afm_transition.hide()
            self.afm_transition.deleteLater()
        
        # Switch to AFM page (this will trigger the existing serial communication)
        self.stack.setCurrentWidget(self.afm_page)
        
    def complete_afm_back_transition(self):
        """Called when coming back from AFM page to main menu"""
        # Switch to main menu page
        self.stack.setCurrentWidget(self.menu_page)
        
        # Start the blue circle shrinking animation (coming back from AFM)
        self.menu_page.start_blue_circle_animation()
        
    def show_power_pong_transition(self):
        """Show Power Pong transition animation before switching to Power Pong page"""
        
        # Send Power Pong command to Arduino immediately (2 = Power Pong mode)
        self.ser.write(b"\x02")
        self.ser.flush()
        
        # Create Power Pong transition animation
        self.power_pong_transition = PowerPongTransitionAnimation()
        
        self.power_pong_transition.animation_complete.connect(self.complete_power_pong_transition)
        
        # Show animation as overlay - set parent to stack widget for proper positioning
        self.power_pong_transition.setParent(self.stack)
        self.power_pong_transition.raise_()
        self.power_pong_transition.show()
        
        # Start animation
        self.power_pong_transition.start_animation()
        
    def complete_power_pong_transition(self):
        """Called when Power Pong transition animation completes"""
        
        # Hide the transition animation
        if hasattr(self, 'power_pong_transition'):
            self.power_pong_transition.hide()
            self.power_pong_transition.deleteLater()
        
        # Switch to Power Pong page
        self.stack.setCurrentWidget(self.power_pong_page)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    # Show the main window immediately - it will display the startup animation first
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
