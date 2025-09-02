from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtGui import QPainter, QColor

class HapticFeedbackAnimation(QWidget):
    """Haptic Feedback loading animation with blue background and yellow loading bar"""
    
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
        
        # Add spacing to push loading bar to bottom
        layout.addStretch(1)
        
        # Create loading bar at the bottom
        self.loading_bar = QProgressBar()
        self.loading_bar.setRange(0, 100)
        self.loading_bar.setValue(0)
        self.loading_bar.setFixedHeight(20)
        self.loading_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #FAC01A;
                border-radius: 10px;
                background-color: rgba(255, 255, 255, 0.1);
                margin: 0px 40px 40px 40px;
            }
            QProgressBar::chunk {
                background-color: #FAC01A;
                border-radius: 8px;
            }
        """)
        layout.addWidget(self.loading_bar)
        
        # Animation timer for loading bar
        self.loading_timer = QTimer()
        self.loading_timer.timeout.connect(self.update_loading_bar)
        self.loading_timer.setInterval(30)  # Update every 30ms for smooth animation
        
        # Animation properties
        self.animation_duration = 4000  # 3 seconds in milliseconds
        self.current_progress = 0
        self.progress_increment = 100 / (self.animation_duration / 30)  # Calculate increment per frame
        
    def start_animation(self):
        """Start the Haptic Feedback loading animation"""
        # Reset progress
        self.current_progress = 0
        self.loading_bar.setValue(0)
        
        # Show the animation
        self.show()
        self.raise_()
        
        # Start the loading bar animation
        self.loading_timer.start()
        
        # Set up completion timer
        QTimer.singleShot(self.animation_duration, self.complete_animation)
    
    def update_loading_bar(self):
        """Update the loading bar progress"""
        self.current_progress += self.progress_increment
        
        # Ensure we don't exceed 100%
        if self.current_progress >= 100:
            self.current_progress = 100
            self.loading_timer.stop()
        
        # Update the progress bar
        self.loading_bar.setValue(int(self.current_progress))
    
    def complete_animation(self):
        """Called when animation completes"""
        # Ensure loading bar is at 100%
        self.loading_bar.setValue(100)
        
        # Stop the loading timer
        self.loading_timer.stop()
        
        # Emit completion signal
        self.animation_complete.emit()
    
    def stop_animation(self):
        """Stop the animation"""
        self.loading_timer.stop()
