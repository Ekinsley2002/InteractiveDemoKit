import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
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
        title = QLabel("Reference Graphs")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #FAC01A; font: 600 28px 'Roboto'; margin: 20px;")
        layout.addWidget(title)

        # Create horizontal layout for the three images
        images_layout = QHBoxLayout()
        images_layout.setSpacing(20)  # Space between images
        
        # Image file paths
        image_files = [
            "Images/Ref_Graphs/HEXAGONAL.png",
            "Images/Ref_Graphs/HUMPHREYS.png", 
            "Images/Ref_Graphs/NAU_LOGO.png"
        ]
        
        # Load and display all three images
        for image_path in image_files:
            image_label = QLabel()
            image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            if os.path.exists(image_path):
                pixmap = QPixmap(image_path)
                # Scale the image to fit nicely in the layout while maintaining aspect ratio
                scaled_pixmap = pixmap.scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                image_label.setPixmap(scaled_pixmap)
            else:
                # Fallback if image not found
                filename = os.path.basename(image_path)
                image_label.setText(f"{filename}\nNot Found")
                image_label.setStyleSheet("color: #FFFFFF; font: 600 14px 'Roboto';")
            
            images_layout.addWidget(image_label)
        
        # Center the images layout
        layout.addLayout(images_layout, stretch=1)

        # Back button
        back_btn = QPushButton("Back")
        back_btn.clicked.connect(self.back_requested.emit)
        layout.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignHCenter)
