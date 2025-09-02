from pathlib import Path
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore    import Qt, QSize, pyqtSignal, QTimer
from PyQt6.QtGui     import QIcon, QCursor
import serial
import time

PROJECT_ROOT = Path(__file__).resolve().parent.parent
IMAGES_DIR   = Path("Images")
STYLES_DIR   = PROJECT_ROOT / "Styles"


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

        title_lbl = QLabel(title, alignment=Qt.AlignmentFlag.AlignCenter)
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


class SpringDampenerPageWidget(QWidget):
    """Spring Dampener Tuning page with adjustable parameters."""
    back_requested = pyqtSignal()

    def __init__(self, serial_connection=None, parent=None):
        super().__init__(parent)

        self.serial_connection = serial_connection
        self.data_collection_active = False
        self.swing_data = []
        
        # Add safety mechanism to prevent rapid button clicking
        self.last_test_time = 0
        self.min_test_interval = 0.5  # Minimum 2 seconds between test commands

        self.setObjectName("SpringDampenerPage")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        root = QVBoxLayout(self)

        # Add yellow title at the very top center
        title = QLabel("Spring Dampener Tuning")
        title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        title.setObjectName("Title")
        root.addWidget(title)

        # Picker controls
        row = QHBoxLayout(); row.setSpacing(40)

        self.spring_picker = Picker("Spring Constant", 0.0, 50.0, is_float=True)
        self.damping_picker = Picker("Damping Gain", 0, 50, is_float=False)

        # Wire pickers to handle value changes
        self.spring_picker.value_added.connect(self._send_spring_constant)
        self.damping_picker.value_added.connect(self._send_damping_gain)

        row.addStretch(1)
        row.addWidget(self.spring_picker)
        row.addWidget(self.damping_picker)
        row.addStretch(1)

        # Create a vertical layout for the Test Parameters button
        button_column = QVBoxLayout()
        button_column.setSpacing(8)  # Small spacing between buttons
        
        test_btn = QPushButton("Test Parameters")
        test_btn.setObjectName("TestBtn")
        test_btn.clicked.connect(self._send_test_parameters)
        button_column.addWidget(test_btn, alignment=Qt.AlignmentFlag.AlignHCenter)
        
        # Add Graph Data button
        graph_btn = QPushButton("Graph Swing Data")
        graph_btn.setObjectName("GraphBtn")
        graph_btn.clicked.connect(self._graph_swing_data)
        button_column.addWidget(graph_btn, alignment=Qt.AlignmentFlag.AlignHCenter)
        
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
        css_file = STYLES_DIR / "styleSpringDampenerPage.qss"
        if css_file.exists():
            self.setStyleSheet(css_file.read_text())
        else:
            # Fallback styling if CSS file doesn't exist
            self.setStyleSheet("""
                QWidget#SpringDampenerPage {
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
                QPushButton#TestBtn {
                    font: 600 18px 'Roboto';
                    color: #FFFFFF;
                    background-color: rgba(255,255,255,0.05);
                    border: 2px solid #FAC01A;
                    border-radius: 8px;
                    padding: 12px 24px;
                    min-width: 200px;
                }
                QPushButton#TestBtn:hover {
                    background-color: rgba(255,255,255,0.10);
                }
                QPushButton#GraphBtn {
                    font: 600 18px 'Roboto';
                    color: #FFFFFF;
                    background-color: rgba(255,255,255,0.05);
                    border: 2px solid #FAC01A;
                    border-radius: 8px;
                    padding: 12px 24px;
                    min-width: 200px;
                }
                QPushButton#GraphBtn:hover {
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

    # Serial communication helpers
    def _write(self, text: str):
        """Low-level send. Falls back to console print when no port present."""
        if self.serial_connection is None:
            print("→", text.strip())
            return
        self.serial_connection.write(text.encode())
        self.serial_connection.flush()

    def _send_spring_constant(self, value: str):
        self._write(f"K{value}\n")

    def _send_damping_gain(self, value: str):
        self._write(f"D{value}\n")

    def _send_test_parameters(self):
        # Safety check: prevent rapid button clicking
        current_time = time.time()
        if current_time - self.last_test_time < self.min_test_interval:
            return  # Ignore rapid clicks
        
        self.last_test_time = current_time
        
        # CRITICAL: Clear serial buffer before sending test command
        if self.serial_connection:
            try:
                self.serial_connection.reset_input_buffer()
            except:
                pass
        
        self._write("Q\n")
        # Start collecting swing data
        self._start_data_collection()
        
    def _graph_swing_data(self):
        """Read swing data from file and create a graph"""
        try:
            # Check if swingData.txt exists
            if not Path("swingData.txt").exists():
                return
                
            # Read the data
            data = []
            with open("swingData.txt", "r") as f:
                for line in f:
                    if line.strip() and "," in line:
                        try:
                            time_val, position_val = line.strip().split(",")
                            data.append((float(time_val), float(position_val)))
                        except ValueError:
                            continue
            
            if not data:
                return
                
            # Create the graph
            self._create_swing_graph(data)
            
        except Exception:
            pass
    
    def _create_swing_graph(self, data):
        """Create and display a graph overlay on the screen"""
        try:
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
            from matplotlib.figure import Figure
            
            # Create overlay widget
            self.graph_overlay = QWidget(self)
            self.graph_overlay.setGeometry(0, 0, 800, 480)  # Full screen size
            self.graph_overlay.setStyleSheet("""
                QWidget {
                    background-color: #002454;
                    border: 2px solid #FAC01A;
                }
            """)
            
            # Create layout for overlay
            overlay_layout = QVBoxLayout(self.graph_overlay)
            overlay_layout.setContentsMargins(20, 20, 20, 20)
            
            # Create title
            title_label = QLabel("Swing Response: Position vs Time")
            title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            title_label.setStyleSheet("""
                QLabel {
                    color: #FAC01A;
                    font: 600 24px 'Roboto';
                    margin-bottom: 10px;
                    background-color: transparent;
                    border: none;
                }
            """)
            overlay_layout.addWidget(title_label)
            
            # Create matplotlib figure with dark theme
            fig = Figure(figsize=(8, 5), facecolor='#002454')
            ax = fig.add_subplot(111, facecolor='#002454')
            
            # Extract time and position data
            times = [point[0] for point in data]
            positions = [point[1] for point in data]
            
            # Plot the data with yellow line to match theme
            ax.plot(times, positions, '#FAC01A', linewidth=3, label='Position')
            ax.set_xlabel('Time (seconds)', color='white', fontsize=12)
            ax.set_ylabel('Position (degrees)', color='white', fontsize=12)
            ax.grid(True, alpha=0.3, color='white')
            ax.legend(facecolor='#002454', edgecolor='#FAC01A', labelcolor='white')
            
            # Style the axes
            ax.tick_params(colors='white')
            ax.spines['bottom'].set_color('white')
            ax.spines['top'].set_color('white') 
            ax.spines['right'].set_color('white')
            ax.spines['left'].set_color('white')
            
            # Add canvas to overlay
            canvas = FigureCanvas(fig)
            canvas.setStyleSheet("background-color: transparent; border: none;")
            overlay_layout.addWidget(canvas)
            
            # Create back button
            back_button = QPushButton("Back")
            back_button.setObjectName("GraphBackBtn")
            back_button.setStyleSheet("""
                QPushButton#GraphBackBtn {
                    font: 600 18px 'Roboto';
                    color: #FFFFFF;
                    background-color: rgba(255,255,255,0.05);
                    border: 2px solid #FAC01A;
                    border-radius: 8px;
                    padding: 12px 24px;
                    min-width: 200px;
                    max-width: 200px;
                }
                QPushButton#GraphBackBtn:hover {
                    background-color: rgba(255,255,255,0.10);
                }
            """)
            back_button.clicked.connect(self._close_graph_overlay)
            overlay_layout.addWidget(back_button, alignment=Qt.AlignmentFlag.AlignCenter)
            
            # Show the overlay
            self.graph_overlay.show()
            self.graph_overlay.raise_()
            
        except ImportError:
            pass
        except Exception:
            pass
    
    def _close_graph_overlay(self):
        """Close the graph overlay"""
        if hasattr(self, 'graph_overlay') and self.graph_overlay:
            self.graph_overlay.hide()
            self.graph_overlay.deleteLater()
            self.graph_overlay = None
    
    def _start_data_collection(self):
        """Start collecting swing data from serial"""
        self.data_collection_active = True
        self.swing_data = []
        self.last_data_time = time.time()
        
        # Set up a timer to check for incoming data
        if hasattr(self, 'data_timer'):
            self.data_timer.stop()
        
        self.data_timer = QTimer()
        self.data_timer.timeout.connect(self._check_serial_data)
        self.data_timer.start(100)  # Check every 100ms
        
        # Set up auto-save timer (saves data if no new data received for 5 seconds)
        if hasattr(self, 'auto_save_timer'):
            self.auto_save_timer.stop()
        
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self._check_auto_save)
        self.auto_save_timer.start(1000)  # Check every 1 second
    
    def _check_serial_data(self):
        """Check for incoming serial data and collect swing position data"""
        if not self.data_collection_active:
            return
            
        if not self.serial_connection:
            return
            
        try:
            # Check if data is available
            if self.serial_connection.in_waiting > 0:
                # Add timeout to prevent blocking
                line = self.serial_connection.readline().decode('utf-8', errors='ignore').strip()
                
                # Check for start signal
                if line == "DATA_START":
                    self.swing_data = []  # Clear any previous data
                    return
                
                # Check for end signal
                if line == "DATA_END":
                    self._stop_data_collection()
                    return
                
                # Look for CSV format data (time,position) - skip header
                if ',' in line and not line.startswith('time') and line != "time,position":
                    try:
                        parts = line.split(',')
                        if len(parts) == 2:
                            time_val = parts[0].strip()
                            position_val = parts[1].strip()
                            time_float = float(time_val)
                            position_float = float(position_val)
                            
                            # Store the data point
                            self.swing_data.append((time_float, position_float))
                            self.last_data_time = time.time()
                            
                    except ValueError:
                        pass
                        
        except Exception:
            pass
    
    def _check_auto_save(self):
        """Check if we should auto-save data after no new data for 5 seconds"""
        if not self.data_collection_active:
            return
            
        time_since_last_data = time.time() - self.last_data_time
        
        # If we have data and no new data for 5 seconds, auto-save
        if self.swing_data and time_since_last_data > 5.0:
            self._stop_data_collection()
    
    def _stop_data_collection(self):
        """Stop collecting data and save to file"""
        self.data_collection_active = False
        
        if hasattr(self, 'data_timer'):
            self.data_timer.stop()
        if hasattr(self, 'auto_save_timer'):
            self.auto_save_timer.stop()
        
        # Save collected data to swingData.txt
        if self.swing_data:
            try:
                with open("swingData.txt", "w") as f:
                    f.write("time,position\n")
                    for time_val, position_val in self.swing_data:
                        f.write(f"{time_val:.3f},{position_val:.3f}\n")
                
            except Exception:
                pass

    def showEvent(self, event):
        """Called when Spring Dampener page is shown"""
        super().showEvent(event)
        # Stop any existing data collection when page is shown
        if hasattr(self, 'data_collection_active') and self.data_collection_active:
            self._stop_data_collection()
        
        # CRITICAL: Clear any pending serial data from previous pages
        if self.serial_connection:
            try:
                self.serial_connection.reset_input_buffer()
                self.serial_connection.reset_output_buffer()
            except:
                pass

    def go_back(self):
        self.back_requested.emit()