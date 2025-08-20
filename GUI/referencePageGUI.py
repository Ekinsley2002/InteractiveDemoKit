import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QPixmap


class ReferencePageWidget(QWidget):
    back_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setObjectName("ReferencePage")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        # Load the same style as AFM page for consistency
        with open("Styles/styleAfmPage.qss", "r") as f:
            self.setStyleSheet(f.read())

        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("NAU Logo")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #FFFFFF; font: 600 28px 'Roboto'; margin: 20px;")
        layout.addWidget(title)

        # Image container
        image_label = QLabel()
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Load and display the NAU logo
        image_path = "Images/Ref_Graphs/NAU_LOGO.png"
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            # Scale the image to fit nicely in the layout while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(500, 500, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            image_label.setPixmap(scaled_pixmap)
        else:
            # Fallback if image not found
            image_label.setText("NAU Logo Image Not Found")
            image_label.setStyleSheet("color: #FFFFFF; font: 600 18px 'Roboto';")
        
        layout.addWidget(image_label, stretch=1)

        # Back button
        back_btn = QPushButton("Back")
        back_btn.clicked.connect(self.back_requested.emit)
        layout.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignHCenter)
