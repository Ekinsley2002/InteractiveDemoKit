# AfmGUI.py
import time, serial, os
import numpy as np
import pyqtgraph as pg
import matplotlib.pyplot as plt
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPointF
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel
)
from PyQt6.QtGui import QPainter, QColor, QPen


class CircleOverlay(QWidget):
    """Separate overlay widget for the shrinking circle animation"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)  # Pass through mouse events
        # Remove the transparency attributes that might be hiding the widget
        # self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        # self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        # Animation properties
        self.circle_radius = 933  # Start with full screen coverage
        self.circle_center = QPointF(400, 240)  # Center of screen
        self.shrinking_circle = True
        
        # Set a solid background to ensure visibility
        self.setStyleSheet("background-color: white;")  # Start with solid white background
        
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


class BlueTransitionOverlay(QWidget):
    """Overlay widget for the blue transition when going back to main menu"""
    
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
        """Draw the expanding blue circle overlay"""
        if not self.expanding_circle:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw blue circle that expands to fill the screen
        painter.setPen(Qt.PenStyle.NoPen)  # No outline
        painter.setBrush(QColor(0, 36, 84))  # #002454 blue fill
        painter.drawEllipse(self.circle_center, self.circle_radius, self.circle_radius)


class AfmPageWidget(QWidget):

    back_requested = pyqtSignal()
    map_requested = pyqtSignal()

    def __init__(self, ser, parent=None):
        super().__init__(parent)

        self.ser = ser

        self.setObjectName("AfmPage")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        with open("Styles/styleAfmPage.qss", "r") as f:
            self.setStyleSheet(f.read())

        self.INIT_Y_MINMAX = (0, 0.5)
        self.AUTO_TRIP_DEG = 2.0
        self.SETTLE_DEG = 0.5
        self.SETTLE_SECS = 10.0
        self.WINDOW_SECONDS = 10
        self.TIMER_MS = 25

        self.DEAD_ZONE = 0.01
        self.LPF_ALPHA = 0.20

        self.MAX_TRIALS = 4
        self.RECORD_DURATION = 10
        self.MAX_VALUES_PER_TRIAL = 100
        self.TRIAL_FILE = "trials.txt"

        # ── GUI Setup ─────────────────────────────
        layout = QVBoxLayout(self)

        # 1) A dedicated container that will hold BOTH the GraphicsLayoutWidget
        #    *and* the Back button.
        graph_holder = QtWidgets.QWidget(self)
        graph_holder.setObjectName("GraphHolder")

        # zero-margin layout so the plot fills the whole thing
        gh_layout = QVBoxLayout(graph_holder)
        gh_layout.setContentsMargins(0, 0, 0, 0)

        win = pg.GraphicsLayoutWidget(title="Gimbal angle (°)")
        win.setBackground('w')  # Set the entire GraphicsLayoutWidget background to white
        gh_layout.addWidget(win)                       # add plot to holder
        layout.addWidget(graph_holder)                 # add holder to page

        self.plot = win.addPlot(labels={"left": "angle (°)",
                                        "bottom": "time (s)"})
        self.plot.setYRange(*self.INIT_Y_MINMAX, padding=0)
        self.plot.showGrid(x=True, y=True, alpha=0.3)
        
        # Set text and axis colors to black for better visibility on white background
        self.plot.getAxis('left').setTextPen('k')  # Y-axis text in black
        self.plot.getAxis('bottom').setTextPen('k')  # X-axis text in black
        self.plot.getAxis('left').setPen('k')  # Y-axis line in black
        self.plot.getAxis('bottom').setPen('k')  # X-axis line in black
        
        self.curve = self.plot.plot(pen="r")

        # 2) Create Back button *with graph_holder as its parent* and
        #    position it manually.
        self.back_button = QPushButton("Back", graph_holder)
        self.back_button.setObjectName("back_button")   # Set object name for CSS styling
        self.back_button.setFixedSize(70, 28)          # optional – keeps it tidy
        self.back_button.move(675, 10)                  # 10 px from top-left
        self.back_button.raise_()                      # make sure it’s on top
        self.back_button.clicked.connect(self.go_back)

        # 3) Create floating trial info container positioned under the back button
        trial_container = QWidget(self)
        trial_container.setObjectName("TrialContainer")
        trial_container.setFixedSize(150, 60)
        trial_container.setStyleSheet("background-color: rgba(0, 36, 84, 0.8); border-radius: 8px;")
        
        # Add trial labels to the container
        trial_layout = QVBoxLayout(trial_container)
        trial_layout.setContentsMargins(8, 8, 8, 8)
        trial_layout.setSpacing(4)
        
        self.trial_label = QLabel("Current Trial: 0 / 4")
        self.trial_label.setStyleSheet("color: #FFFFFF; font: 600 14px 'Roboto'; background-color: transparent;")
        trial_layout.addWidget(self.trial_label)
        
        self.trial_counter = QLabel("Awaiting start...")
        self.trial_counter.setStyleSheet("color: #FFFFFF; font: 600 14px 'Roboto'; background-color: transparent;")
        trial_layout.addWidget(self.trial_counter)
        
        # Position the trial container under the back button area
        trial_container.move(628, 60)  # Same X as back button, below it
        trial_container.raise_()        # Ensure it's on top of the graph

        # 4) The rest of the controls stay in the main vertical layout
        self.record_button = QPushButton("Record")
        layout.addWidget(self.record_button)

        self.map_button = QPushButton("Map")
        layout.addWidget(self.map_button)

        self.clear_trial_file_button = QPushButton("Clear Trials")
        layout.addWidget(self.clear_trial_file_button)

        self.show_references_button = QPushButton("Show References")
        layout.addWidget(self.show_references_button)

        self.guess_samples_button = QPushButton("Guess Samples")
        layout.addWidget(self.guess_samples_button)

        # ── State Variables ───────────────────────
        self.data_t, self.data_deg = [], []
        self.t0, self.deg_filt = None, 0.0
        self.auto_scaled, self.settle_start = False, None
        self.recording, self.recorded_trial_data, self.record_start_time = False, [], None
        self.trial_index = 0

        # ── Load Trials ───────────────────────────
        self.load_trials()

        # ── Button Hooks ──────────────────────────
        self.record_button.clicked.connect(self.start_recording)
        self.map_button.clicked.connect(self.on_map_button)
        self.clear_trial_file_button.clicked.connect(self.clear_trial_file)
        self.back_button.clicked.connect(self.go_back)

        # ── Timer ─────────────────────────────────
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(self.TIMER_MS)
        
        # ── Shrinking Circle Animation ─────────────────────
        self.shrinking_circle = True  # Start with white screen
        self.circle_radius = 933  # Start with full screen coverage
        self.circle_center = QPointF(400, 240)  # Center of screen
        self.shrink_animation_timer = QTimer()
        self.shrink_animation_timer.timeout.connect(self.update_shrink_animation)
        self.shrink_animation_timer.setInterval(16)  # 60 FPS for smooth animation
        self.shrink_frames = 35  # Same speed as expanding circle (0.58 seconds)
        self.shrink_frame_count = 0
        
        # Don't create overlay here - wait until page is shown
        self.circle_overlay = None
        
        # ── Blue Transition Animation (Going Back) ─────────────────────
        self.blue_transition_timer = QTimer()
        self.blue_transition_timer.timeout.connect(self.update_blue_transition)
        self.blue_transition_timer.setInterval(16)  # 60 FPS for smooth animation
        self.blue_transition_frames = 30  # 0.5 seconds
        self.blue_transition_frame_count = 0
        self.blue_transition_active = False
        
        # Don't create blue overlay here - wait until needed
        self.blue_transition_overlay = None
        
        # Add a method to reset animation state
        self._reset_shrink_animation()
    
    def _reset_shrink_animation(self):
        """Reset the shrinking circle animation to initial state"""
        self.shrink_frame_count = 0
        self.shrinking_circle = True
        self.circle_radius = 933  # Full screen coverage
        if hasattr(self, 'shrink_animation_timer'):
            self.shrink_animation_timer.stop()
            
    def _reset_blue_transition(self):
        """Reset the blue transition animation to initial state"""
        self.blue_transition_frame_count = 0
        self.blue_transition_active = False
        if hasattr(self, 'blue_transition_timer'):
            self.blue_transition_timer.stop()
    
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

    def update_blue_transition(self):
        """Update the blue transition animation when going back"""
        self.blue_transition_frame_count += 1
        
        # Calculate progress (0.0 to 1.0)
        progress = min(self.blue_transition_frame_count / self.blue_transition_frames, 1.0)
        
        # Calculate radius based on progress - expand from center to fill screen
        max_radius = 933  # Full screen coverage
        self.blue_transition_radius = progress * max_radius
        
        # Update the blue overlay widget if it exists
        if self.blue_transition_overlay is not None:
            self.blue_transition_overlay.update_circle(self.blue_transition_radius)
            
            # Check if expansion is complete
            if self.blue_transition_frame_count >= self.blue_transition_frames:
                self.blue_transition_timer.stop()
                self.blue_transition_active = False
                
                # Now that the blue circle has filled the screen, emit the back signal
                # This will trigger the page transition to main menu
                self.back_requested.emit()

    def load_trials(self):
        if os.path.exists(self.TRIAL_FILE):
            with open(self.TRIAL_FILE, "r") as f:
                lines = f.readlines()
            self.trial_index = 0 if len(lines) >= self.MAX_TRIALS else len(lines)
        else:
            with open(self.TRIAL_FILE, "w") as f:
                f.write("")
        self.trial_label.setText(f"Current Trial: {self.trial_index} / {self.MAX_TRIALS}")

    def update(self):
        latest = None
        while self.ser.in_waiting:
            try:
                latest = float(self.ser.readline())
            except ValueError:
                continue
        if latest is None:
            return

        latest = 0.0 if abs(latest) < self.DEAD_ZONE else latest
        self.deg_filt = (1 - self.LPF_ALPHA) * self.deg_filt + self.LPF_ALPHA * latest

        now = time.time()
        if self.t0 is None:
            self.t0 = now
        self.data_t.append(now - self.t0)
        self.data_deg.append(self.deg_filt)

        self.curve.setData(self.data_t, self.data_deg)
        self.plot.setXRange(max(0, self.data_t[-1] - self.WINDOW_SECONDS), self.data_t[-1], padding=0)
        self.trial_label.setText(f"Current Trial: {self.trial_index} / {self.MAX_TRIALS}")

        if self.recording:
            seconds = int(now - self.record_start_time)
            self.trial_counter.setText(f"Seconds left: {10 - seconds}")
            if len(self.recorded_trial_data) < self.MAX_VALUES_PER_TRIAL:
                self.recorded_trial_data.append(self.deg_filt)
            if now - self.record_start_time >= self.RECORD_DURATION:
                self.stop_recording()
                
    def _full_reset(self):
        """Clear plot data and zero the clock (leave port open)."""

        self.data_t.clear()
        self.data_deg.clear()
        self.t0       = None
        self.deg_filt = 0.0
        self.curve.clear()

    def _resume_if_needed(self):
        """Called by showEvent – rearm everything when page is shown."""
        if not self.timer.isActive():
            self.ser.reset_input_buffer()    # drop whatever accumulated
            self._full_reset()               # fresh graph
            self.ser.write(b"\x01")          # AFM = 1  ➜ start stream
            self.ser.flush()
            self.timer.start(self.TIMER_MS)

    def start_recording(self):
        if self.trial_index >= self.MAX_TRIALS:
            return
        self.recording = True
        self.recorded_trial_data = []
        self.record_start_time = time.time()

    def stop_recording(self):
        self.recording = False
        with open(self.TRIAL_FILE, "a") as f:
            f.write(",".join(f"{v:.4f}" for v in self.recorded_trial_data) + "\n")
        self.trial_index += 1

    def clear_trial_file(self):
        with open(self.TRIAL_FILE, "w") as f:
            f.write("")
        self.trial_index = 0

    def on_map_button(self):
        """User pressed 'Map' → tell MainWindow to flip pages."""
        self.map_requested.emit()

    def showEvent(self, event):
        self._resume_if_needed()
        super().showEvent(event)
        
        # Always reset and recreate the overlays when the page is shown
        # This ensures the animations work every time
        
        # Clean up existing white shrinking overlay
        if self.circle_overlay is not None:
            self.circle_overlay.deleteLater()
            self.circle_overlay = None
            
        # Clean up existing blue transition overlay (from previous visits)
        if hasattr(self, 'blue_transition_overlay') and self.blue_transition_overlay is not None:
            self.blue_transition_overlay.deleteLater()
            self.blue_transition_overlay = None
        
        # Create fresh white shrinking overlay
        self.circle_overlay = CircleOverlay(self)
        self.circle_overlay.setFixedSize(800, 480)
        self.circle_overlay.move(0, 0)  # Position at top-left corner
        self.circle_overlay.raise_()  # Ensure it's on top of everything
        self.circle_overlay.show()  # Explicitly show the overlay
        
        # Reset animation state and start the shrinking animation
        self._reset_shrink_animation()
        self._reset_blue_transition()  # Also reset blue transition state
        self.shrink_animation_timer.start()

    def go_back(self):
        """User hit Back -> start blue transition animation, then switch to menu."""
        # Stop the data stream and reset
        self.timer.stop()
        self.ser.write(b"\x00")          # MAIN_MENU  = 0  ➜ pause Arduino
        self.ser.flush()
        self._full_reset()
        
        # Clean up shrinking animation state
        if self.circle_overlay is not None:
            self.shrink_animation_timer.stop()
            self.circle_overlay.hide()
            
        # Clean up blue transition animation state
        if hasattr(self, 'blue_transition_timer'):
            self.blue_transition_timer.stop()
        if hasattr(self, 'blue_shrinking_timer'):
            self.blue_shrinking_timer.stop()
        
        # Start the blue transition animation
        self._start_blue_transition()
        
    def _start_blue_transition(self):
        """Start the blue circle expansion animation when going back"""
        # Create the blue transition overlay
        self.blue_transition_overlay = BlueTransitionOverlay(self)
        self.blue_transition_overlay.setFixedSize(800, 480)
        self.blue_transition_overlay.move(0, 0)  # Position at top-left corner
        self.blue_transition_overlay.raise_()  # Ensure it's on top of everything
        self.blue_transition_overlay.show()  # Show the overlay
        
        # Reset animation state
        self.blue_transition_frame_count = 0
        self.blue_transition_active = True
        
        # Activate the blue overlay
        self.blue_transition_overlay.set_animation_state(True)
        
        # Start the animation timer
        self.blue_transition_timer.start()

    def closeEvent(self, event):
        super().closeEvent(event)