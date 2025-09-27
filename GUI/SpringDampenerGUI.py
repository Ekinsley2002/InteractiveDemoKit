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

        # Animation state tracking
        self.animation_in_progress = False

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
        
        # Store button references for enable/disable functionality
        self.all_buttons = [
            self.spring_picker.up_btn if hasattr(self.spring_picker, 'up_btn') else None,
            self.spring_picker.down_btn if hasattr(self.spring_picker, 'down_btn') else None,
            self.spring_picker.add_btn if hasattr(self.spring_picker, 'add_btn') else None,
            self.damping_picker.up_btn if hasattr(self.damping_picker, 'up_btn') else None,
            self.damping_picker.down_btn if hasattr(self.damping_picker, 'down_btn') else None,
            self.damping_picker.add_btn if hasattr(self.damping_picker, 'add_btn') else None,
            test_btn,
            graph_btn,
            back_btn
        ]
        # Filter out None values
        self.all_buttons = [btn for btn in self.all_buttons if btn is not None]

    # Serial communication helpers
    def _write(self, text: str):
        """Low-level send. Falls back to console print when no port present."""
        if self.serial_connection is None:
            print("→", text.strip())
            return
        self.serial_connection.write(text.encode())
        self.serial_connection.flush()

    def _send_spring_constant(self, value: str):
        if self.animation_in_progress:
            return
        self._write(f"K{value}\n")

    def _send_damping_gain(self, value: str):
        if self.animation_in_progress:
            return
        self._write(f"D{value}\n")

    def _send_test_parameters(self):
        if self.animation_in_progress:
            print("Test Parameters button pressed but animation in progress")  # Debug
            return
        # Safety check: prevent rapid button clicking
        current_time = time.time()
        if current_time - self.last_test_time < self.min_test_interval:
            print("Test Parameters button pressed too quickly, ignoring")  # Debug
            return  # Ignore rapid clicks
        
        print("Test Parameters button pressed - sending Q command")  # Debug
        self.last_test_time = current_time
        
        # CRITICAL: Clear serial buffer before sending test command
        if self.serial_connection:
            try:
                self.serial_connection.reset_input_buffer()
                print("Serial buffer cleared")  # Debug
            except Exception as e:
                print(f"Error clearing serial buffer: {e}")  # Debug
        
        self._write("Q\n")
        print("Sent Q command to Arduino")  # Debug
        # Start collecting swing data
        self._start_data_collection()
        
    def _graph_swing_data(self):
        """Read swing data from file and create a graph"""
        if self.animation_in_progress:
            print("Graph button pressed but animation in progress")  # Debug
            return
        
        print("Graph button pressed - checking for data...")  # Debug
        
        try:
            # Check if swingData.txt exists (try both current directory and project root)
            swing_data_file = Path("swingData.txt")
            if not swing_data_file.exists():
                # Try project root directory
                swing_data_file = Path(__file__).parent.parent / "swingData.txt"
                if not swing_data_file.exists():
                    print("swingData.txt file does not exist in current directory or project root")  # Debug
                return
            
            print(f"swingData.txt exists at: {swing_data_file.absolute()}")  # Debug
                
            # Read the data
            data = []
            with open(swing_data_file, "r") as f:
                for line_num, line in enumerate(f, 1):
                    if line.strip() and "," in line:
                        try:
                            time_val, position_val = line.strip().split(",")
                            data.append((float(time_val), float(position_val)))
                        except ValueError:
                            print(f"Error parsing line {line_num}: {line.strip()}")  # Debug
                            continue
            
            print(f"Read {len(data)} data points from file")  # Debug
            
            if not data:
                print("No valid data found in file")  # Debug
                return
                
            print("Creating graph...")  # Debug
            # Create the graph
            self._create_swing_graph(data)
            
        except Exception as e:
            print(f"Error in _graph_swing_data: {e}")  # Debug
    
    def _create_swing_graph(self, data):
        """Create and display a professional step response graph for PID analysis"""
        print(f"Creating professional step response graph with {len(data)} data points")  # Debug
        try:
            # Set matplotlib backend for PyQt6
            import matplotlib
            matplotlib.use('Qt5Agg')  # Use Qt5Agg backend for PyQt6 compatibility
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
            from matplotlib.figure import Figure
            import numpy as np
            
            print("Matplotlib imports successful")  # Debug
            
            # Clean up any existing graph overlay
            if hasattr(self, 'graph_overlay') and self.graph_overlay:
                print("Cleaning up existing graph overlay")  # Debug
                self.graph_overlay.hide()
                self.graph_overlay.deleteLater()
                self.graph_overlay = None
            
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
            overlay_layout.setContentsMargins(10, 10, 10, 10)
            
            # Create title and metrics layout
            title_metrics_layout = QHBoxLayout()
            
            # Create simple title
            title_label = QLabel("Swing Analysis")
            title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            title_label.setStyleSheet("""
                QLabel {
                    color: #FAC01A;
                    font: 600 20px 'Roboto';
                    margin-bottom: 2px;
                    background-color: transparent;
                    border: none;
                }
            """)
            
            # Create metrics box (will be populated with data later)
            self.metrics_label = QLabel("Key Metrics:\nOvershoot: --\nSettling Time: --")
            self.metrics_label.setStyleSheet("""
                QLabel {
                    color: white;
                    font: 600 11px 'Roboto';
                    background-color: #002454;
                    border: 2px solid #FAC01A;
                    border-radius: 6px;
                    padding: 6px;
                    min-width: 130px;
                    max-width: 130px;
                }
            """)
            self.metrics_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            
            # Add title and metrics to horizontal layout
            title_metrics_layout.addWidget(title_label, 1)  # Title takes most space
            title_metrics_layout.addWidget(self.metrics_label, 0)  # Metrics takes minimal space
            
            overlay_layout.addLayout(title_metrics_layout)
            
            # Create matplotlib figure with dark theme
            fig = Figure(figsize=(9.5, 5.5), facecolor='#002454')
            fig.subplots_adjust(bottom=0.12, left=0.12, right=0.95, top=0.95)  # Add margins for labels
            ax = fig.add_subplot(111, facecolor='#002454')
            
            # Extract time and position data
            times = np.array([point[0] for point in data])
            positions = np.array([point[1] for point in data])
            
            if len(times) > 0 and len(positions) > 0:
                # Clean and sort the data for linear presentation
                data_pairs = list(zip(times, positions))
                data_pairs.sort(key=lambda x: x[0])  # Sort by time
                times_clean = np.array([pair[0] for pair in data_pairs])
                positions_clean = np.array([pair[1] for pair in data_pairs])
                
                # Calculate analysis parameters
                initial_pos = positions_clean[0]
                final_pos = positions_clean[-1]
                max_pos = np.max(positions_clean)
                min_pos = np.min(positions_clean)
                
                # Detect swing endpoints by analyzing position changes
                # Look for significant changes in position to identify swing transitions
                position_diff = np.diff(positions_clean)
                significant_changes = np.abs(position_diff) > (np.std(position_diff) * 2)
                
                # Find swing endpoints (where significant position changes occur)
                swing_endpoints = []
                if len(significant_changes) > 0:
                    # Find indices where significant changes occur
                    change_indices = np.where(significant_changes)[0]
                    
                    # Add the first significant change as a potential swing endpoint
                    if len(change_indices) > 0:
                        swing_endpoints.append((times_clean[change_indices[0]], positions_clean[change_indices[0]]))
                    
                    # Look for the end of the swing (where position stabilizes)
                    # Find where the position stops changing significantly for a while
                    stable_window = 10  # Look for stability over 10 data points
                    if len(positions_clean) > stable_window:
                        for i in range(len(positions_clean) - stable_window):
                            window_positions = positions_clean[i:i+stable_window]
                            if np.std(window_positions) < 0.5:  # Position is stable
                                swing_endpoints.append((times_clean[i+stable_window//2], positions_clean[i+stable_window//2]))
                                break
                
                # If no swing endpoints detected, use the end of data as the swing end
                if len(swing_endpoints) == 0:
                    swing_endpoints.append((times_clean[-1], positions_clean[-1]))
                
                # Calculate overshoot percentage (for step response)
                if abs(final_pos - initial_pos) > 1.0:  # Only calculate if there's significant movement
                    step_size = abs(final_pos - initial_pos)
                    
                    if final_pos > initial_pos:  # Positive step (moving up)
                        # For positive step, overshoot is how much we go above the final value
                        if max_pos > final_pos:
                            overshoot = ((max_pos - final_pos) / step_size) * 100
                        else:
                            overshoot = 0
                    else:  # Negative step (moving down)
                        # For negative step, overshoot is how much we go below the final value
                        if min_pos < final_pos:
                            overshoot = ((final_pos - min_pos) / step_size) * 100
                        else:
                            overshoot = 0
                else:
                    overshoot = 0
                
                # Plot the clean step response with markers for data points
                ax.plot(times_clean, positions_clean, '#FAC01A', linewidth=3, 
                       marker='o', markersize=4, markevery=5, label='System Response', zorder=3)
                
                # Add swing endpoint indicators
                if len(swing_endpoints) > 0:
                    # Mark the first swing endpoint (start of significant movement)
                    first_endpoint_time, first_endpoint_pos = swing_endpoints[0]
                    ax.axvline(x=first_endpoint_time, color='#FF6B6B', linestyle='-', alpha=0.8, linewidth=2)
                    ax.text(first_endpoint_time, ax.get_ylim()[1] * 0.95, 'Swing Start', 
                           rotation=90, ha='right', va='top', color='#FF6B6B', fontsize=10, fontweight='bold',
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='#002454', edgecolor='#FF6B6B', alpha=0.8))
                
                # Mark the final swing endpoint (where swing ends/stabilizes)
                final_endpoint_time, final_endpoint_pos = swing_endpoints[-1]
                ax.axvline(x=final_endpoint_time, color='#4ECDC4', linestyle='-', alpha=0.8, linewidth=2)
                ax.text(final_endpoint_time, ax.get_ylim()[1] * 0.85, 'Swing End', 
                       rotation=90, ha='right', va='top', color='#4ECDC4', fontsize=10, fontweight='bold',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='#002454', edgecolor='#4ECDC4', alpha=0.8))
                
                # Add reference lines for analysis
                if abs(final_pos - initial_pos) > 1.0:
                    # Final value line (target)
                    ax.axhline(y=final_pos, color='#FF6B6B', linestyle='--', alpha=0.8, linewidth=2, label='Target')
                    
                    # Initial value line (starting position)
                    ax.axhline(y=initial_pos, color='#4ECDC4', linestyle='--', alpha=0.8, linewidth=2, label='Start')
                    
                    # Overshoot line (shows the extreme point)
                    if overshoot > 0:
                        if final_pos > initial_pos:  # Positive step
                            ax.axhline(y=max_pos, color='#FFE66D', linestyle=':', alpha=0.6, linewidth=1, label='Overshoot')
                        else:  # Negative step
                            ax.axhline(y=min_pos, color='#FFE66D', linestyle=':', alpha=0.6, linewidth=1, label='Overshoot')
                
                # Enhanced styling for professional appearance
                ax.set_xlabel('Time (seconds)', color='white', fontsize=14, fontweight='bold')
                ax.set_ylabel('Position (degrees)', color='white', fontsize=14, fontweight='bold')
                
                # Professional grid
                ax.grid(True, alpha=0.3, color='white', linestyle='-', linewidth=0.5)
                ax.set_axisbelow(True)
                
                # Style the axes
                ax.tick_params(colors='white', labelsize=12)
                ax.spines['bottom'].set_color('white')
                ax.spines['top'].set_color('white') 
                ax.spines['right'].set_color('white')
                ax.spines['left'].set_color('white')
                
                # Update the metrics label with calculated values
                metrics_text = f"""Key Metrics:
Overshoot: {overshoot:.1f}%
Settling Time: {times_clean[-1]:.1f}s"""
                self.metrics_label.setText(metrics_text)
                
                # Compact professional legend
                legend = ax.legend(loc='upper right', facecolor='#002454', edgecolor='#FAC01A', 
                                    labelcolor='white', framealpha=0.9, fontsize=7, 
                                    markerscale=0.8, handlelength=1.5, handletextpad=0.5)
                legend.get_frame().set_linewidth(1.5)
                
                # Set clean axis limits
                time_range = times_clean[-1] - times_clean[0]
                pos_range = max_pos - min_pos
                
                ax.set_xlim(times_clean[0] - time_range * 0.02, times_clean[-1] + time_range * 0.02)
                ax.set_ylim(min_pos - pos_range * 0.05, max_pos + pos_range * 0.05)
                
                # Set nice tick intervals
                ax.xaxis.set_major_locator(plt.MaxNLocator(nbins=8))
                ax.yaxis.set_major_locator(plt.MaxNLocator(nbins=6))
            
            # Add canvas to overlay
            canvas = FigureCanvas(fig)
            canvas.setStyleSheet("background-color: transparent; border: none;")
            overlay_layout.addWidget(canvas)
            
            # Create back button
            back_button = QPushButton("Back")
            back_button.setObjectName("GraphBackBtn")
            back_button.setStyleSheet("""
                QPushButton#GraphBackBtn {
                    font: 600 16px 'Roboto';
                    color: #FFFFFF;
                    background-color: rgba(255,255,255,0.05);
                    border: 2px solid #FAC01A;
                    border-radius: 6px;
                    padding: 8px 20px;
                    min-width: 150px;
                    max-width: 150px;
                }
                QPushButton#GraphBackBtn:hover {
                    background-color: rgba(255,255,255,0.10);
                }
            """)
            back_button.clicked.connect(self._close_graph_overlay)
            overlay_layout.addWidget(back_button, alignment=Qt.AlignmentFlag.AlignCenter)
            
            # Show the overlay
            print("Showing professional step response graph")  # Debug
            self.graph_overlay.show()
            self.graph_overlay.raise_()
            print("Professional graph overlay displayed successfully")  # Debug
            
        except ImportError as e:
            print(f"Import error creating graph: {e}")  # Debug
        except Exception as e:
            print(f"Error creating graph: {e}")  # Debug
    
    def _close_graph_overlay(self):
        """Close the graph overlay"""
        if hasattr(self, 'graph_overlay') and self.graph_overlay:
            self.graph_overlay.hide()
            self.graph_overlay.deleteLater()
            self.graph_overlay = None
    
    def _start_data_collection(self):
        """Start collecting swing data from serial"""
        print("Starting data collection...")  # Debug
        self.data_collection_active = True
        self.swing_data = []
        self.last_data_time = time.time()
        
        # Set up a timer to check for incoming data
        if hasattr(self, 'data_timer'):
            self.data_timer.stop()
        
        self.data_timer = QTimer()
        self.data_timer.timeout.connect(self._check_serial_data)
        self.data_timer.start(100)  # Check every 100ms
        print("Data collection timer started (checking every 100ms)")  # Debug
        
        # Set up auto-save timer (saves data if no new data received for 5 seconds)
        if hasattr(self, 'auto_save_timer'):
            self.auto_save_timer.stop()
        
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self._check_auto_save)
        self.auto_save_timer.start(1000)  # Check every 1 second
        print("Auto-save timer started (checking every 1s)")  # Debug
    
    def _check_serial_data(self):
        """Check for incoming serial data and collect swing position data"""
        if not self.data_collection_active:
            return
            
        if not self.serial_connection:
            print("No serial connection available")  # Debug
            return
            
        try:
            # Check if data is available
            if self.serial_connection.in_waiting > 0:
                # Add timeout to prevent blocking
                line = self.serial_connection.readline().decode('utf-8', errors='ignore').strip()
                
                # Debug: print ALL received lines to see what's coming in
                print(f"Received: '{line}'")
                
                # Check for start signal
                if line == "DATA_START":
                    self.swing_data = []  # Clear any previous data
                    self.last_data_time = time.time()  # Reset timer
                    print("Data collection started")  # Debug
                    return
                
                # Check for end signal
                if line == "DATA_END":
                    print(f"Data collection ended with {len(self.swing_data)} points")  # Debug
                    self._stop_data_collection()
                    return
                
                # Look for CSV format data (time,position) - skip header and empty lines
                if ',' in line and not line.startswith('time') and line != "time,position" and line.strip():
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
                            print(f"Stored data point: {time_float}, {position_float}")  # Debug
                            
                    except ValueError as e:
                        print(f"Error parsing data line: {line}, error: {e}")  # Debug
                        
        except Exception as e:
            print(f"Serial communication error: {e}")  # Debug
    
    def _check_auto_save(self):
        """Check if we should auto-save data after no new data for 10 seconds"""
        if not self.data_collection_active:
            return
            
        time_since_last_data = time.time() - self.last_data_time
        
        # If we have data and no new data for 10 seconds, auto-save (longer timeout for longer tests)
        if self.swing_data and time_since_last_data > 10.0:
            print(f"Auto-saving data after timeout with {len(self.swing_data)} points")  # Debug
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
                # Save to project root directory
                swing_data_file = Path(__file__).parent.parent / "swingData.txt"
                with open(swing_data_file, "w") as f:
                    f.write("time,position\n")
                    for time_val, position_val in self.swing_data:
                        f.write(f"{time_val:.3f},{position_val:.3f}\n")
                print(f"Saved {len(self.swing_data)} data points to {swing_data_file.absolute()}")  # Debug
            except Exception as e:
                print(f"Error saving data: {e}")  # Debug
        else:
            print("No data to save")  # Debug

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

    def go_back(self):
        if self.animation_in_progress:
            return
        # Send MAIN_MENU command to Arduino to reset it from AFM mode
        self.serial_connection.write(b"M\n")
        self.serial_connection.flush()
        self.back_requested.emit()