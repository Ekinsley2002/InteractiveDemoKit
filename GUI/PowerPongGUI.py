from pathlib import Path
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore    import Qt, QSize, pyqtSignal, QTimer, QPointF
from PyQt6.QtGui     import QIcon, QCursor, QPainter, QColor, QPen

PROJECT_ROOT = Path(__file__).resolve().parent.parent
IMAGES_DIR   = Path("Images")
STYLES_DIR   = PROJECT_ROOT / "Styles"


class Picker(QWidget):
    """One vertical picker column with ▲ / ▼ / Add."""
    value_added = pyqtSignal(int)          # emits the *current* value

    COL_W = 200

    def __init__(self, title: str, increment: int = 1, parent: QWidget | None = None):
        super().__init__(parent)
        self._value = 0
        self._increment = increment

        v = QVBoxLayout(self)
        v.setSpacing(12)
        v.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        title_lbl = QLabel(title, alignment=Qt.AlignmentFlag.AlignCenter)
        title_lbl.setObjectName("PickerTitle")
        title_lbl.setFixedWidth(self.COL_W)

        self.value_lbl = QLabel("0", alignment=Qt.AlignmentFlag.AlignCenter)
        self.value_lbl.setObjectName("ValueDisplay")
        self.value_lbl.setFixedSize(self.COL_W, 64)

        up_btn   = self._make_arrow("arrow_up.png",   +1)
        down_btn = self._make_arrow("arrow_down.png", -1)

        add_btn  = QPushButton("Add")
        add_btn.setObjectName("AddBtn")
        add_btn.setFixedSize(120, 44)
        add_btn.clicked.connect(self._emit_add)

        v.addWidget(title_lbl)
        v.addWidget(up_btn)
        v.addWidget(self.value_lbl)
        v.addWidget(down_btn)
        v.addStretch(1)
        v.addWidget(add_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

    def _make_arrow(self, filename: str, delta: int) -> QPushButton:
        path = IMAGES_DIR / filename
        btn  = QPushButton()
        btn.setObjectName("ArrowBtn")
        btn.setIcon(QIcon(str(path)))
        btn.setIconSize(QSize(40, 40))
        btn.setFixedSize(self.COL_W, 64)
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.clicked.connect(lambda: self._bump(delta))
        return btn

    def _bump(self, delta: int):
        new_value = self._value + (delta * self._increment)
        if 0 <= new_value <= 50:
            self._value = new_value
            self.value_lbl.setText(str(self._value))

    def _emit_add(self):
        self.value_added.emit(self._value)


class CircleOverlay(QWidget):
    """Separate overlay widget for the shrinking circle animation"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        
        # Animation properties
        self.circle_radius = 933  # Start with full screen coverage
        self.circle_center = QPointF(400, 240)  # Center of screen
        self.shrinking_circle = True
        
        # Set a solid background to ensure visibility
        self.setStyleSheet("background-color: white;")
        
    def update_circle(self, radius):
        """Update the circle radius for animation"""
        self.circle_radius = radius
        self.update()
        
    def set_animation_state(self, active):
        """Set whether the animation is active"""
        self.shrinking_circle = active
        self.update()
        
    def paintEvent(self, event):
        """Draw the shrinking white circle overlay"""
        if not self.shrinking_circle:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw white circle that covers the screen and shrinks
        painter.setPen(Qt.PenStyle.NoPen)  # No outline
        painter.setBrush(QColor(255, 255, 255))  # White fill
        painter.drawEllipse(self.circle_center, self.circle_radius, self.circle_radius)


class WhiteTransitionOverlay(QWidget):
    """Overlay widget for the white transition when going back to main menu"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        
        # Animation properties
        self.circle_radius = 0  # Start with no coverage
        self.circle_center = QPointF(400, 240)  # Center of screen
        self.expanding_circle = False
        
        # Set transparent background
        self.setStyleSheet("background-color: transparent;")
        
    def update_circle(self, radius):
        """Update the circle radius for animation"""
        self.circle_radius = radius
        self.update()
        
    def set_animation_state(self, active):
        """Set whether the animation is active"""
        self.expanding_circle = active
        self.update()
        
    def paintEvent(self, event):
        """Draw the expanding white circle overlay"""
        if not self.expanding_circle:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw white circle that expands to fill the screen
        painter.setPen(Qt.PenStyle.NoPen)  # No outline
        painter.setBrush(QColor(255, 255, 255))  # White fill
        painter.drawEllipse(self.circle_center, self.circle_radius, self.circle_radius)


class PowerPongPageWidget(QWidget):
    """
    Shows the Power-Pong controls and forwards user actions to the Arduino
    via SimpleFOC Commander.

    Parameters
    ----------
    ser : serial.Serial-like object
        Must support .write(bytes) and .flush(); pass None for boardless mode.
    """
    back_requested = pyqtSignal()

    def __init__(self, ser, parent: QWidget | None = None):
        super().__init__(parent)
        self.ser = ser                      # <- remember the port (can be None)

        self.setObjectName("PowerPongPage")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        root = QVBoxLayout(self)

        title = QLabel("Power Pong Game", alignment=Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("Title")
        root.addWidget(title)

        # Picker controls
        row = QHBoxLayout(); row.setSpacing(40)

        self.speed_picker  = Picker("Speed", increment=5)
        self.offset_picker = Picker("Offset")

        # wire pickers to serial ------------------------------------------------
        self.speed_picker.value_added.connect(self._send_speed)
        self.offset_picker.value_added.connect(self._send_offset)

        row.addStretch(1)
        row.addWidget(self.speed_picker)
        row.addWidget(self.offset_picker)
        row.addStretch(1)

        # Create a vertical layout for the FORE and Zero Position buttons
        button_column = QVBoxLayout()
        button_column.setSpacing(8)  # Small spacing between buttons
        
        fore_btn = QPushButton("FORE!")
        fore_btn.setObjectName("ForeBtn")
        fore_btn.clicked.connect(self._send_fore)
        button_column.addWidget(fore_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Add Zero Position button underneath the FORE button
        zero_btn = QPushButton("Zero Position")
        zero_btn.setObjectName("ZeroBtn")
        zero_btn.clicked.connect(self._send_zero_position)
        button_column.addWidget(zero_btn, alignment=Qt.AlignmentFlag.AlignHCenter)
        
        # Add the button column to the main row
        row.addLayout(button_column)

        row.addStretch(1)
        root.addLayout(row, stretch=1)

        # Back button
        back_btn = QPushButton("Back")
        back_btn.setObjectName("BackBtn")
        back_btn.clicked.connect(self.go_back)
        root.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Load stylesheet
        css_file = STYLES_DIR / "stylePowerPongPage.qss"
        self.setStyleSheet(css_file.read_text())
        
        # Shrinking circle animation
        self.shrinking_circle = True  # Start with white screen
        self.circle_radius = 933  # Start with full screen coverage
        self.circle_center = QPointF(400, 240)  # Center of screen
        self.shrink_animation_timer = QTimer()
        self.shrink_animation_timer.timeout.connect(self.update_shrink_animation)
        self.shrink_animation_timer.setInterval(16)  # 60 FPS for smooth animation
        self.shrink_frames = 35  # Same speed as expanding circle
        self.shrink_frame_count = 0
        
        # Don't create overlay here - wait until page is shown
        self.circle_overlay = None
        
        # White transition animation (going back)
        self.white_transition_timer = QTimer()
        self.white_transition_timer.timeout.connect(self.update_white_transition)
        self.white_transition_timer.setInterval(16)  # 60 FPS for smooth animation
        self.white_transition_frames = 30  # 0.5 seconds
        self.white_transition_frame_count = 0
        self.white_transition_active = False
        
        # Don't create white transition overlay here - wait until needed
        self.white_transition_overlay = None

    # Serial communication helpers
    def _write(self, text: str):
        """
        Low-level send. Falls back to a console print when no port present.
        """
        if self.ser is None:
            print("→", text.strip())
            return
        self.ser.write(text.encode())                # includes trailing \n
        self.ser.flush()

    def _send_speed(self, value: int):
        self._write(f"T{value}\n")

    def _send_offset(self, value: int):
        self._write(f"O{value}\n")

    def _send_fore(self):
        self._write("G\n")

    def _send_zero_position(self):
        # Send command in SimpleFOC Commander format: "R {offset}"
        current_offset = 90
        self._write(f"R{current_offset}\n")
        
    # Animation methods
    def _reset_shrink_animation(self):
        """Reset the shrinking circle animation to initial state"""
        self.shrink_frame_count = 0
        self.shrinking_circle = True
        self.circle_radius = 933  # Full screen coverage
        if hasattr(self, 'shrink_animation_timer'):
            self.shrink_animation_timer.stop()
            
    def update_shrink_animation(self):
        """Update the shrinking circle animation"""
        self.shrink_frame_count += 1
        
        # Calculate progress (0.0 to 1.0) - reverse of expanding circle
        progress = 1.0 - (self.shrink_frame_count / self.shrink_frames)
        progress = max(0.0, progress)  # Don't go below 0
        
        # Calculate radius based on progress
        max_radius = 933
        self.circle_radius = progress * max_radius
        
        # Update the overlay widget if it exists
        if self.circle_overlay is not None:
            self.circle_overlay.update_circle(self.circle_radius)
            
            # Check if shrinking is complete
            if self.shrink_frame_count >= self.shrink_frames:
                self.shrink_animation_timer.stop()
                self.shrinking_circle = False
                self.circle_overlay.set_animation_state(False)  # Hide the overlay
                
    def _reset_white_transition(self):
        """Reset the white transition animation to initial state"""
        self.white_transition_frame_count = 0
        self.white_transition_active = False
        if hasattr(self, 'white_transition_timer'):
            self.white_transition_timer.stop()
            
    def update_white_transition(self):
        """Update the white transition animation when going back"""
        self.white_transition_frame_count += 1
        
        # Calculate progress (0.0 to 1.0)
        progress = min(self.white_transition_frame_count / self.white_transition_frames, 1.0)
        
        # Calculate radius based on progress - expand from center to fill screen
        max_radius = 933  # Full screen coverage
        self.white_transition_radius = progress * max_radius
        
        # Update the white overlay widget if it exists
        if self.white_transition_overlay is not None:
            self.white_transition_overlay.update_circle(self.white_transition_radius)
            
            # Check if expansion is complete
            if self.white_transition_frame_count >= self.white_transition_frames:
                self.white_transition_timer.stop()
                self.white_transition_active = False
                
                # Now that the white circle has filled the screen, emit the back signal
                # This will trigger the page transition to main menu
                self.back_requested.emit()
                
    def go_back(self):
        """User hit Back -> start white transition animation, then switch to menu."""
        # Send MAIN_MENU command to Arduino 
        self.ser.write(b"M\n")
        self.ser.flush()
        # Clean up shrinking animation state
        if self.circle_overlay is not None:
            self.shrink_animation_timer.stop()
            self.circle_overlay.hide()
            
        # Clean up white transition animation state
        if hasattr(self, 'white_transition_timer'):
            self.white_transition_timer.stop()
        
        # Start the white transition animation
        self._start_white_transition()
        
    def _start_white_transition(self):
        """Start the white circle expansion animation when going back"""
        # Create the white transition overlay
        self.white_transition_overlay = WhiteTransitionOverlay(self)
        self.white_transition_overlay.setFixedSize(800, 480)
        self.white_transition_overlay.move(0, 0)  # Position at top-left corner
        self.white_transition_overlay.raise_()  # Ensure it's on top of everything
        self.white_transition_overlay.show()  # Show the overlay
        
        # Reset animation state
        self.white_transition_frame_count = 0
        self.white_transition_active = True
        
        # Activate the white overlay
        self.white_transition_overlay.set_animation_state(True)
        
        # Start the animation timer
        self.white_transition_timer.start()

    def showEvent(self, event):
        """Override showEvent to trigger the white screen collapse animation"""
        super().showEvent(event)
        
        # Always reset and recreate the overlays when the page is shown
        # This ensures the animations work every time
        
        # Clean up existing white shrinking overlay
        if self.circle_overlay is not None:
            self.circle_overlay.deleteLater()
            self.circle_overlay = None
            
        # Clean up existing white transition overlay (from previous visits)
        if hasattr(self, 'white_transition_overlay') and self.white_transition_overlay is not None:
            self.white_transition_overlay.deleteLater()
            self.white_transition_overlay = None
        
        # Create fresh white shrinking overlay
        self.circle_overlay = CircleOverlay(self)
        self.circle_overlay.setFixedSize(800, 480)
        self.circle_overlay.move(0, 0)  # Position at top-left corner
        self.circle_overlay.raise_()  # Ensure it's on top of everything
        self.circle_overlay.show()  # Explicitly show the overlay
        
        # Reset animation state and start the shrinking animation
        self._reset_shrink_animation()
        self._reset_white_transition()  # Also reset white transition state
        self.shrink_animation_timer.start()
