# Interactive Demo Kit

## Overview

The Interactive Demo Kit is a sophisticated PyQt6-based application designed for educational demonstrations and interactive control of Arduino-based hardware systems. The application features a modern, animated interface with multiple specialized pages for different types of experiments and demonstrations.

### Key Features
- **Multi-Page Interface**: AFM, Power Pong, Spring Dampener, Haptic Feedback, and Topography pages
- **Real-time Serial Communication**: Direct Arduino control and data collection
- **Professional Animations**: Smooth transitions, circle overlays, and sprite-based animations
- **Data Visualization**: Real-time graphing and data export capabilities
- **Cross-Platform Support**: Windows, Mac, and Linux compatibility
- **Responsive Design**: Fixed 800x480 resolution optimized for touch interfaces

## Architecture

The application follows a modular architecture with clear separation of concerns:

```
InteractiveDemoKit/
├── main.py                 # Application entry point and page router
├── Config.py              # Configuration settings
├── GUI/                   # User interface pages
├── Animation/             # Animation and transition logic
├── Control/               # Arduino control files
├── Styles/                # Qt Style Sheets (QSS)
├── Images/                # Static image assets
└── trials.txt             # Data storage file
```

## Core Components

### 1. Main Application (`main.py`)

**Purpose**: Central application controller and page router

**Key Functions**:
- Serial communication setup (Arduino interface)
- Page navigation management
- Startup animation coordination
- Cross-platform device detection

**Configurable Parameters**:
```python
self.BAUD = 115_200        # Serial communication baud rate
self.PORT = "COM4"         # Serial port (auto-detected by platform)
```

**Platform Support**:
- **Windows**: `COM4` (configurable)
- **Mac**: `/dev/cu.usbmodem14101`
- **Linux**: `/dev/ttyACM0` (fullscreen mode)

### 2. Configuration (`Config.py`)

**Purpose**: Centralized configuration management

**Settings**:
```python
BOARDLESS = False          # Set to True for testing without hardware
DEVICE = "Windows"         # Platform: Mac, Linux, Windows
DEV_MODE = True            # Development mode (escape button visibility)
```

## GUI Pages

### Main Menu (`GUI/MainMenuGUI.py`)

**Purpose**: Central navigation hub with animated transitions

**Features**:
- Animated button layout with consistent spacing
- White circle reveal animation when returning from other pages
- Responsive button sizing (automatically adjusts for 4 buttons)

**Customizable Elements**:
- Button spacing: Modify `lay.addSpacing()` values
- Button styling: Edit `Styles/styleMainPage.qss`
- Animation timing: Adjust `shrink_frames` and timer intervals

### AFM Page (`GUI/AfmGUI.py`)

**Purpose**: Atomic Force Microscope demonstration interface

**Features**:
- Blue circle collapse animation on startup
- Blue circle expansion animation when returning to main menu
- Real-time data visualization

**Serial Commands**:
- **Enter**: Sends `\x01` (byte value 1)
- **Exit**: Sends `\x00` (byte value 0)

### Power Pong Page (`GUI/PowerPongGUI.py`)

**Purpose**: Interactive Power Pong game with physics simulation

**Features**:
- Real-time ball physics with gravity and collision detection
- Adjustable speed and offset parameters
- Paddle hitting animations with configurable timing
- White circle transitions (startup and return)

**Serial Commands**:
- **Enter**: Sends `\x02` (byte value 2)
- **Speed**: Sends `T {value}\n` format
- **Offset**: Sends `R {value}\n` format
- **FORE**: Sends `M\n`

**Adjustable Parameters**:
```python
paddle_hit_drop_distance = 40      # Paddle drop distance in pixels
paddle_hit_rotation_angle = 20     # Rotation angle in degrees
paddle_hit_animation_speed = 14    # Animation speed (frames)
paddle_hit_trigger_distance = 140  # Distance to trigger swing
first_swing_delay_frames = 35      # Delay before first swing
```

### Spring Dampener Page (`GUI/SpringDampenerGUI.py`)

