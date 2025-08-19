#include <SimpleFOC.h>

// Spring-dampener tuning parameters - ONLY Variables you will change for this lab
float spring_constant = 13; // Proportional gain
float damping_constant = 3; // Derivative gain


// Damping derivative calculation variables
float previous_position = 0;
unsigned long previous_time = 0;

// Toggle parameters
bool toggle_state = false;
float zero_position = 4.38;
float target_offset = 2.094; // 120 degrees in radians

// Variables for performance metrics
unsigned long start_time = 0;
bool logging = false;
float max_position = 0;
bool settled = false;
unsigned long settle_start_time = 0;
bool rise_time_recorded = false;
unsigned long rise_time = 0;
const float fixed_settle_threshold = 0.02 * 2.094; // 5% of the total step change range
unsigned long last_log_time = 0; // Logging time tracker

// Command to change spring constant
void doSpringConstant(char* cmd) { command.scalar(&spring_constant, cmd); }

// Command to change damping constant constant
void doDampingConstant(char* cmd) { command.scalar(&damping_constant, cmd); }

// Command to both produce a step change and record the response, including rise time, overshoot, and settle time
void doToggleSetpoint(char* cmd) {
  toggle_state = !toggle_state;
  start_time = millis(); // Log the start time in milliseconds
  logging = true;
  max_position = 0;
  settled = false;
  rise_time_recorded = false;
  Serial.println("DATA_START"); // Signal to Python that data collection is starting
  Serial.println("time,position"); // CSV header for logging
}


void setupSpringDampener() {
  // Set D7 as to low as a ground for the SimpleFOC V1.0 mini board
  int pin = 7;  
  pinMode(pin, OUTPUT);  // Set the pin as an output
  digitalWrite(pin, LOW);  // Set the pin to LOW as ground

  // Initialize magnetic sensor hardware
  sensor.init();
  
  // Link the motor to the sensor
  motor.linkSensor(&sensor);

  // Power supply voltage
  driver.voltage_power_supply = 12;
  driver.voltage_limit = 6;
  motor.voltage_limit = 6;
  driver.init();
  motor.linkDriver(&driver);

  // Aligning voltage 
  motor.voltage_sensor_align = 2;

  // Choose FOC modulation
  motor.foc_modulation = FOCModulationType::SpaceVectorPWM;

  // Set motion control loop to be used
  motor.controller = MotionControlType::torque;

  // Use monitoring with serial 
  Serial.begin(115200);

  // Initialize motor
  motor.init();

  // Align sensor and start FOC
  motor.initFOC();

  // Add commands to adjust parameters
  command.add('K', doSpringConstant, "spring constant"); // Sending command "K13" changes the spring constant to 13
  command.add('D', doDampingConstant, "damping constant"); // Sending command "D0.001" changes the damping constant to 0.001
  command.add('T', doToggleSetpoint, "toggle setpoint"); // Sending command "T" toggles between two angle setpoints

  // Print statements on start-up for interface instructions
  Serial.println(F("Motor ready."));
  Serial.println(F("Set the tuning parameters using serial terminal, Prompt with 'K' and 'D'."));
  Serial.println(F("Toggle setpoint using 'T' command."));
  _delay(2000);
}


void springDampenerLoop() {

  // Main FOC algorithm function that updates motor and sensor variables
      motor.loopFOC();

  // Get the current position and velocity and time measurements
      float current_position = motor.shaftAngle(); // returns position in radians
      float current_position_degrees = current_position * (180.0 / PI); // convert position to degrees for logging
      unsigned long current_time = millis(); // Time in milliseconds
      float velocity = (current_position - previous_position) / ((current_time - previous_time) / 1000.0); // rad/s

  // Determine the target position based on the toggle state
      float target_position = toggle_state ? zero_position + target_offset : zero_position;
      float target_position_90 = target_position * 0.9; // defines 90% of the target position (rise time computation)

  // Calculate the spring force (proportional) and damping force (derivative), and total motor command
      float spring_voltage = spring_constant * (target_position - current_position);
      float damping_voltage = -damping_constant * velocity;

  // Sum forces to get the motor command voltage
      float motor_voltage = spring_voltage + damping_voltage;

  // Apply motor command (voltage)
      motor.move(motor_voltage);

  // Update previous values for the next loop iteration
      previous_position = current_position;
      previous_time = current_time;

  // This code is what logs the data at 100 Hz and characterizes the response
                if (logging && millis() - last_log_time >= 100) { // 100 Hz logging
                  last_log_time = millis();
                  Serial.print((current_time - start_time) / 1000.0, 3); // Log time in seconds with 3 decimal places
                  Serial.print(",");
                  Serial.println(current_position_degrees, 3); // Log position in degrees with 3 decimal places
                  
                  // Save swing data to file for GUI graphing
                  // Note: Arduino cannot directly write to files, so we'll send this data
                  // to the Python GUI which will save it to swingData.txt

                  // Track maximum position for overshoot calculation
                  if (current_position > max_position) {
                    max_position = current_position;
                  }

                  // Record the rise time when the position first reaches 90% of the target position
                  if (!rise_time_recorded && fabs(current_position - target_position_90) < fixed_settle_threshold) {
                    rise_time = current_time - start_time;
                    rise_time_recorded = true;
                  }

                  // Check for settling
                  if (fabs(current_position - target_position) < fixed_settle_threshold) {
                    if (!settled) {
                      settled = true;
                      settle_start_time = current_time;
                    } else if (current_time - settle_start_time >= 10000) { // Settling time condition (1 second within threshold)
                      logging = false; // Stop logging
                      Serial.println("DATA_END"); // Signal to Python that data collection is ending
                      float overshoot = ((max_position - target_position) / (target_position - zero_position)) * 100.0;
                      float settling_time = (current_time - start_time) / 10000.0;
                      Serial.print("Overshoot (%): ");
                      Serial.println(overshoot, 2);
                      Serial.print("Rise Time (s): ");
                      Serial.println(rise_time / 10000.0, 3); // Convert rise time to seconds
                      Serial.print("Settling Time (s): ");
                      Serial.println(settling_time, 3);
                    }
                  } else {
                    settled = false; // Reset settling check if out of threshold
                  }
                }

  // User communication - updates commands from the serial monitor
  command.run();
}
