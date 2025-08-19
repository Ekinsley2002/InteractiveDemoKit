from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QSizePolicy
from PyQt6.QtGui import QPixmap, QPainter, QColor, QTransform
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
        
        # Load single gear image for rotation
        gear_path = base_dir / "Animation" / "Sprites" / "gear1.png"
        if gear_path.exists():
            self.original_gear_pixmap = QPixmap(str(gear_path))
        else:
            self.original_gear_pixmap = QPixmap()
        
        # Animation variables
        self.gear_size = 640  # Size of gear image - ADJUSTABLE
        self.rotation_angle = 0  # Current rotation angle in degrees
        
        # Create gear label that will rotate around the logo
        self.gear_label = QLabel()
        self.gear_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.gear_label.setMinimumSize(self.gear_size, self.gear_size)
        self.gear_label.setStyleSheet("background-color: transparent;")  # Make gear label transparent
        
        # Load and display the initial gear image
        self.update_gear_rotation()
        
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
    
    def update_gear_rotation(self):
        """Update the gear image with current rotation angle"""
        if self.original_gear_pixmap.isNull():
            return
            
        # Create a transform for rotation
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
    
    def paintEvent(self, event):
        """Custom paint event to draw the yellow circle overlay"""
        super().paintEvent(event)
        
        # Only draw yellow circle when it's visible
        if self.yellow_circle_visible and self.yellow_circle_radius > 0:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Set yellow color (same as your theme)
            painter.setPen(Qt.PenStyle.NoPen)  # No outline
            painter.setBrush(QColor(250, 192, 26))  # #FAC01A - your yellow theme color
            
            # Draw circle at screen center - this will be on top of everything
            center_x = 800 // 2
            center_y = 480 // 2
            painter.drawEllipse(center_x - self.yellow_circle_radius, 
                              center_y - self.yellow_circle_radius,
                              self.yellow_circle_radius * 2, 
                              self.yellow_circle_radius * 2)
    
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
        
        # Setup gear rotation animation timer
        self.gear_animation_timer = QTimer()
        self.gear_animation_timer.timeout.connect(self.animate_gear_rotation)
        self.gear_animation_timer.setInterval(16)  # 60 FPS for smooth rotation
        
        # Dynamic rotation speed control
        self.animation_phase = "start"  # start, accelerate, crescendo, decelerate
        self.animation_start_time = 0
        self.total_animation_duration = 2500  # 2.5 seconds total animation (1.5s sooner total)
        self.current_rotation_speed = 1.0  # degrees per frame (starts slow)
        self.max_rotation_speed = 8.0  # maximum speed during crescendo
        self.phase_timings = {
            "start": 0,        # 0-1s: slow start
            "accelerate": 1000, # 1-2s: gradually speed up
            "crescendo": 2000,  # 2-2.5s: maximum speed (shortened)
            "decelerate": 2000  # 2-2.5s: slow down (adjusted for 2.5s total)
        }
        
        # Gear shrinking and expansion animation properties
        self.shrinking_gear = False
        self.expanding_gear = False
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_gear_animation)
        self.animation_timer.setInterval(16)  # 60 FPS for smooth animation
        
        # Shrinking phase
        self.shrink_frames = 20  # 0.33 seconds for shrinking
        self.shrink_frame_count = 0
        
        # Expansion phase  
        self.expand_frames = 25  # 0.42 seconds for expansion
        self.expand_frame_count = 0
        
        # Store original properties
        self.original_gear_position = None
        self.original_gear_size = None
        
        # Yellow circle properties
        self.yellow_circle_visible = False
        self.yellow_circle_radius = 0
    
    def start_animation(self):
        """Start the startup animation sequence"""
        # Ensure window is properly sized and positioned
        self.resize(800, 480)
        self.show()
        

        
        self.fade_in.start()
    
    def start_logo_animation(self):
        """Start the gear rotation animation"""
        # Reset rotation angle and timing
        self.rotation_angle = 0
        self.animation_start_time = 0
        self.animation_phase = "start"
        self.current_rotation_speed = 1.0
        
        # Start the gear rotation animation timer
        self.gear_animation_timer.start()
        
        # Run the animation for 2.5 seconds then start shrinking animation (1.5 seconds sooner total)
        QTimer.singleShot(2500, self.start_gear_shrinking)
    
    def animate_gear_rotation(self):
        """Animate the gear rotation with dynamic speed control"""
        # Calculate elapsed time since animation started
        self.animation_start_time += 16  # 16ms per frame at 60 FPS
        elapsed_ms = self.animation_start_time
        
        # Determine current animation phase and adjust speed
        if elapsed_ms < self.phase_timings["accelerate"]:
            # Phase 1: Slow start (0-1s)
            self.animation_phase = "start"
            self.current_rotation_speed = 1.0
            
        elif elapsed_ms < self.phase_timings["crescendo"]:
            # Phase 2: Accelerate (1-2s)
            self.animation_phase = "accelerate"
            # Linear acceleration from 1.0 to max_speed
            progress = (elapsed_ms - self.phase_timings["accelerate"]) / 1000.0
            self.current_rotation_speed = 1.0 + (self.max_rotation_speed - 1.0) * progress
            
        elif elapsed_ms < self.phase_timings["decelerate"]:
            # Phase 3: Crescendo at maximum speed (2-3s)
            self.animation_phase = "crescendo"
            self.current_rotation_speed = self.max_rotation_speed
            
        else:
            # Phase 4: Decelerate (3-4s)
            self.animation_phase = "decelerate"
            # Linear deceleration from max_speed back to 1.0
            progress = (elapsed_ms - self.phase_timings["decelerate"]) / 1000.0
            self.current_rotation_speed = self.max_rotation_speed - (self.max_rotation_speed - 1.0) * progress
        
        # Apply the current rotation speed
        self.rotation_angle += self.current_rotation_speed
        
        # Keep angle between 0 and 360 degrees
        self.rotation_angle = self.rotation_angle % 360
        
        # Update the gear display with new rotation
        self.update_gear_rotation()
        

    
    def start_gear_shrinking(self):
        """Start the gear shrinking animation to center"""
        
        # Store original gear properties for animation
        self.original_gear_position = (self.gear_label.x(), self.gear_label.y())
        self.original_gear_size = self.gear_size
        
        # Start shrinking animation
        self.shrinking_gear = True
        self.shrink_frame_count = 0
        
        # Start the animation timer
        self.animation_timer.start()
    
    def update_gear_animation(self):
        """Update the gear shrinking and expansion animation"""
        if self.shrinking_gear:
            self.update_shrink_animation()
        elif self.expanding_gear:
            self.update_expand_animation()
    
    def update_shrink_animation(self):
        """Update the gear shrinking animation frame by frame"""
        self.shrink_frame_count += 1
        
        # Calculate progress (0.0 to 1.0)
        progress = min(self.shrink_frame_count / self.shrink_frames, 1.0)
        
        # Calculate new size - shrink to small size in center
        target_size = 50  # Small size when shrunk
        new_size = int(self.original_gear_size - (self.original_gear_size - target_size) * progress)
        
        # Calculate new position to keep gear centered on screen
        center_x = 800 // 2  # Screen center X
        center_y = 480 // 2  # Screen center Y
        new_x = center_x - new_size // 2
        new_y = center_y - new_size // 2
        
        # Update gear size and position
        self.gear_size = new_size
        self.gear_label.setFixedSize(new_size, new_size)
        self.gear_label.move(new_x, new_y)
        
        # Also shrink the logo and white circle together with the gear
        # Calculate new logo size (proportional to gear size)
        original_logo_size = 200  # Original logo size
        new_logo_size = int(original_logo_size * (new_size / self.original_gear_size))
        
        # Update logo size
        self.logo_label.setFixedSize(new_logo_size, new_logo_size)
        
        # Update white circle size (proportional to gear size)
        original_white_circle_size = 210  # Original white circle size
        new_white_circle_size = int(original_white_circle_size * (new_size / self.original_gear_size))
        self.white_circle.setFixedSize(new_white_circle_size, new_white_circle_size)
        
        # Keep logo and white circle centered with the gear
        logo_x = center_x - new_logo_size // 2
        logo_y = center_y - new_logo_size // 2
        self.logo_label.move(logo_x, logo_y)
        
        white_circle_x = center_x - new_white_circle_size // 2
        white_circle_y = center_y - new_white_circle_size // 2
        self.white_circle.move(white_circle_x, white_circle_y)
        
        # Update the gear display with current rotation
        self.update_gear_rotation()
        
        # Check if shrinking is complete
        if self.shrink_frame_count >= self.shrink_frames:
            self.shrinking_gear = False
            self.expanding_gear = True
            self.expand_frame_count = 0
            
            # Hide the gear completely
            self.gear_label.hide()
            
            # Hide the logo and white background immediately when shrinking completes
            self.logo_label.hide()
            self.white_circle.hide()
            
            # Show yellow circle at smallest point
            self.yellow_circle_visible = True
            self.yellow_circle_radius = 25  # Half of the shrunk gear size
            
            # Force a redraw to show the yellow circle
            self.update()
    
    def update_expand_animation(self):
        """Update the gear expansion animation frame by frame"""
        self.expand_frame_count += 1
        
        # Calculate progress (0.0 to 1.0)
        progress = min(self.expand_frame_count / self.expand_frames, 1.0)
        
        # Update yellow circle radius - expand to fill screen
        # Start from 25 (when shrinking finished) and expand to cover entire screen
        max_radius = 600  # Large enough to cover 800x480 screen
        self.yellow_circle_radius = int(25 + (max_radius - 25) * progress)
        
        # Force redraw to show the expanding yellow circle
        self.update()
        
        # Check if expansion is complete
        if self.expand_frame_count >= self.expand_frames:
            self.animation_timer.stop()
            self.expanding_gear = False
            # Start fade out after expansion completes
            self.fade_out.start()
    
    def animation_finished(self):
        """Called when startup animation is complete"""
        # Stop all animation timers
        self.gear_animation_timer.stop()
        if hasattr(self, 'animation_timer'):
            self.animation_timer.stop()
        # Don't hide the window - just emit the signal to transition content
        self.animation_complete.emit()