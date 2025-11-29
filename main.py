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
from Animation.SpringDampenerAnimation import SpringDampenerAnimation
from Animation.HapticFeedbackAnimation import HapticFeedbackAnimation


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
        
        # Animation state tracking
        self.animation_in_progress = False
        
        # Clear data files on startup
        self.clear_data_files()
        
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
        
        # Clear data files when entering main menu
        self.clear_data_files()
        
        # Enable all buttons after startup animation completes
        self.animation_in_progress = False
        self.enable_all_buttons()
        
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
        self.menu_page.haptic_btn.clicked.connect(self.show_haptic_feedback_transition)
        self.menu_page.spgdmp_btn.clicked.connect(self.show_spring_dampener_transition)
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
        self.haptic_feedback_page.back_requested.connect(self.haptic_feedback_back)

        # page 6 → Spring Dampener Tuning Page
        self.spring_dampener_page = SpringDampenerPageWidget(self.ser)
        self.stack.addWidget(self.spring_dampener_page)
        self.spring_dampener_page.back_requested.connect(self.spring_dampener_back)
    
    def disable_all_buttons(self):
        """Disable all buttons during transition animations"""
        if self.menu_page:
            self.menu_page.afm_btn.setEnabled(False)
            self.menu_page.pwrpng_btn.setEnabled(False)
            self.menu_page.haptic_btn.setEnabled(False)
            self.menu_page.spgdmp_btn.setEnabled(False)
    
    def enable_all_buttons(self):
        """Enable all buttons after transition animations complete"""
        if self.menu_page:
            self.menu_page.afm_btn.setEnabled(True)
            self.menu_page.pwrpng_btn.setEnabled(True)
            self.menu_page.haptic_btn.setEnabled(True)
            self.menu_page.spgdmp_btn.setEnabled(True)
    
    def clear_data_files(self):
        """Clear swingData.txt and trials.txt files"""
        data_files = ["swingData.txt", "trials.txt"]
        for filename in data_files:
            try:
                if os.path.exists(filename):
                    with open(filename, 'w') as f:
                        f.write("")  # Clear the file content
            except Exception:
                pass  # Silently ignore any file operation errors
        
        # Refresh topography page to show empty state
        if hasattr(self, 'topo_page') and self.topo_page:
            self.topo_page.refresh()
        
    def show_afm_transition(self):
        """Show AFM transition animation before switching to AFM page"""
        if self.animation_in_progress:
            return
            
        self.animation_in_progress = True
        self.disable_all_buttons()
        
        # Send AFM command to Arduino immediately (A = AFM mode)
        self.ser.write(b"A\n")
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
        
        # Re-enable buttons after transition completes
        self.animation_in_progress = False
        self.enable_all_buttons()
        
    def complete_afm_back_transition(self):
        """Called when coming back from AFM page to main menu"""
        # CRITICAL: Clear serial buffers to prevent conflicts
        try:
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
        except:
            pass
        
        # Clear data files when returning to main menu
        self.clear_data_files()
        
        # Switch to main menu page
        self.stack.setCurrentWidget(self.menu_page)
        
        # Start the blue circle shrinking animation (coming back from AFM)
        self.menu_page.start_blue_circle_animation()
        
    def show_power_pong_transition(self):
        """Show Power Pong transition animation before switching to Power Pong page"""
        if self.animation_in_progress:
            return
            
        self.animation_in_progress = True
        self.disable_all_buttons()
        
        # Send Power Pong command to Arduino immediately (P = Power Pong mode)
        self.ser.write(b"P\n")
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
        
        # Re-enable buttons after transition completes
        self.animation_in_progress = False
        self.enable_all_buttons()

    def complete_power_pong_back_transition(self):
        """Called when coming back from Power Pong page to main menu"""
        # Send MAIN_MENU command to Arduino to reset it from Power Pong mode
        
        # Clear data files when returning to main menu
        self.clear_data_files()
        
        # Switch to main menu page
        self.stack.setCurrentWidget(self.menu_page)
        
        # Start the white circle shrinking animation (coming back from Power Pong)
        self.menu_page.start_white_circle_animation()

    def show_spring_dampener_transition(self):
        """Show Spring Dampener transition animation before switching to Spring Dampener page"""
        if self.animation_in_progress:
            return
            
        self.animation_in_progress = True
        self.disable_all_buttons()
        
        # Clear any leftover serial data from previous modes
        self.ser.reset_input_buffer()
        
        # Send Spring Dampener command to Arduino immediately (S = Spring Dampener mode)
        self.ser.write(b"S\n")
        self.ser.flush()
        
        # Create Spring Dampener transition animation
        self.spring_dampener_transition = SpringDampenerAnimation()
        
        self.spring_dampener_transition.animation_complete.connect(self.complete_spring_dampener_transition)
        
        # Show animation as overlay - set parent to stack widget for proper positioning
        self.spring_dampener_transition.setParent(self.stack)
        self.spring_dampener_transition.raise_()
        self.spring_dampener_transition.show()
        
        # Start animation
        self.spring_dampener_transition.start_animation()
        
    def complete_spring_dampener_transition(self):
        """Called when Spring Dampener transition animation completes"""
        # Hide the transition animation
        if hasattr(self, 'spring_dampener_transition'):
            self.spring_dampener_transition.hide()
            self.spring_dampener_transition.deleteLater()
        
        # Switch to Spring Dampener page
        self.stack.setCurrentWidget(self.spring_dampener_page)
        
        # Re-enable buttons after transition completes
        self.animation_in_progress = False
        self.enable_all_buttons()

    def show_haptic_feedback_transition(self):
        """Show Haptic Feedback transition animation before switching to Haptic Feedback page"""
        if self.animation_in_progress:
            return
            
        self.animation_in_progress = True
        self.disable_all_buttons()
        
        # Clear any leftover serial data from previous modes
        self.ser.reset_input_buffer()
        
        # Send Haptic Feedback command to Arduino immediately (H = Haptic Feedback mode)
        self.ser.write(b"H\n")
        self.ser.flush()
        
        # Create Haptic Feedback transition animation
        self.haptic_feedback_transition = HapticFeedbackAnimation()
        
        self.haptic_feedback_transition.animation_complete.connect(self.complete_haptic_feedback_transition)
        
        # Show animation as overlay - set parent to stack widget for proper positioning
        self.haptic_feedback_transition.setParent(self.stack)
        self.haptic_feedback_transition.raise_()
        self.haptic_feedback_transition.show()
        
        # Start animation
        self.haptic_feedback_transition.start_animation()
        
    def complete_haptic_feedback_transition(self):
        """Called when Haptic Feedback transition animation completes"""
        # Hide the transition animation
        if hasattr(self, 'haptic_feedback_transition'):
            self.haptic_feedback_transition.hide()
            self.haptic_feedback_transition.deleteLater()
        
        # Switch to Haptic Feedback page
        self.stack.setCurrentWidget(self.haptic_feedback_page)
        
        # Start the shrinking circle animation to reveal the page
        self.haptic_feedback_page.start_shrink_animation()
        
        # Re-enable buttons after transition completes
        self.animation_in_progress = False
        self.enable_all_buttons()



    def haptic_feedback_back(self):
        """Send stop command to Arduino and return to main menu from Haptic Feedback page"""
        
        # Clear data files when returning to main menu
        self.clear_data_files()
        
        # Switch to main menu page
        self.stack.setCurrentWidget(self.menu_page)
        
        # Start the white circle shrinking animation (coming back from Haptic Feedback)
        self.menu_page.start_white_circle_animation()



    def spring_dampener_back(self):
        """Send stop command to Arduino and return to main menu from Spring Dampener page"""
        
        # Clear data files when returning to main menu
        self.clear_data_files()
        
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
