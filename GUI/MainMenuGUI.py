
from pathlib import Path
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PyQt6.QtCore    import Qt, QTimer, QPointF
from PyQt6.QtGui     import QPixmap, QTransform, QPainter, QColor
import Config


class YellowCircleOverlay(QWidget):
    """Separate overlay widget for the shrinking yellow circle animation"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)  # Pass through mouse events
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        # Animation properties
        self.circle_radius = 1000  # Start with full screen coverage
        self.circle_center = QPointF(400, 240)  # Center of screen
        self.visible = True
        
        # Set a solid background to ensure visibility
        self.setStyleSheet("background-color: transparent;")  # Start transparent
        
    def update_circle(self, radius):
        """Update the circle radius for animation"""
        self.circle_radius = radius
        self.update()
        
    def set_animation_state(self, active):
        """Set whether the animation is active"""
        self.visible = active
        self.update()
        
    def paintEvent(self, event):
        """Draw the shrinking yellow circle overlay"""
        if not self.visible:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw yellow circle that covers the screen and shrinks
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(250, 192, 26))  # #FAC01A
        painter.drawEllipse(self.circle_center, self.circle_radius, self.circle_radius)


class BlueCircleOverlay(QWidget):
    """Separate overlay widget for the shrinking blue circle animation"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)  # Pass through mouse events
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        # Animation properties
        self.circle_radius = 1000  # Start with full screen coverage
        self.circle_center = QPointF(400, 240)  # Center of screen
        self.visible = True
        
        # Set a solid background to ensure visibility
        self.setStyleSheet("background-color: transparent;")  # Start transparent
        
    def update_circle(self, radius):
        """Update the circle radius for animation"""
        self.circle_radius = radius
        self.update()
        
    def set_animation_state(self, active):
        """Set whether the animation is active"""
        self.visible = active
        self.update()
        
    def paintEvent(self, event):
        """Draw the shrinking blue circle overlay"""
        if not self.visible:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw blue circle that covers the screen and shrinks
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 36, 84))  # #002454
        painter.drawEllipse(self.circle_center, self.circle_radius, self.circle_radius)


