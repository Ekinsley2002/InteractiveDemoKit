from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QSizePolicy
from PyQt6.QtGui import QPixmap, QPainter, QColor
from pathlib import Path
import math

class StartupAnimation(QWidget):
    animation_complete = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_animations()
        
    def setup_ui(self):
        """Setup the startup animation window"""
        # Match your main app dimensions exactly
        self.setFixedSize(800, 480)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        # Remove translucent background to ensure proper sizing
        # self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Center the window on screen
        screen = self.screen()
        if screen:
            screen_geometry = screen.geometry()
            x = (screen_geometry.width() - 800) // 2
            y = (screen_geometry.height() - 480) // 2
            self.move(x, y)
        
        # Create main layout that fills the entire window
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Ensure the main widget fills the entire window area
        self.setMinimumSize(800, 480)
        self.resize(800, 480)
        
        # Create white circular background
        self.white_circle = QLabel()
        self.white_circle.setFixedSize(210, 210)  # Size for the white circle (tiny bit smaller)
        self.white_circle.setStyleSheet("""
            background-color: white;
            border-radius: 105px;  /* Make it perfectly circular (half of new size) */
        """)
        self.white_circle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.white_circle.setAutoFillBackground(False)  # Don't let it interfere with main background
        
        # Create logo label in the center
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setMinimumSize(200, 200)
        self.logo_label.setStyleSheet("background-color: transparent;")  # Make logo label transparent
        
        # Load and scale the logo
        base_dir = Path(__file__).resolve().parent.parent
        logo_path = base_dir / "Images" / "logo.png"
        
        if logo_path.exists():
            logo_pixmap = QPixmap(str(logo_path))
            if not logo_pixmap.isNull():
                # Scale logo to desired size (adjust these values as needed)
                scaled_logo = logo_pixmap.scaled(
                    200, 200,  # Width: 200px, Height: 200px - ADJUSTABLE
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.logo_label.setPixmap(scaled_logo)
            else:
                self.logo_label.setText("Logo")
        else:
            self.logo_label.setText("Logo")
        
        # Store gear sprite paths FIRST
        self.gear_sprites = []
        for i in range(1, 13):  # 1 through 12
            gear_path = base_dir / "Animation" / "Sprites" / f"gear{i}.png"
            if gear_path.exists():
                self.gear_sprites.append(str(gear_path))
                print(f"Loaded gear sprite: {gear_path}")
            else:
                print(f"Gear sprite not found: {gear_path}")
        
        print(f"Total gear sprites loaded: {len(self.gear_sprites)}")
        
        # Animation variables
        self.current_gear_frame = 0
        self.gear_size = 640  # Size of gear sprites - ADJUSTABLE (doubled again from 320)
        
        # Create gear label that will rotate around the logo
        self.gear_label = QLabel()
        self.gear_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.gear_label.setMinimumSize(self.gear_size, self.gear_size)
        self.gear_label.setStyleSheet("background-color: transparent;")  # Make gear label transparent
        
        # Load the first gear sprite (now gear_sprites is defined)
        self.load_gear_sprite(1)
        
        # Position gear exactly in the center of the screen (on top of logo)
        # Calculate center position: window center minus half the gear size
        center_x = 800 // 2  # Window width / 2
        center_y = 480 // 2  # Window height / 2
        gear_x = center_x - self.gear_size // 2
        gear_y = center_y - self.gear_size // 2
        self.gear_label.move(gear_x, gear_y)
        
        # Add white circle and logo to center of layout
        main_layout.addStretch()
        main_layout.addWidget(self.white_circle, alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addStretch()
        
        # Add logo label as a child of the white circle so it appears on top
        self.logo_label.setParent(self.white_circle)
        self.logo_label.move(5, 5)  # Center the logo within the white circle (210-200)/2 = 5
        
        # Add gear label as a child of the main window, so it can be moved freely
        self.gear_label.setParent(self)  # This makes it a child of the main window, not the layout
        self.gear_label.raise_()  # Ensure it's on top
        
        # Make the StartupAnimation widget transparent so it shows the MainWindow's blue background
        self.setStyleSheet("background-color: transparent;")
    #002454 - BLUE
    #FAC01A - YELLOW
    
    def load_gear_sprite(self, frame_number):
        """Load a specific gear sprite frame"""
        if 1 <= frame_number <= 12 and frame_number <= len(self.gear_sprites):
            gear_pixmap = QPixmap(self.gear_sprites[frame_number - 1])
            if not gear_pixmap.isNull():
                scaled_gear = gear_pixmap.scaled(
                    self.gear_size, self.gear_size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.gear_label.setPixmap(scaled_gear)
    
    def setup_animations(self):
        """Setup the animation sequence"""
        # Fade in animation
        self.fade_in = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in.setDuration(1000)  # 1 second
        self.fade_in.setStartValue(0.0)
        self.fade_in.setEndValue(1.0)
        self.fade_in.setEasingCurve(QEasingCurve.Type.InOutCubic)
        
        # Fade out animation
        self.fade_out = QPropertyAnimation(self, b"windowOpacity")
        self.fade_out.setDuration(1000)  # 1 second
        self.fade_out.setStartValue(1.0)
        self.fade_out.setEndValue(0.0)
        self.fade_out.setEasingCurve(QEasingCurve.Type.InOutCubic)
        
        # Connect animations
        self.fade_in.finished.connect(self.start_logo_animation)
        self.fade_out.finished.connect(self.animation_finished)
        
        # Setup gear animation timer
        self.gear_animation_timer = QTimer()
        self.gear_animation_timer.timeout.connect(self.animate_gears)
        self.gear_animation_timer.setInterval(100)  # 100ms between frames (10 FPS)
    
    def start_animation(self):
        """Start the startup animation sequence"""
        # Ensure window is properly sized and positioned
        self.resize(800, 480)
        self.show()
        
        # Debug: print window dimensions
        print(f"Startup window size: {self.width()}x{self.height()}")
        print(f"Startup window geometry: {self.geometry()}")
        
        self.fade_in.start()
    
    def start_logo_animation(self):
        """Start the gear rotation animation"""
        print("Starting gear animation...")
        # Start the gear animation timer
        self.gear_animation_timer.start()
        
        # Run the animation for 3 seconds then fade out
        QTimer.singleShot(3000, self.fade_out.start)
    
    def animate_gears(self):
        """Animate the rotating gears by cycling through sprite frames"""
        # Update gear frame (cycle through 1-12)
        self.current_gear_frame = (self.current_gear_frame % 12) + 1
        self.load_gear_sprite(self.current_gear_frame)
        
        # Debug output (only print every 10 frames to avoid spam)
        if self.current_gear_frame % 10 == 0:
            print(f"Gear animation: frame {self.current_gear_frame}")
    
    def animation_finished(self):
        """Called when startup animation is complete"""
        # Stop the gear animation timer
        self.gear_animation_timer.stop()
        # Don't hide the window - just emit the signal to transition content
        self.animation_complete.emit()