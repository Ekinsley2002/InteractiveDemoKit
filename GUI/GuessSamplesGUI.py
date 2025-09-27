import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, 
                             QGraphicsProxyWidget, QFrame)
from PyQt6.QtCore import pyqtSignal, Qt, QPointF, QRectF, QMimeData
from PyQt6.QtGui import QPixmap, QDrag, QPainter, QColor, QFont


class DraggableLabel(QLabel):
    """A draggable label that can be moved around the scene"""
    
    def __init__(self, text, target_image_name, parent=None):
        super().__init__(text, parent)
        self.target_image_name = target_image_name
        self.setAcceptDrops(False)
        self.setStyleSheet("""
            QLabel {
                background-color: #FAC01A;
                color: #002454;
                border: 2px solid #002454;
                border-radius: 8px;
                padding: 8px 12px;
                font: 600 14px 'Roboto';
                min-width: 100px;
                max-width: 100px;
            }
        """)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.pos()
    
    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
            
        if ((event.pos() - self.drag_start_position).manhattanLength() < 10):
            return
            
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(self.text())
        mime_data.setData("target_image", self.target_image_name.encode())
        drag.setMimeData(mime_data)
        
        # Create a pixmap of the label for dragging
        pixmap = self.grab()
        drag.setPixmap(pixmap)
        drag.setHotSpot(self.drag_start_position)
        
        drag.exec(Qt.DropAction.MoveAction)


class DropZone(QLabel):
    """A drop zone that accepts dropped labels"""
    
    def __init__(self, image_path, expected_label, parent=None):
        super().__init__(parent)
        self.expected_label = expected_label
        self.dropped_label = None
        self.setAcceptDrops(True)
        
        # Load and display the image
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            scaled_pixmap = pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio, 
                                         Qt.TransformationMode.SmoothTransformation)
            self.setPixmap(scaled_pixmap)
        else:
            self.setText(f"Image not found:\n{os.path.basename(image_path)}")
            self.setStyleSheet("color: white; font: 12px;")
            self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #FAC01A;
                border-radius: 8px;
                background-color: rgba(250, 192, 26, 0.1);
                padding: 10px;
            }
        """)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(220, 220)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
            self.setStyleSheet("""
                QLabel {
                    border: 2px solid #00FF00;
                    border-radius: 8px;
                    background-color: rgba(0, 255, 0, 0.2);
                    padding: 10px;
                }
            """)
    
    def dragLeaveEvent(self, event):
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #FAC01A;
                border-radius: 8px;
                background-color: rgba(250, 192, 26, 0.1);
                padding: 10px;
            }
        """)
    
    def dropEvent(self, event):
        if event.mimeData().hasText():
            label_text = event.mimeData().text()
            
            # Fix the QByteArray decode issue
            target_image_bytes = event.mimeData().data("target_image")
            if target_image_bytes:
                try:
                    target_image = target_image_bytes.data().decode()
                except AttributeError:
                    target_image = target_image_bytes.decode()
            else:
                target_image = ""
            
            # Create a label showing what was dropped
            self.dropped_label = label_text
            self.setStyleSheet("""
                QLabel {
                    border: 2px solid #FAC01A;
                    border-radius: 8px;
                    background-color: rgba(250, 192, 26, 0.3);
                    padding: 10px;
                }
            """)
            
            # Notify parent that a drop occurred
            parent_widget = self.parent()
            while parent_widget and not hasattr(parent_widget, 'on_drop'):
                parent_widget = parent_widget.parent()
            if parent_widget and hasattr(parent_widget, 'on_drop'):
                parent_widget.on_drop(self, label_text, target_image)
            
            event.acceptProposedAction()


