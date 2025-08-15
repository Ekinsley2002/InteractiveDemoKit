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
        
        # Add title at the top of the screen
        title_label = QLabel("Setting up the device...")
        title_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font: 600 36px 'Roboto';
                background-color: transparent;
            }
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Add spacing after title to push line drawing area down
        layout.addSpacing(40)
        
        # Add spacing to push line drawing area to upper third
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
        
        # Line drawing area - positioned in upper third of screen
        self.line_area_top = 120      # Start drawing line below the title (upper third)
        self.line_area_bottom = 200   # End drawing line in upper third
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
        
        # Wave animation properties
        self.wave_offset = 0  # Controls wave movement
        self.wave_speed = 10   # Pixels per frame for wave movement (increased from 4)
        self.wave_amplitude = 25  # Height of the wave peaks/troughs (increased from 15)
        self.wave_frequency = 0.02  # How many waves per pixel (controls wave density)
        self.wave_bottom_y = 450   # Y position for the bottom of the wave
        self.wave_color = QColor(255, 255, 255)  # White color for the wave
        
        # Probe animation properties
        self.probe_image = None
        self.probe_rotation_angle = 150  # Current rotation angle in degrees (start 30 degrees lower)
        self.probe_rotation_speed = 2.0  # Degrees per frame for smooth rotation
        self.probe_center_x = 225  # X position of the probe center (gimbal point)
        self.probe_center_y = 340  # Y position of the probe center (gimbal point) - moved higher
        self.probe_scale = 0.42  # Scale factor for the probe image (reduced by 30% from 0.6)
        self.needle_tip_offset_x = 160  # X offset from probe center to needle tip (negative = left)
        self.needle_tip_offset_y = 62    # Y offset from probe center to needle tip
        self.gimbal_hole_offset_x = -120  # X offset from probe center to gimbal hole (rotation point)
        self.gimbal_hole_offset_y = 0    # Y offset from probe center to gimbal hole (rotation point)
        
        # Probe physics properties
        self.probe_touching_wave = False  # Whether probe tip is touching the wave
        self.probe_rotation_direction = 1  # 1 for clockwise, -1 for counterclockwise
        self.probe_force = 0.0  # Force applied by probe to wave surface
        self.probe_spring_constant = 0.4  # How much the probe resists being pushed up
        self.probe_damping = .2  # Damping factor to prevent excessive bouncing
        
        # Debug mode for visualization
        self.debug_mode = False  # Set to True to see probe tip and wave contact points
    
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
        
        # Initialize wave animation
        self.wave_offset = 0
        
        # Reset probe physics state
        self.probe_touching_wave = False
        self.probe_rotation_angle = 0
        self.probe_force = 0.0
        
        # Load and initialize probe image
        self.load_probe_image()
        
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
        
        # Update wave animation
        self.update_wave_animation()
        
        # Update probe rotation
        self.update_probe_rotation()
        
    def generate_wave_points(self):
        """Generate points for the moving wave at the bottom of the screen"""
        wave_points = []
        
        # Generate wave points across the entire width of the screen
        for x in range(0, 801, 2):  # Step by 2 pixels for smooth wave
            # Calculate wave Y position using sine function
            wave_y = self.wave_bottom_y + self.wave_amplitude * math.sin(
                self.wave_frequency * (x + self.wave_offset)
            )
            wave_points.append(QPointF(x, wave_y))
        
        return wave_points
        
    def update_wave_animation(self):
        """Update the wave animation by moving the wave offset"""
        # Normalize wave movement to be consistent regardless of frame rate
        # Main animation runs at 20 FPS (50ms), expand animation runs at 60 FPS (16ms)
        if hasattr(self, 'expanding_circle') and self.expanding_circle:
            # During expansion, normalize to 20 FPS equivalent
            frame_rate_factor = 16.0 / 50.0  # 16ms / 50ms = 0.32
            normalized_speed = self.wave_speed * frame_rate_factor
        else:
            # During main animation, use normal speed
            normalized_speed = self.wave_speed
        
        self.wave_offset += normalized_speed
        
        # Reset offset when wave has moved far enough to create seamless loop
        if self.wave_offset > 2 * math.pi / self.wave_frequency:
            self.wave_offset = 0
        
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
        
        # Update wave animation during expansion
        self.update_wave_animation()
        
        # Update probe rotation during expansion
        self.update_probe_rotation()
        
        # Check if expansion is complete
        if self.expand_frame_count >= self.expand_frames:
            self.expand_animation_timer.stop()
            self.on_animation_complete()
        
    def paintEvent(self, event):
        """Custom paint event to draw the animated line, expanding circle, and moving wave"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw the moving wave at the bottom (always visible)
        self.draw_wave(painter)
        
        # Draw the rotating probe
        self.draw_probe(painter)
        
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
    
    def draw_wave(self, painter):
        """Draw the moving wave at the bottom of the screen"""
        # Set wave pen and brush
        wave_pen = QPen(self.wave_color, 3, Qt.PenStyle.SolidLine)
        painter.setPen(wave_pen)
        painter.setBrush(self.wave_color)
        
        # Generate wave points
        wave_points = self.generate_wave_points()
        
        # Create a path for the wave
        if wave_points:
            path = QPainterPath()
            path.moveTo(wave_points[0])
            
            # Draw the wave line
            for point in wave_points[1:]:
                path.lineTo(point)
            
            # Complete the wave shape by adding bottom corners and closing the path
            # Add bottom-right corner
            path.lineTo(800, 480)
            # Add bottom-left corner
            path.lineTo(0, 480)
            # Close the path back to the first wave point
            path.lineTo(wave_points[0])
            
            # Fill the wave area with a solid white color
            painter.setBrush(QColor(255, 255, 255))  # Solid white fill
            painter.drawPath(path)
            
            # Draw the wave outline
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(path)
    
    def draw_probe(self, painter):
        """Draw the rotating probe with needle tip positioned on the wave surface"""
        if not self.probe_image or self.probe_image.isNull():
            return
        
        # Use fixed probe position - probe stays in place
        probe_center_x = self.probe_center_x
        probe_center_y = self.probe_center_y
        
        # Calculate the gimbal hole position (actual rotation center)
        gimbal_hole_x = probe_center_x + self.gimbal_hole_offset_x
        gimbal_hole_y = probe_center_y + self.gimbal_hole_offset_y
        
        # Save the current painter state
        painter.save()
        
        # Move to gimbal hole and apply rotation
        painter.translate(gimbal_hole_x, gimbal_hole_y)
        painter.rotate(self.probe_rotation_angle)
        
        # Scale the probe image
        scaled_probe = self.probe_image.scaled(
            int(self.probe_image.width() * self.probe_scale),
            int(self.probe_image.height() * self.probe_scale),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        # Draw the probe with offset so gimbal hole is at rotation center
        painter.drawPixmap(
            -scaled_probe.width() // 2 - self.gimbal_hole_offset_x,
            -scaled_probe.height() // 2 - self.gimbal_hole_offset_y,
            scaled_probe
        )
        
        # Restore the painter state
        painter.restore()
        
        # Debug visualization - draw probe tip position and wave contact point
        if hasattr(self, 'debug_mode') and self.debug_mode:
            # Draw probe tip position
            tip_x, tip_y = self.calculate_probe_tip_position()
            painter.setPen(QPen(QColor(255, 0, 0), 3))  # Red pen
            painter.setBrush(QColor(255, 0, 0))
            painter.drawEllipse(QPointF(tip_x, tip_y), 5, 5)
            
            # Draw wave contact point
            wave_y_at_tip = self.get_wave_y_at_x(tip_x)
            painter.setPen(QPen(QColor(0, 255, 0), 3))  # Green pen
            painter.setBrush(QColor(0, 255, 0))
            painter.drawEllipse(QPointF(tip_x, wave_y_at_tip), 5, 5)
            
            # Draw line between tip and wave
            painter.setPen(QPen(QColor(255, 255, 0), 2))  # Yellow line
            painter.drawLine(int(tip_x), int(tip_y), int(tip_x), int(wave_y_at_tip))
    
    def get_wave_y_at_x(self, x):
        """Get the wave Y position at a specific X coordinate"""
        # Use the same wave calculation as generate_wave_points
        wave_y = self.wave_bottom_y + self.wave_amplitude * math.sin(
            self.wave_frequency * (x + self.wave_offset)
        )
        return wave_y
    
    def on_animation_complete(self):
        """Called when animation completes"""
        self.animation_timer.stop()
        self.animation_complete.emit()
    
    def stop_animation(self):
        """Stop the animation"""
        self.animation_timer.stop()
        if hasattr(self, 'expand_animation_timer'):
            self.expand_animation_timer.stop()
    
    def load_probe_image(self):
        """Load the probe image from the sprites folder"""
        try:
            from pathlib import Path
            base_dir = Path(__file__).resolve().parent
            probe_path = Path("Animation/Sprites/probe.png")
            
            if probe_path.exists():
                from PyQt6.QtGui import QPixmap
                self.probe_image = QPixmap(str(probe_path))
                print(f"Probe image loaded successfully: {probe_path}")
            else:
                print(f"Probe image not found: {probe_path}")
                self.probe_image = None
        except Exception as e:
            print(f"Error loading probe image: {e}")
            self.probe_image = None
    
    def update_probe_rotation(self):
        """Update the probe rotation animation with force-based physics"""
        if not self.probe_touching_wave:
            # Probe is not touching wave yet - rotate clockwise until it hits
            self.probe_rotation_angle += self.probe_rotation_speed
            
            # Calculate the actual probe tip position based on current rotation
            tip_x, tip_y = self.calculate_probe_tip_position()
            
            # Get the wave Y position at the tip's X coordinate
            wave_y_at_tip = self.get_wave_y_at_x(tip_x)
            
            # Check if the probe tip is close enough to the wave surface
            distance_to_wave = abs(tip_y - wave_y_at_tip)
            
            if distance_to_wave < 10:  # Within 10 pixels of wave surface
                self.probe_touching_wave = True
                print(f"Probe touched wave! Distance: {distance_to_wave:.1f}")
                # Initialize force when contact is made
                self.probe_force = 0.0
        else:
            # Probe is touching wave - implement force-based interaction
            
            # Get current tip position
            tip_x, tip_y = self.calculate_probe_tip_position()
            wave_y_at_tip = self.get_wave_y_at_x(tip_x)
            
            # Calculate penetration depth (how much probe is "pushing into" the wave)
            penetration = wave_y_at_tip - tip_y
            
            # Apply spring force (probe pushes back against wave)
            spring_force = penetration * self.probe_spring_constant
            
            # Apply damping to prevent excessive bouncing
            self.probe_force = self.probe_force * self.probe_damping + spring_force
            
            # Determine rotation direction based on wave movement
            # Look ahead to see if wave is going up or down
            ahead_x = tip_x + 5
            ahead_wave_y = self.get_wave_y_at_x(ahead_x)
            
            if ahead_wave_y < wave_y_at_tip:
                # Wave is going up - rotate counterclockwise
                self.probe_rotation_direction = -1
            elif ahead_wave_y > wave_y_at_tip:
                # Wave is going down - rotate clockwise
                self.probe_rotation_direction = 1
            
            # Apply rotation with force influence
            # The force affects how much the probe can resist being pushed up
            force_factor = max(0.1, 1.0 - abs(self.probe_force) * 0.01)
            
            # Apply rotation in the determined direction
            rotation_amount = self.probe_rotation_speed * self.probe_rotation_direction * force_factor
            self.probe_rotation_angle += rotation_amount
            
            # Apply wave push-back effect
            # If wave is pushing up strongly, it can influence the rotation
            if abs(penetration) > 5:  # Significant penetration
                # Wave can push the rotation up
                wave_push_angle = penetration * 0.1  # Convert penetration to rotation
                self.probe_rotation_angle += wave_push_angle
            
            # Proactive surface constraint: Check and correct before applying wave push-back
            # This prevents the probe from flying off the surface
            current_tip_x, current_tip_y = self.calculate_probe_tip_position()
            current_wave_y = self.get_wave_y_at_x(current_tip_x)
            
            # If tip is already below surface, apply immediate correction
            if current_tip_y > current_wave_y:
                # Immediate correction to bring tip back to surface
                immediate_adjustment = 3.0
                if self.probe_rotation_direction > 0:
                    self.probe_rotation_angle -= immediate_adjustment
                else:
                    self.probe_rotation_angle += immediate_adjustment
            
            # Constraint: Prevent probe tip from going below wave surface
            # Check if tip would go below wave after rotation
            constrained_tip_x, constrained_tip_y = self.calculate_probe_tip_position()
            wave_y_at_constrained_tip = self.get_wave_y_at_x(constrained_tip_x)
            
            # If tip is below wave, apply more aggressive correction
            if constrained_tip_y > wave_y_at_constrained_tip:
                # Calculate penetration depth
                penetration_depth = constrained_tip_y - wave_y_at_constrained_tip
                
                # Use more aggressive adjustment for deeper penetration
                if penetration_depth > 5:
                    # Deep penetration - use stronger correction
                    adjustment_angle = 4.0
                elif penetration_depth > 2:
                    # Medium penetration - use moderate correction
                    adjustment_angle = 2.5
                else:
                    # Light penetration - use gentle correction
                    adjustment_angle = 1.5
                
                # Determine which direction to rotate to bring tip up
                # This depends on the current probe orientation
                if self.probe_rotation_direction > 0:
                    # Currently rotating clockwise, adjust counterclockwise to bring tip up
                    self.probe_rotation_angle -= adjustment_angle
                else:
                    # Currently rotating counterclockwise, adjust clockwise to bring tip up
                    self.probe_rotation_angle += adjustment_angle
                
                # Additional constraint: If tip is significantly below surface, apply immediate strong correction
                if penetration_depth > 8:
                    # Very deep penetration - apply immediate strong correction
                    strong_adjustment = 6.0
                    if self.probe_rotation_direction > 0:
                        self.probe_rotation_angle -= strong_adjustment
                    else:
                        self.probe_rotation_angle += strong_adjustment
        
        # Keep angle between 0 and 360 degrees
        self.probe_rotation_angle = self.probe_rotation_angle % 360

    def calculate_probe_tip_position(self):
        """Calculate the actual position of the probe tip after rotation"""
        # The probe tip position is determined by rotating around the gimbal hole
        
        # First, calculate the gimbal hole position (rotation center)
        gimbal_hole_x = self.probe_center_x + self.gimbal_hole_offset_x
        gimbal_hole_y = self.probe_center_y + self.gimbal_hole_offset_y
        
        # Calculate the probe tip position relative to the gimbal hole
        # The tip is offset from the probe center, and the probe center is offset from the gimbal hole
        relative_tip_x = self.needle_tip_offset_x - self.gimbal_hole_offset_x
        relative_tip_y = self.needle_tip_offset_y - self.gimbal_hole_offset_y
        
        # Apply rotation to the relative tip position
        angle_rad = math.radians(self.probe_rotation_angle)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        
        # Rotate the relative tip position
        rotated_tip_x = relative_tip_x * cos_a - relative_tip_y * sin_a
        rotated_tip_y = relative_tip_x * sin_a + relative_tip_y * cos_a
        
        # Add the gimbal hole position to get the absolute tip position
        absolute_tip_x = gimbal_hole_x + rotated_tip_x
        absolute_tip_y = gimbal_hole_y + rotated_tip_y
        
        return absolute_tip_x, absolute_tip_y
