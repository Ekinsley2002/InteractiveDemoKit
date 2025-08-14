# PowerPongTransitionAnimation.py
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, pyqtSignal, QTimer


class PowerPongTransitionAnimation(QWidget):
    """Simple blue screen transition animation for Power Pong page"""
    
    # Signal emitted when animation completes
    animation_complete = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Set up the widget properties
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setFixedSize(800, 480)
        
        # Set solid blue background matching your theme
        self.setStyleSheet("background-color: #002454;")
        
        # Animation timer
        self.transition_timer = QTimer()
        self.transition_timer.timeout.connect(self.complete_transition)
        self.transition_duration = 500  # 0.5 seconds
        
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
