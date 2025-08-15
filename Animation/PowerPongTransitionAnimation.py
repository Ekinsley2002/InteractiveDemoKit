# PowerPongTransitionAnimation.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QPainter, QColor


class PowerPongTransitionAnimation(QWidget):
    """Simple blue screen transition animation for Power Pong page"""
    
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
        
        # Create layout for text content (similar to GraphingLineAnimation)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Add spacing to center the text
        layout.addStretch(2)
        
        # Add title text
        title_label = QLabel("POWER PONG TRANSITION")
        title_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font: 600 36px 'Roboto';
                background-color: transparent;
            }
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Add subtitle
        subtitle_label = QLabel("Preparing to play...")
        subtitle_label.setStyleSheet("""
            QLabel {
                color: #CEF9F2;
                font: 400 20px 'Roboto';
                background-color: transparent;
            }
        """)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle_label)
        
        # Add spacing to center the text
        layout.addStretch(2)
        
        # Animation timer - make it shorter for testing
        self.transition_timer = QTimer()
        self.transition_timer.timeout.connect(self.complete_transition)
        self.transition_duration = 3000  # 3 seconds for testing
        
    def start_animation(self):
        """Start the blue screen transition animation"""
        # Show the blue screen
        self.show()
        self.raise_()
        
        # Start timer to complete transition
        self.transition_timer.start(self.transition_duration)
        
    def complete_transition(self):
        """Called when transition timer expires"""
        self.transition_timer.stop()
        self.animation_complete.emit()
        
    def paintEvent(self, event):
        """Custom paint event to ensure the blue background is drawn"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw the blue background manually as a fallback
        painter.fillRect(self.rect(), QColor(0, 36, 84))  # #002454

