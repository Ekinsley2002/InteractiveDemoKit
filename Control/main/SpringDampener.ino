#include <SimpleFOC.h>

// Forward declaration
void disableMotor();
void setMotorReady();
void cleanupSpringDampener();
void resetSpringDampenerState();

// Spring-dampener tuning parameters
float spring_dampener_constant = 13.0; // Proportional gain
float damping_constant = 3.0; // Derivative gain

// Use global navigation commander (declared in main.ino)


// Damping derivative calculation variables
float previous_position = 0;
unsigned long previous_time = 0;

// Toggle parameters
bool toggle_state = false;
float zero_position = 0.8;
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
void doSpringConstant(char* cmd) { navigationCommander.scalar(&spring_dampener_constant, cmd); }

// Command to change damping constant constant
void doDampingConstant(char* cmd) { navigationCommander.scalar(&damping_constant, cmd); }

// Command to toggle setpoint and record response
void doToggleSetpoint(char* cmd) {
  toggle_state = !toggle_state;
  start_time = millis();
  logging = true;
  max_position = 0;
  settled = false;
  rise_time_recorded = false;
  Serial.println("DATA_START");
  Serial.println("time,position");
}


void setupSpringDampener() {
  pinMode(7, OUTPUT);
  digitalWrite(7, LOW);
  disableMotor();
  sensor.init();
  driver.voltage_power_supply = 12;
  driver.voltage_limit = 6;
  motor.voltage_limit = 6;
  driver.init();
  motor.linkSensor(&sensor);
  motor.linkDriver(&driver);
  motor.voltage_sensor_align = 2;
  motor.foc_modulation = FOCModulationType::SpaceVectorPWM;
  motor.controller = MotionControlType::torque;
  motor.init();
  motor.initFOC();
  motor.enable();
  motor.target = 0;
  motor.voltage.q = 0;
  motor.voltage.d = 0;
  delay(500);
  setMotorReady();
  resetSpringDampenerState();
  Serial.println(F("Motor ready."));
}


void springDampenerLoop() {

  // Main FOC algorithm function
  motor.loopFOC();
  // Get the current position and velocity and time measurements
      float current_position = motor.shaftAngle(); // returns position in radians
      float current_position_degrees = current_position * (180.0 / PI); // convert position to degrees for logging
      unsigned long current_time = millis(); // Time in milliseconds
      
      // Calculate velocity with safety check to prevent division by zero
      float velocity = 0.0;
      if (current_time != previous_time) {
        velocity = (current_position - previous_position) / ((current_time - previous_time) / 1000.0); // rad/s
      }

  // Determine the target position based on the toggle state
      float target_position = toggle_state ? zero_position + target_offset : zero_position;
      float target_position_90 = target_position * 0.9; // defines 90% of the target position (rise time computation)

  // Calculate the spring force (proportional) and damping force (derivative), and total motor command
      float spring_voltage = spring_dampener_constant * (target_position - current_position);
      float damping_voltage = -damping_constant * velocity;

  // Sum forces to get the motor command voltage
      float motor_voltage = spring_voltage + damping_voltage;

  // Apply motor command (voltage)
      motor.move(motor_voltage);

  // Update previous values for the next loop iteration
      previous_position = current_position;
      previous_time = current_time;

  // This code is what logs the data at 100 Hz and characterizes the response
                if (logging && millis() - last_log_time >= 100 && start_time > 0) { // 100 Hz logging with safety check
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
                      Serial.println("DATA_END");
                    }
                  } else {
                    settled = false; // Reset settling check if out of threshold
                  }
                }

  navigationCommander.run();
}

void cleanupSpringDampener() {
  if (motor.driver != nullptr) {
    motor.move(0);
    motor.disable();
    delay(300);
    motor.target = 0;
    motor.voltage.q = 0;
    motor.voltage.d = 0;
    motor.PID_velocity.reset();
    delay(100);
  }
  resetSpringDampenerState();
}

void resetSpringDampenerState() {
  toggle_state = false;
  logging = false;
  start_time = 0;
  max_position = 0;
  settled = false;
  settle_start_time = 0;
  rise_time_recorded = false;
  rise_time = 0;
  last_log_time = 0;
  previous_position = 0;
  previous_time = 0;
}
