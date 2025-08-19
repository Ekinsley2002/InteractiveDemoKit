# HapticFeedbackGUI.py
from pathlib import Path
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore    import Qt, pyqtSignal
from PyQt6.QtGui     import QPixmap

# Get the styles directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
STYLES_DIR   = PROJECT_ROOT / "Styles"

class HapticFeedbackPageWidget(QWidget):
    """
    Haptic Feedback page for touch and tactile response demonstrations.
    """
    back_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self.setObjectName("HapticFeedbackPage")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        # Load the stylesheet
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
                QPushButton {
                    font: 600 18px 'Roboto';
                    color: #FFFFFF;
                    background-color: #003366;
                    border: 2px solid #FAC01A;
                    border-radius: 8px;
                    padding: 12px 24px;
                    min-width: 200px;
                }
                QPushButton:hover {
                    background-color: #004477;
                }
                QPushButton:pressed {
                    background-color: #002255;
                }
            """)

        root = QVBoxLayout(self)

        title = QLabel("Haptic Feedback", alignment=Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("Title")
        root.addWidget(title)

        # Main content area - placeholder for haptic feedback controls
        content_label = QLabel("Haptic Feedback Controls\n\nTouch and tactile response demonstrations will be implemented here.", 
                             alignment=Qt.AlignmentFlag.AlignCenter)
        content_label.setObjectName("ContentLabel")
        content_label.setStyleSheet("""
            QLabel#ContentLabel {
                font: 400 16px 'Roboto';
                color: #CEF9F2;
                margin: 40px 20px;
                padding: 20px;
                border: 2px solid #FAC01A;
                border-radius: 12px;
                background-color: rgba(0, 52, 132, 0.3);
            }
        """)
        root.addWidget(content_label, stretch=1)

        # Back button
        back_btn = QPushButton("Back")
        back_btn.setObjectName("BackBtn")
        back_btn.clicked.connect(self.back_requested.emit)
        root.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignHCenter)