class GuessSamplesPageWidget(QWidget):
    """Interactive drag-and-drop guessing game for sample identification"""
    
    back_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setObjectName("GuessSamplesPage")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        
        # Load the same style as AFM page for consistency
        with open("Styles/styleAfmPage.qss", "r") as f:
            self.setStyleSheet(f.read())
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Guess the Samples!")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                color: #FAC01A;
                font: 600 28px 'Roboto';
                margin: 20px;
                background-color: transparent;
                border: none;
            }
        """)
        layout.addWidget(title)
        
        # Instructions
        instructions = QLabel("Drag the labels to match the correct samples below:")
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instructions.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font: 600 16px 'Roboto';
                margin: 10px;
                background-color: transparent;
                border: none;
            }
        """)
        layout.addWidget(instructions)
        
        # Create draggable labels
        labels_container = QHBoxLayout()
        labels_container.setSpacing(20)
        
        self.draggable_labels = []
        label_names = ["NAU LOGO", "HUMPHREYS", "HEXAGONAL"]
        image_names = ["NAU_LOGO", "HUMPHREYS", "HEXAGONAL"]
        
        for i, (label_name, image_name) in enumerate(zip(label_names, image_names)):
            label = DraggableLabel(label_name, image_name)
            self.draggable_labels.append(label)
            labels_container.addWidget(label)
        
        layout.addLayout(labels_container)
        
        # Create drop zones for images
        images_container = QHBoxLayout()
        images_container.setSpacing(20)
        
        self.drop_zones = []
        image_paths = [
            "Images/Ref_Graphs/NAU_LOGO.png",
            "Images/Ref_Graphs/HUMPHREYS.png",
            "Images/Ref_Graphs/HEXAGONAL.png"
        ]
        expected_labels = ["NAU LOGO", "HUMPHREYS", "HEXAGONAL"]
        
        for image_path, expected_label in zip(image_paths, expected_labels):
            drop_zone = DropZone(image_path, expected_label)
            self.drop_zones.append(drop_zone)
            images_container.addWidget(drop_zone)
        
        layout.addLayout(images_container)
        
        # Guess button and feedback
        button_container = QHBoxLayout()
        
        self.guess_button = QPushButton("GUESS!")
        self.guess_button.setObjectName("GuessBtn")
        self.guess_button.setStyleSheet("""
            QPushButton#GuessBtn {
                font: 600 20px 'Roboto';
                color: #FFFFFF;
                background-color: #00AA00;
                border: 2px solid #008800;
                border-radius: 8px;
                padding: 15px 30px;
                min-width: 150px;
            }
            QPushButton#GuessBtn:hover {
                background-color: #00CC00;
            }
            QPushButton#GuessBtn:pressed {
                background-color: #008800;
            }
        """)
        self.guess_button.clicked.connect(self.check_guess)
        button_container.addWidget(self.guess_button)
        
        # Feedback label
        self.feedback_label = QLabel("")
        self.feedback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.feedback_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font: 600 16px 'Roboto';
                background-color: transparent;
                border: none;
            }
        """)
        button_container.addWidget(self.feedback_label)
        
        layout.addLayout(button_container)
        
        # Back button
        back_btn = QPushButton("Back")
        back_btn.setObjectName("BackBtn")
        back_btn.clicked.connect(self.back_requested.emit)
        layout.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignHCenter)
        
        # Initialize tracking
        self.reset_game()
    
    def reset_game(self):
        """Reset the game state"""
        self.correct_matches = {}
        self.feedback_label.setText("")
        self.guess_button.setEnabled(True)
        
        # Reset drop zone styles
        for drop_zone in self.drop_zones:
            drop_zone.setStyleSheet("""
                QLabel {
                    border: 2px dashed #FAC01A;
                    border-radius: 8px;
                    background-color: rgba(250, 192, 26, 0.1);
                    padding: 10px;
                }
            """)
            drop_zone.dropped_label = None
    
    def on_drop(self, drop_zone, label_text, target_image):
        """Handle when a label is dropped on a drop zone"""
        self.correct_matches[drop_zone.expected_label] = label_text
    
    def check_guess(self):
        """Check if all matches are correct"""
        correct_count = 0
        total_count = len(self.drop_zones)
        
        # Debug: Print what we're checking
        print("Checking guesses:")
        for i, drop_zone in enumerate(self.drop_zones):
            print(f"Drop zone {i}: expected='{drop_zone.expected_label}', got='{drop_zone.dropped_label}'")
        
        # Check each drop zone to see if the correct label was dropped on it
        for drop_zone in self.drop_zones:
            if drop_zone.dropped_label == drop_zone.expected_label:
                correct_count += 1
        
        if correct_count == total_count:
            self.feedback_label.setText("🎉 Perfect! All matches are correct!")
            self.feedback_label.setStyleSheet("""
                QLabel {
                    color: #00FF00;
                    font: 600 16px 'Roboto';
                    background-color: transparent;
                    border: none;
                }
            """)
            self.guess_button.setEnabled(False)
        else:
            self.feedback_label.setText(f"❌ {correct_count}/{total_count} correct. Try again!")
            self.feedback_label.setStyleSheet("""
                QLabel {
                    color: #FF6B6B;
                    font: 600 16px 'Roboto';
                    background-color: transparent;
                    border: none;
                }
            """)