**Purpose**: Spring-dampener system tuning and data collection

**Features**:
- Real-time parameter adjustment (Spring Constant, Damping Gain)
- Automatic data collection during swing tests
- Professional data visualization with matplotlib
- Auto-save functionality (5-second timeout)

**Serial Commands**:
- **Enter**: Sends `\x04` (byte value 4)
- **Exit**: Sends `\x00` (byte value 0)
- **Spring Constant**: Sends `K{value}\n` (e.g., `K12.5\n`)
- **Damping Gain**: Sends `D{value}\n` (e.g., `D0\n`)
- **Test Parameters**: Sends `T\n`

**Data Collection**:
- **Auto-start**: Begins when "Test Parameters" button is pressed
- **Auto-save**: Saves to `swingData.txt` after 5 seconds of no new data
- **Format**: CSV with `time,position` columns
- **Graphing**: Full-screen overlay with professional styling

**Customizable Parameters**:
```python
# Picker ranges
Spring Constant: 0.0 to 50.0 (0.1 increments)
Damping Gain: 0 to 50 (1 increments)

# Auto-save timing
Auto-save timeout: 5 seconds (configurable in `_check_auto_save`)
Data collection frequency: 100ms (configurable in `_start_data_collection`)
```

### Haptic Feedback Page (`GUI/HapticFeedbackGUI.py`)

**Purpose**: Haptic feedback demonstration interface

**Features**:
- Basic placeholder interface
- Consistent styling with other pages
- Back navigation to main menu

### Topography Page (`GUI/TopographyGUI.py`)

**Purpose**: Topography data visualization

**Features**:
- Data loading from `trials.txt`
- Wave visualization with probe interaction
- Real-time distance calculations

## Animation System

### Startup Animation (`Animation/StartupAnimation.py`)

**Purpose**: Application launch sequence

**Features**:
- Dynamic gear rotation with acceleration/deceleration
- Shrinking circle animation
- Yellow circle expansion reveal
- Configurable timing and visual elements

**Customizable Parameters**:
```python
self.shrink_frames = 35            # Shrinking animation duration
self.expand_frames = 35            # Expansion animation duration
self.gear_rotation_speed = 5.2     # Degrees per frame
```

### Power Pong Transition (`Animation/PowerPongTransitionAnimation.py`)

**Purpose**: Ball physics and paddle animations

**Features**:
- Realistic gravity simulation
- Collision detection and bounce physics
- Paddle swing animations with rotation
- Ball expansion and transition effects

**Physics Parameters**:
```python
self.gravity = 0.5                 # Gravity acceleration
self.bounce_damping = 0.7          # Bounce energy loss
self.paddle_hit_drop_distance = 40 # Paddle movement range
```

### Graphing Line Animation (`Animation/GraphingLineAnimation.py`)

**Purpose**: Real-time line plotting animations

**Features**:
- Smooth line drawing with configurable speed
- Multiple animation phases
- Professional graph styling

## Arduino Control

### Main Controller (`Control/main/main.ino`)

**Purpose**: Primary Arduino sketch for hardware control

**Features**:
- Mode switching between different experiments
- Serial command processing
- Hardware initialization

### Spring Dampener Controller (`Control/main/SpringDampener.ino`)

**Purpose**: Spring-dampener system control and data logging

**Features**:
- PID control with adjustable gains
- Real-time position logging at 100Hz
- Performance metrics calculation (overshoot, rise time, settling time)

**Serial Protocol**:
```
DATA_START                    # Start data collection
time,position                 # CSV header
0.000,4.380                  # Time (s), Position (degrees)
0.100,4.385
...
DATA_END                      # End data collection
Overshoot (%): 12.5          # Performance metrics
Rise Time (s): 0.850
Settling Time (s): 3.200
```

**Adjustable Parameters**:
```cpp
float spring_constant = 13;        // Proportional gain
float damping_constant = 3;        // Derivative gain
float target_offset = 2.094;       // 120 degrees in radians
const float fixed_settle_threshold = 0.02 * 2.094; // 5% threshold
```

