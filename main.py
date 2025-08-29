import os, sys, pathlib, serial, time
import Config

# DPI / Scale settings - must be set before QApplication exists
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
os.environ["QT_SCALE_FACTOR"]            = "1"
os.environ["QT_ENABLE_HIGHDPI_SCALING"]  = "0"

from pathlib import Path
import os

APP_DIR = Path(__file__).resolve().parent
os.chdir(APP_DIR)  # make relative paths resolve from project root


from PyQt6.QtCore import Qt, QCoreApplication, pyqtSignal
from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PyQt6.QtGui import QCursor

from GUI.MainMenuGUI   import MenuPage
from GUI.AfmGUI        import AfmPageWidget
from GUI.TopographyGUI import TopographyPageWidget
from GUI.PowerPongGUI  import PowerPongPageWidget
from GUI.HapticFeedbackGUI import HapticFeedbackPageWidget
from GUI.SpringDampenerGUI    import SpringDampenerPageWidget
from GUI.referencePageGUI import ReferencePageWidget
from Animation.StartupAnimation import StartupAnimation
from Animation.GraphingLineAnimation import GraphingLineAnimation
from Animation.PowerPongTransitionAnimation import PowerPongTransitionAnimation


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.BAUD = 115_200
        
        # Platform-specific port configuration
        if Config.DEVICE == "Mac":
            self.PORT = "/dev/cu.usbmodem14101"
        elif Config.DEVICE == "Linux":
            self.PORT = "/dev/ttyACM0"
            self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
            self.showFullScreen()
            self.setCursor(QCursor(Qt.CursorShape.BlankCursor))
        elif Config.DEVICE == "Windows":
            self.PORT = "COM4"

        # Serial connection setup
        if Config.BOARDLESS:
            self.ser = serial.serial_for_url("loop://", timeout=1)
        else:
            self.ser = serial.Serial(self.PORT, self.BAUD, timeout=1)

        self.setWindowTitle("Interactive Demo Kit")

        # Window configuration
        self.setFixedSize(800, 480)
        self.setWindowFlag(Qt.WindowType.WindowMinimizeButtonHint, False)
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, False)

        # Page container
        self.stack = QStackedWidget(self)
        
        # Main window styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #002454;
            }
        """)
        
        # Startup animation setup
        self.startup_animation = StartupAnimation()
        self.startup_animation.animation_complete.connect(self.transition_to_main_menu)
        self.setCentralWidget(self.startup_animation)
        self.startup_animation.start_animation()

        # Initialize page references (created after startup animation)
        self.menu_page = None
        self.afm_page = None
        self.topo_page = None
        self.reference_page = None
        self.power_pong_page = None
        self.haptic_feedback_page = None
        self.spring_dampener_page = None

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

        # page 3 → Reference Page
        self.reference_page = ReferencePageWidget()
        self.stack.addWidget(self.reference_page)
        self.afm_page.references_requested.connect(
            lambda: self.stack.setCurrentWidget(self.reference_page)
        )
        self.reference_page.back_requested.connect(
            lambda: self.stack.setCurrentWidget(self.afm_page)
        )

        # page 4 → Power-Pong
        self.power_pong_page = PowerPongPageWidget(self.ser)
        self.stack.addWidget(self.power_pong_page)
        self.power_pong_page.back_requested.connect(self.complete_power_pong_back_transition)

        # page 5 → Haptic Feedback
        self.haptic_feedback_page = HapticFeedbackPageWidget(self.ser)
        self.stack.addWidget(self.haptic_feedback_page)
        self.menu_page.haptic_btn.clicked.connect(self.show_haptic_feedback)
        self.haptic_feedback_page.back_requested.connect(self.haptic_feedback_back)

        # page 6 → Spring Dampener Tuning Page
        self.spring_dampener_page = SpringDampenerPageWidget(self.ser)
        self.stack.addWidget(self.spring_dampener_page)
        self.menu_page.spgdmp_btn.clicked.connect(self.show_spring_dampener)
        self.spring_dampener_page.back_requested.connect(self.spring_dampener_back)
        
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

    def complete_power_pong_back_transition(self):
        """Called when coming back from Power Pong page to main menu"""
        # Send MAIN_MENU command to Arduino to reset it from Power Pong mode
        self.ser.write(b"\x00")
        self.ser.flush()
        
        # Switch to main menu page
        self.stack.setCurrentWidget(self.menu_page)
        
        # Start the white circle shrinking animation (coming back from Power Pong)
        self.menu_page.start_white_circle_animation()

    def show_haptic_feedback(self):
        """Send Haptic Feedback command to Arduino and switch to Haptic Feedback page"""
        
        # Send Haptic Feedback command to Arduino (3 = Haptic Feedback mode)
        self.ser.write(b"\x03")
        self.ser.flush()
        
        # Switch directly to Haptic Feedback page (no transition animation)
        self.stack.setCurrentWidget(self.haptic_feedback_page)

    def haptic_feedback_back(self):
        """Send stop command to Arduino and return to main menu from Haptic Feedback page"""
        
        # Send stop command to Arduino (0 = stop/idle mode)
        self.ser.write(b"\x00")
        self.ser.flush()
        
        # Switch back to main menu
        self.stack.setCurrentWidget(self.menu_page)

    def show_spring_dampener(self):
        """Send Spring Dampener command to Arduino and switch to Spring Dampener page"""
        
        # Send Spring Dampener command to Arduino (4 = Spring Dampener mode)
        self.ser.write(b"\x04")
        self.ser.flush()
        
        # Switch directly to Spring Dampener page (no transition animation)
        self.stack.setCurrentWidget(self.spring_dampener_page)

    def spring_dampener_back(self):
        """Send stop command to Arduino and return to main menu from Spring Dampener page"""
        
        # Send stop command to Arduino (0 = stop/idle mode)
        self.ser.write(b"\x00")
        self.ser.flush()
        
        # Switch back to main menu
        self.stack.setCurrentWidget(self.menu_page)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    # Show the main window immediately - it will display the startup animation first
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
