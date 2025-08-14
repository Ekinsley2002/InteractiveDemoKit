
# menu_page.py  – only the top portion needs editing
from pathlib import Path                        # ← NEW
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore    import Qt, QTimer, QPointF
from PyQt6.QtGui     import QPixmap, QTransform, QPainter, QColor


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
        painter.setPen(Qt.PenStyle.NoPen)  # No outline
        painter.setBrush(QColor(250, 192, 26))  # #FAC01A - your yellow theme color
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
        painter.setPen(Qt.PenStyle.NoPen)  # No outline
        painter.setBrush(QColor(0, 36, 84))  # #002454 - your blue theme color
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
        lay.setSpacing(16)  # Reduced from 20 to save space
        lay.setContentsMargins(0, 0, 0, 0)  # Remove margins to prevent white areas
        
        # ───────── LOGO ─────────
        base_dir = Path(__file__).resolve().parent.parent     # folder where menu_page.py lives
        logo_path = base_dir / "images" / "logoBackground.png"   # works on Windows & Linux

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
        
        # ───────── ROTATING GEAR ─────────
        # Load the gear image for rotation
        gear_path = base_dir / "Animation" / "Sprites" / "gearMainMenu.png"
        if gear_path.exists():
            self.original_gear_pixmap = QPixmap(str(gear_path))
            print(f"Main menu: Loaded gear image: {gear_path}")
        else:
            print(f"Main menu: Gear image not found: {gear_path}")
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
        
        # ───────── GEAR ROTATION ANIMATION ─────────
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
        
        # ───────── HEADLINE ─────────
        headline = QLabel("Welcome to the Interactive Demo Kit!")
        headline.setObjectName("IntroLabel")
        headline.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        lay.addWidget(headline, alignment=Qt.AlignmentFlag.AlignHCenter)


        lay.addSpacing(12)  # Reduced from 18 to save space

        # primary button → AFM page
        self.afm_btn = QPushButton("Atomic Force Microscope")
        self.afm_btn.setObjectName("AfmBtn")
        lay.addWidget(self.afm_btn, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.afm_btn.clicked.connect(self.on_afm_btn_clicked)

        lay.addSpacing(10)  # Reduced from 12 to save space

        # secondary → AFM page
        self.pwrpng_btn = QPushButton("Power Pong!")
        self.pwrpng_btn.setObjectName("PwrPngBtn")
        lay.addWidget(self.pwrpng_btn, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.pwrpng_btn.clicked.connect(self.on_pwer_png_clicked)

        lay.addSpacing(10)  # Reduced from 12 to save space

        # tertiary -> Motor Fun page
        self.mtrfun_btn = QPushButton("Control and Feedback Tuning")
        self.mtrfun_btn.setObjectName("MtrFunBtn")
        lay.addWidget(self.mtrfun_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        lay.addSpacing(10)  # Reduced from 12 to save space 

        lay.addStretch()
        
        # ───────── CIRCLE OVERLAY ANIMATION SETUP ─────────
        # Setup timers and properties for circle overlays
        self.shrink_animation_timer = QTimer()
        self.shrink_animation_timer.timeout.connect(self.update_shrink_animation)
        self.shrink_animation_timer.setInterval(16)  # 60 FPS for smooth animation
        self.shrink_frames = 20  # 0.33 seconds (20 frames at 60 FPS)
        self.shrink_frame_count = 0
        
        # Don't create overlays automatically - they will be created by specific functions
        self.yellow_circle_overlay = None
        self.blue_circle_overlay = None
    
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
            print(f"Main menu: Yellow circle shrinking - radius: {new_radius}")
        elif self.blue_circle_overlay is not None:
            self.blue_circle_overlay.update_circle(new_radius)
            print(f"Main menu: Blue circle shrinking - radius: {new_radius}")
        
        # Check if shrinking is complete
        if self.shrink_frame_count >= self.shrink_frames:
            print("Main menu circle shrinking complete!")
            self.shrink_animation_timer.stop()
            
            # Hide the appropriate overlay completely
            if self.yellow_circle_overlay is not None:
                self.yellow_circle_overlay.set_animation_state(False)
                self.yellow_circle_overlay = None
            elif self.blue_circle_overlay is not None:
                self.blue_circle_overlay.set_animation_state(False)
                self.blue_circle_overlay = None
    
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
        
        print(f"Main menu: Starting with yellow circle overlay, radius: {self.yellow_circle_overlay.circle_radius}")
        print(f"Main menu: Overlay parent: {self.yellow_circle_overlay.parent()}")
        
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
        
        print(f"Main menu: Starting with blue circle overlay, radius: {self.blue_circle_overlay.circle_radius}")
        print(f"Main menu: Overlay parent: {self.blue_circle_overlay.parent()}")
        
        # Reset animation state and start the shrinking animation
        self.shrink_frame_count = 0
        QTimer.singleShot(100, self.shrink_animation_timer.start)  # 0.1 second delay

    
    def reposition_gear(self, x, y):
        """Reposition the gear to new coordinates at runtime"""
        self.gear_x = x
        self.gear_y = y
        self.gear_label.move(self.gear_x, self.gear_y)
    
    def on_afm_btn_clicked(self):
        """
        Send a single raw byte 0x01 (decimal 1 = AFM).
        """
        if self.ser.is_open:
            self.ser.write(b"\x01")      # GOOD: raw byte, not an int
            self.ser.flush()
    def on_pwer_png_clicked(self):
        """
        Send a single raw byte 0x02
        """
        if self.ser.is_open:
            self.ser.write(b"\x02")      # GOOD: raw byte, not an int
            self.ser.flush()
        

