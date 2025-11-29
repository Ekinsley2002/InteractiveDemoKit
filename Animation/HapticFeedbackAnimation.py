from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPointF, QElapsedTimer
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QPainter, QColor, QPen
import random
import math

class HapticFeedbackAnimation(QWidget):
    """Haptic Feedback loading animation with blue background and ripple effects"""
    
    # Signal emitted when animation completes
    animation_complete = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Set up the widget properties
        self.setFixedSize(800, 480)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        
        # Set solid blue background matching your theme
        self.setStyleSheet("background-color: #002454;")
        
        # Create main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Add title at the top
        title_label = QLabel("Preparing Haptic System...")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font: 600 36px 'Roboto';
                background-color: transparent;
                margin: 60px 0px 40px 0px;
            }
        """)
        layout.addWidget(title_label)
        
        # Animation properties
        self.animation_duration = 4000  # 4 seconds in milliseconds
        
        # Ripple tracking
        self.ripples = []  # List of ripple dictionaries: {center: QPointF, start_time: int, radius: float, opacity: float, color: QColor}
        self.elapsed_timer = QElapsedTimer()
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_timer.setInterval(16)  # ~60 FPS
        
        # Screen center for final ripple
        self.screen_center = QPointF(400, 240)
        self.screen_size = math.sqrt(800**2 + 480**2)  # Diagonal for full coverage
        
        # Color definitions
        self.white_color = QColor(255, 255, 255)  # White
        self.yellow_color = QColor(250, 192, 26)    # #FAC01A - theme yellow
        
    def start_animation(self):
        """Start the Haptic Feedback loading animation"""
        # Reset state
        self.ripples = []
        self.elapsed_timer.restart()
        
        # Show the animation
        self.show()
        self.raise_()
        
        # Start animation timer
        self.animation_timer.start()
        
        # Spawn first 3 ripples at random positions (0s, 1s, 2s)
        QTimer.singleShot(0, lambda: self.spawn_random_ripple(0))
        QTimer.singleShot(1000, lambda: self.spawn_random_ripple(1000))
        QTimer.singleShot(2000, lambda: self.spawn_random_ripple(2000))
        
        # Spawn final center ripple at 3s
        QTimer.singleShot(3000, lambda: self.spawn_center_ripple())
        
        # Set up completion timer
        QTimer.singleShot(self.animation_duration, self.complete_animation)
    
    def spawn_random_ripple(self, start_time):
        """Spawn a ripple at a random position on screen"""
        # Random position with some margin from edges
        margin = 100
        x = random.uniform(margin, 800 - margin)
        y = random.uniform(margin, 480 - margin)
        
        # 1/3 chance for yellow, 2/3 chance for white
        is_yellow = random.random() < (1.0 / 3.0)
        ripple_color = self.yellow_color if is_yellow else self.white_color
        
        ripple = {
            'center': QPointF(x, y),
            'start_time': start_time,  # 0, 1000, 2000
            'radius': 0,
            'opacity': 1.0,
            'color': ripple_color
        }
        self.ripples.append(ripple)
    
    def spawn_center_ripple(self):
        """Spawn the final ripple at the center of the screen"""
        ripple = {
            'center': self.screen_center,
            'start_time': 3000,  # Starts at 3 seconds
            'radius': 0,
            'opacity': 1.0,
            'color': self.white_color  # Final ripple is always white
        }
        self.ripples.append(ripple)
    
    def update_animation(self):
        """Update the ripple animations"""
        current_time = self.elapsed_timer.elapsed()  # Get elapsed time in milliseconds
        
        # Update each ripple
        for ripple in self.ripples:
            elapsed = current_time - ripple['start_time']
            
            if elapsed < 0:
                continue  # Ripple hasn't started yet
            
            # For first 3 ripples: expand and fade out over 1 second
            if ripple['center'] != self.screen_center:
                max_radius = 200  # Maximum radius for random ripples
                ripple_duration = 1000  # 1 second
                
                if elapsed < ripple_duration:
                    progress = elapsed / ripple_duration
                    ripple['radius'] = progress * max_radius
                    ripple['opacity'] = 1.0 - progress  # Fade out
                else:
                    ripple['opacity'] = 0  # Fully faded
            else:
                # Final center ripple: expand to cover screen over 1 second
                ripple_duration = 1000  # 1 second to expand
                
                if elapsed < ripple_duration:
                    progress = elapsed / ripple_duration
                    ripple['radius'] = progress * self.screen_size
                    ripple['opacity'] = 1.0  # Stay fully opaque
                else:
                    ripple['radius'] = self.screen_size  # Full coverage
                    ripple['opacity'] = 1.0
        
        # Trigger redraw
        self.update()
    
    def paintEvent(self, event):
        """Draw the ripples with multiple concentric rings"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw each ripple
        for ripple in self.ripples:
            if ripple['opacity'] <= 0 or ripple['radius'] <= 0:
                continue
            
            center = ripple['center']
            radius = ripple['radius']
            is_center_ripple = (center == self.screen_center)
            
            if is_center_ripple:
                # Final center ripple: solid white circle (no outline)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(255, 255, 255))  # Solid white
                painter.drawEllipse(
                    int(center.x() - radius),
                    int(center.y() - radius),
                    int(radius * 2),
                    int(radius * 2)
                )
            else:
                # First 3 ripples: multiple concentric rings with fading effect
                # Get the ripple's color (yellow or white)
                ripple_color = ripple.get('color', self.white_color)
                
                num_rings = 4  # Number of concentric rings
                ring_spacing = radius / num_rings  # Space between rings
                
                for ring in range(num_rings):
                    # Calculate ring radius (smaller rings are further from center)
                    ring_radius = radius - (ring * ring_spacing)
                    
                    if ring_radius <= 0:
                        continue
                    
                    # Calculate opacity - outer rings are more transparent
                    # Base opacity decreases with distance from center
                    ring_opacity = ripple['opacity'] * (1.0 - (ring * 0.25))
                    ring_opacity = max(0, ring_opacity)  # Clamp to 0
                    
                    if ring_opacity <= 0:
                        continue
                    
                    # Vary pen width - outer rings are thinner
                    pen_width = max(2, int(4 - (ring * 0.5)))
                    
                    # Set pen with varying opacity using the ripple's color
                    pen_color = QColor(ripple_color.red(), ripple_color.green(), ripple_color.blue(), int(255 * ring_opacity))
                    pen = QPen(pen_color)
                    pen.setWidth(pen_width)
                    painter.setPen(pen)
                    
                    # No fill for rings, just outlines
                    painter.setBrush(Qt.BrushStyle.NoBrush)
                    
                    # Draw the ring
                    painter.drawEllipse(
                        int(center.x() - ring_radius),
                        int(center.y() - ring_radius),
                        int(ring_radius * 2),
                        int(ring_radius * 2)
                    )
                
                # Add a subtle inner glow effect
                if radius > 20:
                    glow_radius = min(radius * 0.3, 30)
                    glow_opacity = ripple['opacity'] * 0.4
                    
                    # Use the ripple's color for the glow
                    glow_pen_color = QColor(ripple_color.red(), ripple_color.green(), ripple_color.blue(), int(255 * glow_opacity))
                    glow_brush_color = QColor(ripple_color.red(), ripple_color.green(), ripple_color.blue(), int(255 * glow_opacity * 0.2))
                    
                    pen = QPen(glow_pen_color)
                    pen.setWidth(1)
                    painter.setPen(pen)
                    painter.setBrush(glow_brush_color)
                    
                    painter.drawEllipse(
                        int(center.x() - glow_radius),
                        int(center.y() - glow_radius),
                        int(glow_radius * 2),
                        int(glow_radius * 2)
                    )
    
    def complete_animation(self):
        """Called when animation completes"""
        # Stop animation timer
        self.animation_timer.stop()
        
        # Emit completion signal
        self.animation_complete.emit()
    
    def stop_animation(self):
        """Stop the animation"""
        self.animation_timer.stop()
