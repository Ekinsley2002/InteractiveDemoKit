# PowerPongTransitionAnimation.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPointF
from PyQt6.QtGui import QPainter, QColor, QPixmap, QTransform
import os
import math
from pathlib import Path


class PowerPongTransitionAnimation(QWidget):
    """Power Pong transition animation with centered paddle sprite and bouncing ball"""
    
    # Signal emitted when animation completes
    animation_complete = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Set up the widget properties - match GraphingLineAnimation setup exactly
        self.setFixedSize(800, 480)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)  # CRITICAL for background to show
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        
        # Set solid blue background matching your theme
        self.setStyleSheet("background-color: #002454;")
        
        # Ball properties
        self.ball_radius = 30
        self.ball_pos = QPointF(400, 50)  # Start at top center
        self.ball_velocity = QPointF(0, 3)  # Initial downward velocity
        self.gravity = 0.2
        self.bounce_count = 0  # Track number of bounces
        self.expanding = False  # Track if ball is expanding
        
        # Paddle rotation animation properties
        self.paddle_rotation_frames = 16  # Total frames (1-16.png)
        self.current_rotation_frame = 1
        self.paddle_rotation_timer = None
        self.paddle_rotation_active = False
        
        # Paddle positioning properties
        self.paddle_start_x = 140  # Starting X position (adjust this value)
        self.paddle_start_y = 190   # Starting Y position (adjust this value)
        self.paddle_move_left_per_frame = 1  # Pixels to move left per frame (adjust this value)
        self.paddle_move_up_per_frame = 10    # Pixels to move up per frame (adjust this value)
        self.paddle_current_x = self.paddle_start_x  # Current X position during animation
        self.paddle_current_y = self.paddle_start_y  # Current Y position during animation
        
        # Simple movement system
        self.paddle_movement_step = 0  # Current movement step (0 to 15)
        
        # Debug: print initial paddle position
        print(f"Initial paddle position: X = {self.paddle_start_x}")
        
        # Create the ball as a separate widget (like the gear in MainMenuGUI)
        self.ball_label = QLabel(self)
        self.ball_label.setFixedSize(self.ball_radius * 2, self.ball_radius * 2)
        self.ball_label.setStyleSheet("""
            QLabel {
                background-color: white;
                border-radius: 30px;
                background-color: #FFFFFF;
            }
        """)
        # Position the ball initially
        self.ball_label.move(int(self.ball_pos.x() - self.ball_radius), int(self.ball_pos.y() - self.ball_radius))
        # Ensure ball is on top of everything
        self.ball_label.raise_()
        
        # Create a completely free-floating paddle (no layout constraints)
        # Create label for the paddle sprite
        self.paddle_label = QLabel(self)  # Direct parent to self, no layout
        self.paddle_label.setFixedSize(400, 400)  # Fixed size to prevent layout interference
        # No alignment - positioning is completely coordinate-based
        
        # Load and display the paddleSide.png sprite
        sprite_path = os.path.join(os.path.dirname(__file__), "Sprites", "paddleSide.png")
        if os.path.exists(sprite_path):
            pixmap = QPixmap(sprite_path)
            # Scale the pixmap to a reasonable size (adjust as needed)
            scaled_pixmap = pixmap.scaled(400, 400, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.paddle_label.setPixmap(scaled_pixmap)
        else:
            # Fallback text if image not found
            self.paddle_label.setText("PADDLE")
            self.paddle_label.setStyleSheet("""
                QLabel {
                    color: #FFFFFF;
                    font: 600 36px 'Roboto';
                    background-color: transparent;
                }
            """)
        
        # Position the paddle manually (completely free from layout)
        self.paddle_label.move(self.paddle_start_x, self.paddle_start_y)
        self.paddle_label.raise_()  # Ensure it's on top
        
        # Create a simple layout just for the ball (paddle is completely independent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Add spacing to center the ball vertically
        layout.addStretch(1)
        layout.addSpacing(75)
        
        # Animation timer for the ball physics
        self.ball_timer = QTimer()
        self.ball_timer.timeout.connect(self.update_ball)
        self.ball_timer.setInterval(16)  # 60 FPS for smooth animation
        
        # Transition timer
        self.transition_timer = QTimer()
        self.transition_timer.timeout.connect(self.complete_transition)
        self.transition_duration = 10000  # 3 seconds for testing
        
    def start_animation(self):
        """Start the Power Pong transition animation"""
        # Show the blue screen with paddle
        self.show()
        self.raise_()
        
        # Ensure the ball is properly positioned and on top
        self.ball_label.move(int(self.ball_pos.x() - self.ball_radius), int(self.ball_pos.y() - self.ball_radius))
        self.ball_label.raise_()
        
        # Start ball physics animation
        self.ball_timer.start()
        
        # Start timer to complete transition
        self.transition_timer.start(self.transition_duration)
        
    def update_ball(self):
        """Update ball position and handle collisions"""
        # If expanding, handle expansion animation
        if self.expanding:
            self.handle_expansion()
            return
            
        # Apply gravity
        self.ball_velocity.setY(self.ball_velocity.y() + self.gravity)
        
        # Update position
        self.ball_pos.setX(self.ball_pos.x() + self.ball_velocity.x())
        self.ball_pos.setY(self.ball_pos.y() + self.ball_velocity.y())
        
        # Check collision with paddle at fixed Y coordinate (simplified)
        if self.ball_pos.y() + self.ball_radius >= 380:  # Adjust this value to match paddle position
            # Increment bounce count
            self.bounce_count += 1
            
            # Check if this is the third bounce
            if self.bounce_count >= 3:
                # After third bounce, let ball complete its upward journey to center
                # Calculate velocity to reach center of screen (Y=240)
                height_to_center = 380 - 240  # Distance from paddle to center
                required_velocity = math.sqrt(2 * self.gravity * height_to_center)
                self.ball_velocity.setY(-required_velocity)
                
                # Start paddle rotation animation
                self.start_paddle_rotation()
                
                # Don't set expanding flag yet - wait until ball reaches center
                # Ensure ball doesn't get stuck below bounce point
                self.ball_pos.setY(380 - self.ball_radius)
                return
            
            # Normal bounce - calculate velocity to reach center of screen (Y=240)
            # Use physics formula: v² = 2 * g * h, where h is height difference
            height_to_center = 380 - 240  # Distance from paddle to center
            required_velocity = math.sqrt(2 * self.gravity * height_to_center)
            self.ball_velocity.setY(-required_velocity)
            # Ensure ball doesn't get stuck below bounce point
            self.ball_pos.setY(380 - self.ball_radius)
        
        # Check if ball has reached the center (peak of 3rd bounce) and should expand
        if self.bounce_count >= 3 and self.ball_pos.y() <= 240 and not self.expanding:
            # Ball has reached the center after 3rd bounce, now start expanding
            self.expanding = True
            # Ball has reached the center, stop it and start expansion
            self.ball_pos.setY(240)
            self.ball_velocity.setY(0)  # Stop the ball
            self.ball_label.move(int(self.ball_pos.x() - self.ball_radius), int(self.ball_pos.y() - self.ball_radius))
            return
        
        # Check wall collisions
        if self.ball_pos.x() - self.ball_radius <= 0 or self.ball_pos.x() + self.ball_radius >= 800:
            self.ball_velocity.setX(-self.ball_velocity.x())
        
        # Check ceiling collision
        if self.ball_pos.y() - self.ball_radius <= 0:
            self.ball_velocity.setY(abs(self.ball_velocity.y()))
            self.ball_pos.setY(self.ball_radius)
        
        # Check floor collision
        if self.ball_pos.y() + self.ball_radius >= 480:
            # Reset ball to top when it hits the floor
            self.ball_pos = QPointF(400, 50)
            self.ball_velocity = QPointF(0, 3)
        
        # Move the actual ball widget to the new position
        self.ball_label.move(int(self.ball_pos.x() - self.ball_radius), int(self.ball_pos.y() - self.ball_radius))
        
    def start_paddle_rotation(self):
        """Start the paddle rotation animation sequence (frames 1-16)"""
        # Start paddle rotation animation
        self.paddle_rotation_active = True
        self.paddle_movement_step = 0 # Reset movement step for new animation
        
        # Reset paddle position to starting coordinates
        self.paddle_current_x = self.paddle_start_x
        self.paddle_current_y = self.paddle_start_y
        self.paddle_label.move(int(self.paddle_current_x), int(self.paddle_current_y))  # Reset to starting position
        
        # Set up rotation timer for smooth animation
        self.paddle_rotation_timer = QTimer()
        self.paddle_rotation_timer.timeout.connect(self.update_paddle_rotation)
        self.paddle_rotation_timer.setInterval(16)  # 60 FPS for fast rotation
        self.paddle_rotation_timer.start()
        

        
        # Load first rotation frame
        self.load_paddle_rotation_frame(1)
        
    def load_paddle_rotation_frame(self, frame_number):
        """Load and display a specific paddle rotation frame"""
        if frame_number < 1 or frame_number > self.paddle_rotation_frames:
            return
            
        # Construct filename (1.png, 2.png, etc.)
        frame_filename = f"paddle{frame_number}.png"
        sprite_path = Path(__file__).parent / "Sprites" / frame_filename
        
        if os.path.exists(sprite_path):
            pixmap = QPixmap(str(sprite_path))
            # Scale the pixmap to the specified size
            scaled_pixmap = pixmap.scaled(400, 400, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            
            # Calculate progressive rotation: start at 0° and rotate 5.625° clockwise per frame
            # Frame 1 = 0°, Frame 2 = 5.625°, Frame 3 = 11.25°, ..., Frame 16 = 84.375°
            rotation_angle = (frame_number - 1) * 5.625  # Start from 0° for frame 1
            
            # Apply progressive rotation
            transform = QTransform()
            transform.rotate(rotation_angle)  # Positive for clockwise
            rotated_pixmap = scaled_pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)
            
            # SIMPLE MOVEMENT: Calculate new X and Y positions based on current frame
            new_x = self.paddle_start_x - ((frame_number - 1) * self.paddle_move_left_per_frame)
            new_y = self.paddle_start_y - ((frame_number - 1) * self.paddle_move_up_per_frame)
            
            # Debug: print the movement calculation
            print(f"Frame {frame_number}: X = {new_x} (moved {((frame_number - 1) * self.paddle_move_left_per_frame)} pixels left), Y = {new_y} (moved {((frame_number - 1) * self.paddle_move_up_per_frame)} pixels up)")
            
            # Update BOTH the image AND position in one go
            self.paddle_label.setPixmap(rotated_pixmap)
            self.paddle_label.move(int(new_x), int(new_y))  # Use both X and Y movement
            
            # Force immediate update
            self.paddle_label.update()
            self.paddle_label.repaint()
            
            # Store current position
            self.paddle_current_x = new_x
            self.paddle_current_y = new_y
        else:
            # Fallback text if image not found
            self.paddle_label.setText(f"[{frame_filename} not found]")
            self.paddle_label.setStyleSheet("""
                QLabel {
                    color: #FFFFFF;
                    font: 600 18px 'Roboto';
                    background-color: transparent;
                }
            """)
        
    def update_paddle_rotation(self):
        """Update the paddle rotation animation frame by frame"""
        if not self.paddle_rotation_active:
            return
            
        # Load current rotation frame
        self.load_paddle_rotation_frame(self.current_rotation_frame)
        
        # Move to next frame
        self.current_rotation_frame += 1
        
        # Check if rotation animation is complete
        if self.current_rotation_frame > self.paddle_rotation_frames:
            # Rotation complete, stop the timer
            self.paddle_rotation_timer.stop()
            self.paddle_rotation_active = False
            # Keep the last frame (16.png) visible
            self.current_rotation_frame = self.paddle_rotation_frames
        
    def update_paddle_movement(self):
        """Update the paddle's leftward movement during rotation"""
        # This function is no longer needed as movement is continuous
        pass
        
    def handle_expansion(self):
        """Handle the ball expansion animation to fill the entire page"""
        # Get current ball size
        current_size = self.ball_label.width()
        
        # Calculate expansion rate (increase size each frame)
        expansion_rate = 20  # pixels per frame
        
        # Increase ball size
        new_size = current_size + expansion_rate
        
        # Update ball size and position to keep it centered
        self.ball_label.setFixedSize(new_size, new_size)
        self.ball_label.setStyleSheet(f"""
            QLabel {{
                background-color: white;
                border-radius: {new_size//2}px;
                background-color: #FFFFFF;
            }}
        """)
        
        # Keep ball centered as it expands
        new_x = int(self.ball_pos.x() - new_size//2)
        new_y = int(self.ball_pos.y() - new_size//2)
        self.ball_label.move(new_x, new_y)
        
        # Check if ball has expanded enough to cover the entire screen
        if new_size >= 1000:  # Large enough to cover 800x480 screen
            # Ball has filled the screen, complete the transition
            self.complete_transition()
        
    def complete_transition(self):
        """Called when transition timer expires"""
        # Stop all timers
        if self.paddle_rotation_timer:
            self.paddle_rotation_timer.stop()
        self.ball_timer.stop()
        self.transition_timer.stop()
        self.animation_complete.emit()
        
    def paintEvent(self, event):
        """Custom paint event to draw the blue background"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw the blue background manually as a fallback
        painter.fillRect(self.rect(), QColor(0, 36, 84))  # #002454

