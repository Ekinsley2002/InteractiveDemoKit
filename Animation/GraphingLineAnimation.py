# GraphingLineAnimation.py
import random
import math
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve, QPointF
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QPainter, QPen, QColor, QPainterPath


class GraphingLineAnimation(QWidget):
    """
    Animation that shows a jagged black line moving from left to right across the screen,
    simulating real-time graphing on a blue background.
    """
    
    animation_complete = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Set up the widget
        self.setFixedSize(800, 480)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background-color: #002454;")
        
        # Create layout for any text content
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Add spacing to push title lower on screen
        layout.addStretch(1)
        
        # Add title - positioned lower on screen
        title_label = QLabel("Setting up the device...")
        title_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font: 600 28px 'Roboto';
                background-color: transparent;
            }
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Add spacing to push line drawing area to bottom
        layout.addStretch(1)
        
        # Animation properties
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_timer.setInterval(50)  # 20 FPS for smooth animation
        
        # Line drawing properties
        self.line_points = []
        self.current_x = 0
        self.line_speed = 15  # pixels per frame - much faster!
        self.max_points = 800 // self.line_speed  # How many points to store
        
        # Line style
        self.line_pen = QPen(QColor(255, 255, 255), 6, Qt.PenStyle.SolidLine)  # White, 6px thick
        
        # Animation state - no fixed duration, ends when line reaches right edge
        self.elapsed_time = 0
        
        # Trend control for smoother movement
        self.trend_direction = 1  # 1 for up, -1 for down
        self.trend_counter = 0  # How long to maintain current trend
        self.trend_duration = random.randint(30, 80)  # Frames to maintain trend
        
        # Line drawing area - positioned in lower portion of screen
        self.line_area_top = 300      # Start drawing line below the text
        self.line_area_bottom = 450   # Leave some margin at bottom
        self.line_area_center = (self.line_area_top + self.line_area_bottom) // 2
        
        # Expanding circle animation properties
        self.expanding_circle = False
        self.circle_radius = 0
        self.circle_center = QPointF(0, 0)
        self.expand_animation_timer = QTimer()
        self.expand_animation_timer.timeout.connect(self.update_expand_animation)
        self.expand_animation_timer.setInterval(16)  # 60 FPS for smooth expansion
        self.expand_duration = 1000  # 1 second in milliseconds
        self.expand_start_time = 0
        self.expand_frames = 35  # Medium speed: 35 frames (0.58 seconds)
        
    def start_animation(self):
        """Start the graphing line animation"""
        # Initialize line starting point in the lower line drawing area
        start_y = random.randint(self.line_area_top, self.line_area_bottom)
        self.line_points = [QPointF(0, start_y)]
        self.current_x = 0
        self.elapsed_time = 0
        
        # Initialize trend system
        self.trend_direction = random.choice([1, -1])  # Random starting direction
        self.trend_counter = 0
        self.trend_duration = random.randint(30, 80)  # Frames to maintain trend
        
        # Start the animation timer
        self.animation_timer.start()
        
    def update_animation(self):
        """Update the animation frame by frame"""
        self.elapsed_time += 50  # 50ms per frame
        
        # Move the line to the right
        self.current_x += self.line_speed
        
        # Check if line has reached the right edge of the screen
        if self.current_x >= 800:
            # Start expanding circle animation
            self.start_expanding_circle()
            return
        
        # Generate new Y position with smooth, gradual trends
        if len(self.line_points) > 0:
            last_y = self.line_points[-1].y()
            
            # Update trend counter
            self.trend_counter += 1
            
            # Check if we should change trend direction
            if self.trend_counter >= self.trend_duration:
                # Change direction and set new duration
                self.trend_direction *= -1  # Reverse direction
                self.trend_counter = 0
                self.trend_duration = random.randint(30, 80)  # New trend duration
            
            # Create smooth, gradual movement
            # Base trend movement (gradual up or down)
            trend_movement = self.trend_direction * 0.8  # Smooth movement per frame
            
            # Small amount of noise for realism (much less than before)
            noise = random.randint(-3, 3)  # Very small noise
            
            # Slight pull toward center of line drawing area
            center_pull = (self.line_area_center - last_y) * 0.02
            
            # Calculate new Y position
            new_y = last_y + trend_movement + noise + center_pull
            
            # Keep Y within the line drawing area bounds
            new_y = max(self.line_area_top, min(self.line_area_bottom, new_y))
            
            # Add new point
            new_point = QPointF(self.current_x, new_y)
            self.line_points.append(new_point)
            
            # Remove old points to keep memory usage low
            if len(self.line_points) > self.max_points:
                self.line_points.pop(0)
        
        # Trigger redraw
        self.update()
        
    def start_expanding_circle(self):
        """Start the expanding circle animation when line reaches right edge"""
        # Stop the line animation timer
        self.animation_timer.stop()
        
        # Set up expanding circle animation
        self.expanding_circle = True
        self.circle_center = QPointF(800, self.line_points[-1].y())  # End point of line
        self.circle_radius = 0
        self.expand_start_time = self.elapsed_time
        self.expand_frame_count = 0  # Initialize frame counter
        
        # Start the expansion animation timer
        self.expand_animation_timer.start()
        
    def update_expand_animation(self):
        """Update the expanding circle animation"""
        # Use a separate timer-based approach instead of relying on elapsed_time
        if not hasattr(self, 'expand_frame_count'):
            self.expand_frame_count = 0
        
        self.expand_frame_count += 1
        
        # Calculate progress based on frame count (20 frames for fast expansion)
        progress = min(self.expand_frame_count / self.expand_frames, 1.0)
        
        # Calculate radius based on progress
        # We need the circle to expand to cover the entire screen
        # The diagonal distance from any corner to center is sqrt(800² + 480²) ≈ 933 pixels
        max_radius = 933
        self.circle_radius = progress * max_radius
        
        # Trigger redraw
        self.update()
        
        # Check if expansion is complete
        if self.expand_frame_count >= self.expand_frames:
            self.expand_animation_timer.stop()
            self.on_animation_complete()
        
    def paintEvent(self, event):
        """Custom paint event to draw the animated line and expanding circle"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw the line if we have enough points and not expanding
        if len(self.line_points) > 1 and not self.expanding_circle:
            # Set the line pen
            painter.setPen(self.line_pen)
            
            # Create a path for smooth line drawing
            path = QPainterPath()
            path.moveTo(self.line_points[0])
            
            for point in self.line_points[1:]:
                path.lineTo(point)
            
            painter.drawPath(path)
            
            # Draw a circle at the current end point for visual effect
            if self.line_points:
                current_point = self.line_points[-1]
                painter.setBrush(QColor(255, 255, 255))  # White brush
                painter.drawEllipse(current_point, 4, 4)  # Slightly larger circle
        
        # Draw expanding circle if animation is active
        if self.expanding_circle:
            painter.setPen(Qt.PenStyle.NoPen)  # No outline
            painter.setBrush(QColor(255, 255, 255))  # White fill
            painter.drawEllipse(self.circle_center, self.circle_radius, self.circle_radius)
    
    def on_animation_complete(self):
        """Called when animation completes"""
        self.animation_timer.stop()
        self.animation_complete.emit()
    
    def stop_animation(self):
        """Stop the animation"""
        self.animation_timer.stop()
        if hasattr(self, 'expand_animation_timer'):
            self.expand_animation_timer.stop()
