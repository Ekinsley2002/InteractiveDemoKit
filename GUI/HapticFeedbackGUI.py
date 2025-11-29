from pathlib import Path
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore    import Qt, QSize, pyqtSignal, QTimer, QPointF
from PyQt6.QtGui     import QIcon, QCursor, QPainter, QColor
import serial

PROJECT_ROOT = Path(__file__).resolve().parent.parent
IMAGES_DIR   = Path("Images")
STYLES_DIR   = PROJECT_ROOT / "Styles"


class CircleOverlay(QWidget):
    """Separate overlay widget for the shrinking circle animation"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        
        # Animation properties
        self.circle_radius = 1000  # Start with full screen coverage
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
        painter.setPen(Qt.PenStyle.NoPen)
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
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(255, 255, 255))  # White fill
        painter.drawEllipse(self.circle_center, self.circle_radius, self.circle_radius)


class Picker(QWidget):
    """One vertical picker column with ▲ / ▼ / Add."""
    value_added = pyqtSignal(str)

    COL_W = 200

    def __init__(self, title: str, min_val: float = 0, max_val: float = 50, is_float: bool = False, parent: QWidget | None = None):
        super().__init__(parent)
        self._value = min_val
        self._min_val = min_val
        self._max_val = max_val
        self._is_float = is_float
        self._increment = 0.1 if is_float else 1

        v = QVBoxLayout(self)
        v.setSpacing(12)
        v.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        title_lbl = QLabel(title, alignment=Qt.AlignmentFlag.AlignHCenter)
        title_lbl.setObjectName("PickerTitle")
        title_lbl.setFixedWidth(self.COL_W)

        self.value_lbl = QLabel(str(self._value), alignment=Qt.AlignmentFlag.AlignCenter)
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
        if self._min_val <= new_value <= self._max_val:
            self._value = new_value
            display_text = f"{self._value:.1f}" if self._is_float else str(int(self._value))
            self.value_lbl.setText(display_text)

    def _emit_add(self):
        formatted_value = f"{self._value:.1f}" if self._is_float else str(int(self._value))
        self.value_added.emit(formatted_value)


class HapticFeedbackPageWidget(QWidget):
    """Haptic Feedback page with adjustable parameters for ticks and spring constant."""
    back_requested = pyqtSignal()

    def __init__(self, serial_connection=None, parent=None):
        super().__init__(parent)

        self.serial_connection = serial_connection
        
        # Animation state tracking
        self.animation_in_progress = False

        self.setObjectName("HapticFeedbackPage")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        root = QVBoxLayout(self)

        # Add yellow title at the very top center
        title = QLabel("Haptic Feedback")
        title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        title.setObjectName("Title")
        root.addWidget(title)

        # Picker controls
        row = QHBoxLayout(); row.setSpacing(40)

        self.ticks_picker = Picker("Number of Ticks", 1, 20, is_float=False)
        self.spring_picker = Picker("Spring Constant", 0.1, 10.0, is_float=True)

        # Wire pickers to handle value changes
        self.ticks_picker.value_added.connect(self._send_num_ticks)
        self.spring_picker.value_added.connect(self._send_spring_constant)

        row.addStretch(1)
        row.addWidget(self.ticks_picker)
        row.addWidget(self.spring_picker)
        row.addStretch(1)

        root.addLayout(row, stretch=1)

        # Back button
        back_btn = QPushButton("Back")
        back_btn.setObjectName("BackBtn")
        back_btn.clicked.connect(self.go_back)
        root.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        # Load stylesheet
        css_file = STYLES_DIR / "styleHapticFeedbackPage.qss"
        if css_file.exists():
            self.setStyleSheet(css_file.read_text())
        else:
            # Fallback styling if CSS file doesn't exist
            self.setStyleSheet("""
                QWidget#HapticFeedbackPage {
                    background-color: #002454;
                    color: #FFFFFF;
                }
                QLabel#Title {
                    font: 600 32px 'Roboto';
                    color: #FAC01A;
                    margin: 20px 0px;
                }
                QLabel#PickerTitle {
                    font: 600 18px 'Roboto';
                    color: #FFFFFF;
                }
                QLabel#ValueDisplay {
                    font: 600 24px 'Roboto';
                    color: #FAC01A;
                    background-color: rgba(255,255,255,0.10);
                    border: 2px solid #FAC01A;
                    border-radius: 8px;
                    padding: 0px;
                    margin: 0px;
                }
                QPushButton#ArrowBtn {
                    background-color: rgba(255,255,255,0.05);
                    border: 2px solid #FAC01A;
                    border-radius: 8px;
                }
                QPushButton#ArrowBtn:hover {
                    background-color: rgba(255,255,255,0.10);
                }
                QPushButton#AddBtn {
                    font: 600 16px 'Roboto';
                    color: #FFFFFF;
                    background-color: rgba(255,255,255,0.05);
                    border: 2px solid #FAC01A;
                    border-radius: 8px;
                    padding: 8px 16px;
                }
                QPushButton#AddBtn:hover {
                    background-color: rgba(255,255,255,0.10);
                }
                QPushButton#BackBtn {
                    font: 600 18px 'Roboto';
                    color: #FFFFFF;
                    background-color: rgba(255,255,255,0.05);
                    border: 2px solid #FAC01A;
                    border-radius: 8px;
                    padding: 12px 24px;
                    min-width: 200px;
                }
                QPushButton#BackBtn:hover {
                    background-color: rgba(255,255,255,0.10);
                }
            """)
        
        # Store button references for enable/disable functionality
        self.all_buttons = [
            self.ticks_picker.up_btn if hasattr(self.ticks_picker, 'up_btn') else None,
            self.ticks_picker.down_btn if hasattr(self.ticks_picker, 'down_btn') else None,
            self.ticks_picker.add_btn if hasattr(self.ticks_picker, 'add_btn') else None,
            self.spring_picker.up_btn if hasattr(self.spring_picker, 'up_btn') else None,
            self.spring_picker.down_btn if hasattr(self.spring_picker, 'down_btn') else None,
            self.spring_picker.add_btn if hasattr(self.spring_picker, 'add_btn') else None,
            back_btn
        ]
        # Filter out None values
        self.all_buttons = [btn for btn in self.all_buttons if btn is not None]
        
        # Shrinking circle animation setup
        self.shrink_animation_timer = QTimer()
        self.shrink_animation_timer.timeout.connect(self.update_shrink_animation)
        self.shrink_animation_timer.setInterval(16)  # 60 FPS for smooth animation
        self.shrink_frames = 35  # Same as AFM
        self.shrink_frame_count = 0
        self.circle_overlay = None
        
        # White transition animation (going back)
        self.white_transition_timer = QTimer()
        self.white_transition_timer.timeout.connect(self.update_white_transition)
        self.white_transition_timer.setInterval(16)  # 60 FPS for smooth animation
        self.white_transition_frames = 35  # Match shrinking animation speed
        self.white_transition_frame_count = 0
        self.white_transition_active = False
        self.white_transition_overlay = None

    # Serial communication helpers
    def _write(self, text: str):
        """Low-level send. Falls back to console print when no port present."""
        if self.serial_connection is None:
            print("→", text.strip())
            return
        self.serial_connection.write(text.encode())
        self.serial_connection.flush()

    def _send_num_ticks(self, value: str):
        """Send number of ticks command: n{value}"""
        if self.animation_in_progress:
            return
        self._write(f"n{value}\n")

    def _send_spring_constant(self, value: str):
        """Send spring constant command: k{value}"""
        if self.animation_in_progress:
            return
        self._write(f"k{value}\n")
    
    def disable_all_buttons(self):
        """Disable all buttons during animations"""
        self.animation_in_progress = True
        for button in self.all_buttons:
            button.setEnabled(False)
    
    def enable_all_buttons(self):
        """Enable all buttons after animations complete"""
        self.animation_in_progress = False
        for button in self.all_buttons:
            button.setEnabled(True)

    def _reset_white_transition(self):
        """Reset the white transition animation to initial state"""
        self.white_transition_frame_count = 0
        self.white_transition_active = False
        if hasattr(self, 'white_transition_timer'):
            self.white_transition_timer.stop()
    
    def showEvent(self, event):
        """Called when page is shown - clean up overlays and reset animations"""
        super().showEvent(event)
        
        # Always reset and recreate the overlays when the page is shown
        # This ensures the animations work every time
        
        # Clean up existing white shrinking overlay
        if self.circle_overlay is not None:
            self.circle_overlay.deleteLater()
            self.circle_overlay = None
        
        # Clean up existing white transition overlay (from previous visits)
        if self.white_transition_overlay is not None:
            self.white_transition_overlay.deleteLater()
            self.white_transition_overlay = None
        
        # Reset animation states
        self._reset_white_transition()
    
    def start_shrink_animation(self):
        """Start the shrinking circle animation when page is first shown"""
        # Clean up existing overlay if any
        if self.circle_overlay is not None:
            self.circle_overlay.setParent(None)
            self.circle_overlay.deleteLater()
            self.circle_overlay = None
        
        # Create fresh white shrinking overlay
        self.circle_overlay = CircleOverlay(self)
        self.circle_overlay.setFixedSize(800, 480)
        self.circle_overlay.move(0, 0)
        self.circle_overlay.raise_()
        self.circle_overlay.show()
        
        # Reset animation state and start the shrinking animation
        self.shrink_frame_count = 0
        self.shrink_animation_timer.start()
    
    def update_shrink_animation(self):
        """Update the shrinking circle animation"""
        self.shrink_frame_count += 1
        
        # Calculate progress (1.0 to 0.0 - shrinking)
        progress = 1.0 - (self.shrink_frame_count / self.shrink_frames)
        progress = max(0.0, progress)  # Clamp to 0
        
        # Calculate new radius - shrink from full screen to small circle
        start_radius = 1000  # Full screen coverage
        end_radius = 25      # Small circle in center
        new_radius = int(start_radius - (start_radius - end_radius) * (1.0 - progress))
        
        # Update the circle overlay
        if self.circle_overlay is not None:
            self.circle_overlay.update_circle(new_radius)
        
        # Check if shrinking is complete
        if self.shrink_frame_count >= self.shrink_frames:
            self.shrink_animation_timer.stop()
            
            # Hide the overlay completely
            if self.circle_overlay is not None:
                self.circle_overlay.set_animation_state(False)
                self.circle_overlay.hide()
                self.circle_overlay.setParent(None)
                self.circle_overlay.deleteLater()
                self.circle_overlay = None
    
    def update_white_transition(self):
        """Update the white transition animation when going back"""
        self.white_transition_frame_count += 1
        
        # Calculate progress (0.0 to 1.0)
        progress = min(self.white_transition_frame_count / self.white_transition_frames, 1.0)
        
        # Calculate radius based on progress - expand from center to fill screen
        max_radius = 1000  # Full screen coverage
        white_transition_radius = progress * max_radius
        
        # Update the white overlay widget if it exists
        if self.white_transition_overlay is not None:
            self.white_transition_overlay.update_circle(white_transition_radius)
            
            # Check if expansion is complete
            if self.white_transition_frame_count >= self.white_transition_frames:
                self.white_transition_timer.stop()
                self.white_transition_active = False
                
                # Re-enable buttons before emitting back signal
                self.enable_all_buttons()
                
                # Now that the white circle has filled the screen, emit the back signal
                self.back_requested.emit()
    
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
    
    def go_back(self):
        """Start white transition animation, then emit back signal"""
        if self.animation_in_progress:
            return
        
        # Disable buttons during animation
        self.disable_all_buttons()
        
        # Send MAIN_MENU command to Arduino to reset it from Haptic Feedback mode
        self.serial_connection.write(b"M\n")
        self.serial_connection.flush()
        
        # Clean up any existing white transition overlay
        if self.white_transition_overlay is not None:
            self.white_transition_overlay.deleteLater()
            self.white_transition_overlay = None
        
        # Start the white transition animation
        self._start_white_transition()