### Power Pong Controller (`Control/main/PowerPong.ino`)

**Purpose**: Power Pong game control logic

**Features**:
- Motor control for paddle movement
- Game state management
- Score tracking

## Styling System

### Qt Style Sheets (QSS)

**Location**: `Styles/` directory

**Purpose**: Consistent visual theming across all pages

**Theme Colors**:
- **Primary Blue**: `#002454` (background)
- **Accent Yellow**: `#FAC01A` (buttons, highlights)
- **White**: `#FFFFFF` (text, borders)
- **Transparent**: `rgba(255,255,255,0.05)` (button backgrounds)

**Customization**:
- Modify individual `.qss` files for page-specific styling
- Update `styleMainPage.qss` for global button styling
- Adjust colors, fonts, and spacing in each file

## Data Management

### File Storage

**swingData.txt**: Spring dampener test results
- **Format**: CSV with `time,position` columns
- **Auto-generation**: Created after each swing test
- **Location**: Project root directory

**trials.txt**: Topography data
- **Format**: Custom data format
- **Usage**: Loaded by Topography page

### Data Flow

1. **Collection**: Arduino sends real-time data via serial
2. **Processing**: Python parses and validates data
3. **Storage**: Data automatically saved to appropriate files
4. **Visualization**: matplotlib graphs with professional styling

## Customization Guide

### Adding New Pages

1. **Create GUI File**: Add new page class in `GUI/` directory
2. **Update main.py**: Import and add to page stack
3. **Add Styling**: Create corresponding `.qss` file
4. **Update Navigation**: Add button to main menu

### Modifying Serial Communication

1. **Arduino**: Update command handlers in `.ino` files
2. **Python**: Modify serial command methods in GUI files
3. **Protocol**: Ensure consistent command format between systems

### Adjusting Animation Timing

1. **Frame Counts**: Modify `*_frames` variables
2. **Timer Intervals**: Adjust `setInterval()` values
3. **Animation Speed**: Update speed parameters in animation classes

### Changing Visual Theme

1. **Colors**: Update hex values in `.qss` files
2. **Fonts**: Modify font family and size specifications
3. **Spacing**: Adjust margins, padding, and layout parameters

## Troubleshooting

### Common Issues

**Serial Connection Failed**:
- Check `Config.py` for correct device setting
- Verify Arduino is connected and port is available
- Ensure no other applications are using the serial port

**Animation Not Working**:
- Check PyQt6 installation
- Verify sprite image files exist in `Animation/Sprites/`
- Check console for error messages

**Data Not Saving**:
- Verify write permissions in project directory
- Check serial communication is active
- Monitor console for auto-save messages

**Graph Not Displaying**:
- Install matplotlib: `pip install matplotlib`
- Check `swingData.txt` exists and contains valid data
- Verify data format matches expected CSV structure

### Debug Mode

Enable detailed logging by setting `DEV_MODE = True` in `Config.py`

## Dependencies

### Python Packages
- **PyQt6**: GUI framework
- **pyserial**: Serial communication
- **matplotlib**: Data visualization
- **numpy**: Numerical operations

### Installation
```bash
pip install PyQt6 pyserial matplotlib numpy
```

### Arduino Libraries
- **SimpleFOC**: Motor control library
- **Commander**: Serial command processing

## Development Notes

### Code Style
- Consistent naming conventions (snake_case for Python, camelCase for Qt)
- Comprehensive error handling and debug output
- Modular design with clear separation of concerns
- Extensive commenting for maintainability

### Performance Considerations
- Fixed 800x480 resolution for consistent performance
- Efficient animation loops with configurable frame rates
- Optimized serial communication with appropriate timeouts
- Memory management for large datasets

### Future Enhancements
- Additional experiment types
- Enhanced data analysis tools
- Network connectivity for remote monitoring
- Database integration for long-term data storage

---

**Version**: 4.0  
**Last Updated**: Aug 2025  
**Maintainer**: Elliott Kinsley