class WhiteCircleOverlay(QWidget):
    """Separate overlay widget for the shrinking white circle animation when coming back from Power Pong"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)  # Pass through mouse events
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        # Animation properties
        self.circle_radius = 1000  # Start with full screen coverage
        self.circle_center = QPointF(400, 240)  # Center of screen
        self.visible = True
        
        # Set a solid background to ensure visibility
        self.setStyleSheet("background-color: transparent;")  # Start transparent
        
    def update_circle(self, radius):
        """Update the circle radius for animation"""
        self.circle_radius = radius
        self.update()
        
    def set_animation_state(self, active):
        """Set whether the animation is active"""
        self.visible = active
        self.update()
        
    def paintEvent(self, event):
        """Draw the shrinking white circle overlay"""
        if not self.visible:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw white circle that covers the screen and shrinks
        painter.setPen(Qt.PenStyle.NoPen)  # No outline
        painter.setBrush(QColor(255, 255, 255))  # White fill
        painter.drawEllipse(self.circle_center, self.circle_radius, self.circle_radius)


class MenuPage(QWidget):
    def __init__(self, ser, main_window=None, parent=None):
        super().__init__(parent)
        self.ser = ser
        self.main_window = main_window  # Store reference to main window

        self.setObjectName("CentralArea")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        with open("Styles/styleMainPage.qss") as f:
            self.setStyleSheet(f.read())

        lay = QVBoxLayout(self)
        lay.setSpacing(12)  # Reduced from 20 to save space
        lay.setContentsMargins(0, 0, 0, 0)  # Remove margins to prevent white areas
        
        # Logo setup
        base_dir = Path(__file__).resolve().parent.parent
        logo_path = "Images/logoBackground.png"

        logo_lbl = QLabel()
        pix = QPixmap(str(logo_path))                  # always pass str(…) to Qt
        if not pix.isNull():                          # file found – show it
            pix = pix.scaledToWidth(
                355, Qt.TransformationMode.SmoothTransformation
            )
            logo_lbl.setPixmap(pix)
        else:                                         # fallback: text placeholder
            logo_lbl.setText("[ logoBackground.png not found ]")
            logo_lbl.setStyleSheet("color:#CEF9F2; font:600 18px 'Roboto';")

        logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_lbl.setStyleSheet("background-color: transparent;")  # Ensure logo has no background
        
        # Rotating gear setup
        gear_path = base_dir / "Animation" / "Sprites" / "gearMainMenu.png"
        if gear_path.exists():
            self.original_gear_pixmap = QPixmap(str(gear_path))
        else:
            self.original_gear_pixmap = QPixmap()
        
        # Create gear label that will rotate around the logo
        self.gear_label = QLabel()
        self.gear_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.gear_size = 324  # Same size as startup animation
        self.gear_label.setFixedSize(self.gear_size, self.gear_size)  # Fixed size for precise positioning
        self.gear_label.setStyleSheet("background-color: transparent;")
        
        # Position gear using easily adjustable x,y coordinates
        # Adjust these values to position the gear exactly where you want it
        self.gear_x = 221  # X coordinate in pixels (0 = left edge, 800 = right edge)
        self.gear_y = -60  # Y coordinate: negative to make gear "touch" top of screen
        
        # Position the gear at the specified coordinates
        self.gear_label.move(self.gear_x, self.gear_y)
        
        # Add the logo directly to the main layout
        lay.addWidget(logo_lbl, alignment=Qt.AlignmentFlag.AlignHCenter)
        
        # Add gear label as a direct child of the main window for free positioning
        # This removes it from any layout constraints
        self.gear_label.setParent(self)
        self.gear_label.raise_()  # Ensure it's on top of everything
        
        # Gear rotation animation
        self.rotation_angle = 0  # Current rotation angle in degrees
        self.rotation_speed = 0.5  # Constant slow rotation speed (degrees per frame)
        
        # Setup rotation timer for smooth animation
        self.rotation_timer = QTimer()
        self.rotation_timer.timeout.connect(self.update_gear_rotation)
        self.rotation_timer.setInterval(50)  # 20 FPS for smooth but not too fast rotation
        
        # Start the rotation animation
        self.rotation_timer.start()
        
        # Load and display the initial gear image
        self.update_gear_rotation()
        
        # Escape button (dev mode only)
        if Config.DEV_MODE:
            # Create escape button for development mode - completely independent styling
            self.escape_button = QPushButton("ESC", self)
            self.escape_button.setObjectName("EscapeBtn")
            self.escape_button.setFixedSize(35, 30)
            self.escape_button.move(10, 10)  # Position in top left corner
            self.escape_button.raise_()  # Ensure it's on top
            
            # Apply minimal inline styling to bypass all QSS constraints
            self.escape_button.setStyleSheet("""
                QPushButton {
                    background-color: #FF0000;
                    color: white;
                    border: 2px solid #CC0000;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 12px;
                    padding: 2px;
                    margin: 0px;
                    min-width: 35px;
                    max-width: 35px;
                    min-height: 30px;
                    max-height: 30px;
                }
                QPushButton:hover {
                    background-color: #FF3333;
                }
                QPushButton:pressed {
                    background-color: #CC0000;
                }
            """)
            
            self.escape_button.clicked.connect(self.quit_app)
        
        # Headline
        headline = QLabel("Welcome to Metrology, Motors, and More!")
        headline.setObjectName("IntroLabel")
        headline.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        lay.addWidget(headline, alignment=Qt.AlignmentFlag.AlignHCenter)


        lay.addSpacing(4)  # Reduced further to fit 4 buttons

        # Create a container for the 2x2 button grid
        button_grid_container = QWidget()
        button_grid_layout = QVBoxLayout(button_grid_container)
        button_grid_layout.setSpacing(10)  # Reduced spacing between rows
        button_grid_layout.setContentsMargins(0, 0, 0, 0)
        
        # First row of buttons (AFM and Power Pong)
        first_row = QWidget()
        first_row_layout = QHBoxLayout(first_row)
        first_row_layout.setSpacing(10)  # Spacing between buttons in the same row
        first_row_layout.setContentsMargins(0, 0, 0, 0)
        
        # primary button → AFM page
        self.afm_btn = QPushButton("Atomic Force Microscope")
        self.afm_btn.setObjectName("AfmBtn")
        first_row_layout.addWidget(self.afm_btn)
        
        # secondary → Power Pong page
        self.pwrpng_btn = QPushButton("Power Pong!")
        self.pwrpng_btn.setObjectName("PwrPngBtn")
        first_row_layout.addWidget(self.pwrpng_btn)
        
        # Add first row to button grid
        button_grid_layout.addWidget(first_row)
        
        # Second row of buttons (Haptic Feedback and Spring Dampener)
        second_row = QWidget()
        second_row_layout = QHBoxLayout(second_row)
        second_row_layout.setSpacing(10)  # Spacing between buttons in the same row
        second_row_layout.setContentsMargins(0, 0, 0, 0)
        
        # tertiary -> Haptic Feedback page
        self.haptic_btn = QPushButton("Haptic Feedback")
        self.haptic_btn.setObjectName("HapticBtn")
        second_row_layout.addWidget(self.haptic_btn)
        
        # quaternary -> Spring Dampener Tuning Page
        self.spgdmp_btn = QPushButton("Spring Dampener Tuning")
        self.spgdmp_btn.setObjectName("SpgDmpBtn")
        second_row_layout.addWidget(self.spgdmp_btn)
        
        # Add second row to button grid
        button_grid_layout.addWidget(second_row)
        
        # Add the button grid container to the main layout
        lay.addWidget(button_grid_container, alignment=Qt.AlignmentFlag.AlignHCenter)

        lay.addSpacing(8)  # Reduced final spacing
        
        lay.addStretch()
        
        # Circle overlay animation setup
        self.shrink_animation_timer = QTimer()
        self.shrink_animation_timer.timeout.connect(self.update_shrink_animation)
        self.shrink_animation_timer.setInterval(16)  # 60 FPS for smooth animation
        self.shrink_frames = 20  # 0.33 seconds
        self.shrink_frame_count = 0
        
        # Don't create overlays automatically - they will be created by specific functions
        self.yellow_circle_overlay = None
        self.blue_circle_overlay = None
        self.white_circle_overlay = None
    
    def update_gear_rotation(self):
        """Update the gear image with current rotation angle"""
        if self.original_gear_pixmap.isNull():
            return
            
        # Create a transform for rotation - using the exact same method as startup animation
        transform = QTransform()
        transform.translate(self.gear_size // 2, self.gear_size // 2)  # Move to center
        transform.rotate(self.rotation_angle)  # Apply rotation
        transform.translate(-self.gear_size // 2, -self.gear_size // 2)  # Move back
        
        # Apply the transform to create rotated gear
        rotated_gear = self.original_gear_pixmap.scaled(
            self.gear_size, self.gear_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        # Apply rotation transform
        rotated_gear = rotated_gear.transformed(transform, Qt.TransformationMode.SmoothTransformation)
        
        # Set the rotated gear to the label
        self.gear_label.setPixmap(rotated_gear)
        
        # Increment rotation angle for next frame
        self.rotation_angle += self.rotation_speed
        
        # Keep angle between 0 and 360 degrees
        self.rotation_angle = self.rotation_angle % 360
    
    def update_shrink_animation(self):
        """Update the circle shrinking animation frame by frame (works for both yellow and blue)"""
        self.shrink_frame_count += 1
        
        # Calculate progress (0.0 to 1.0)
        progress = min(self.shrink_frame_count / self.shrink_frames, 1.0)
        
        # Calculate new radius - shrink from full screen to small circle
        start_radius = 1000  # Full screen coverage (much larger than needed)
        end_radius = 25      # Small circle in center
        new_radius = int(start_radius - (start_radius - end_radius) * progress)
        
        # Update the appropriate overlay widget
        if self.yellow_circle_overlay is not None:
            self.yellow_circle_overlay.update_circle(new_radius)
        elif self.blue_circle_overlay is not None:
            self.blue_circle_overlay.update_circle(new_radius)
        elif self.white_circle_overlay is not None:
            self.white_circle_overlay.update_circle(new_radius)
        
        # Check if shrinking is complete
        if self.shrink_frame_count >= self.shrink_frames:
            self.shrink_animation_timer.stop()
            
            # Hide the appropriate overlay completely
            if self.yellow_circle_overlay is not None:
                self.yellow_circle_overlay.set_animation_state(False)
                self.yellow_circle_overlay = None
            elif self.blue_circle_overlay is not None:
                self.blue_circle_overlay.set_animation_state(False)
                self.blue_circle_overlay = None
            elif self.white_circle_overlay is not None:
                self.white_circle_overlay.set_animation_state(False)
                self.white_circle_overlay = None
    
    def start_yellow_circle_animation(self):
        """Start the yellow circle shrinking animation (called after startup animation)"""
        # Create the yellow circle overlay
        if self.main_window:
            self.yellow_circle_overlay = YellowCircleOverlay(self.main_window)
        else:
            self.yellow_circle_overlay = YellowCircleOverlay(self)
            
        self.yellow_circle_overlay.setFixedSize(800, 480)
        self.yellow_circle_overlay.move(0, 0)  # Position at top-left corner
        
        # CRITICAL: Ensure overlay is on top of everything
        self.yellow_circle_overlay.raise_()  # Raise to top
        self.yellow_circle_overlay.show()    # Show the overlay
        
        # Reset animation state and start the shrinking animation
        self.shrink_frame_count = 0
        QTimer.singleShot(100, self.shrink_animation_timer.start)  # 0.1 second delay
        
    def start_blue_circle_animation(self):
        """Start the blue circle shrinking animation (called when coming back from AFM GUI)"""
        # Create the blue circle overlay
        if self.main_window:
            self.blue_circle_overlay = BlueCircleOverlay(self.main_window)
        else:
            self.blue_circle_overlay = BlueCircleOverlay(self)
            
        self.blue_circle_overlay.setFixedSize(800, 480)
        self.blue_circle_overlay.move(0, 0)  # Position at top-left corner
        
        # CRITICAL: Ensure overlay is on top of everything
        self.blue_circle_overlay.raise_()  # Raise to top
        self.blue_circle_overlay.show()    # Show the overlay
        
        # Reset animation state and start the shrinking animation
        self.shrink_frame_count = 0
        QTimer.singleShot(100, self.shrink_animation_timer.start)  # 0.1 second delay
        
    def start_white_circle_animation(self):
        """Start the white circle shrinking animation (called when coming back from Power Pong)"""
        # Create the white circle overlay
        if self.main_window:
            self.white_circle_overlay = WhiteCircleOverlay(self.main_window)
        else:
            self.white_circle_overlay = WhiteCircleOverlay(self)
            
        self.white_circle_overlay.setFixedSize(800, 480)
        self.white_circle_overlay.move(0, 0)  # Position at top-left corner
        
        # CRITICAL: Ensure overlay is on top of everything
        self.white_circle_overlay.raise_()  # Raise to top
        self.white_circle_overlay.show()    # Show the overlay
        
        # Reset animation state and start the shrinking animation
        self.shrink_frame_count = 0
        QTimer.singleShot(100, self.shrink_animation_timer.start)  # 0.1 second delay

    
    def reposition_gear(self, x, y):
        """Reposition the gear to new coordinates at runtime"""
        self.gear_x = x
        self.gear_y = y
        self.gear_label.move(self.gear_x, self.gear_y)
    
    def quit_app(self):
        """Quit the application (called by escape button in dev mode)"""
        if self.main_window:
            self.main_window.close()
        else:
            # Fallback: quit the application directly
            from PyQt6.QtWidgets import QApplication
            QApplication.quit()





        

