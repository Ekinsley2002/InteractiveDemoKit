# include <SimpleFOC.h>

// ============================================================================
// CALIBRATION INSTRUCTIONS:
// ============================================================================
// To calibrate the zero position:
// 1. Change the CALIBRATED_ZERO_POSITION value below
// 2. Upload the code to the Arduino
// 3. Click "Zero Position" in the GUI - motor will go to this position
// 4. If not correct, adjust CALIBRATED_ZERO_POSITION and repeat
// 
// The offset picker works RELATIVE to this calibrated zero position
// ============================================================================

// velocity set point variable
float target_velocity = 2;
float zero_point = 0;

// CALIBRATED ZERO POSITION - Change this value to set where "zero" should be
const float CALIBRATED_ZERO_POSITION = 0.0f; // Adjust this value in radians to calibrate zero position

// instantiate the commander
Commander command = Commander(Serial);
void doTarget(char* cmd) { command.scalar(&target_velocity, cmd); }
void doMove270(char* cmd);
void doResetZero(char* cmd);

void setupPowerPong() {
  // Set D7 as to low as a ground for the SimpleFOC V1.0 mini board
  int pin = 7;
  pinMode(pin, OUTPUT);  // Set the pin as an output
  digitalWrite(pin, LOW);  // Set the pin to LOW

  // Initialize the onboard LED pin as an output
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);

  // initialise magnetic sensor hardware
  sensor.init();
  
  // link the motor to the sensor
  motor.linkSensor(&sensor);

  // driver config - power supply voltage [V]
  driver.voltage_power_supply = 12;
  driver.init();
  
  // link the motor and the driver
  motor.linkDriver(&driver);

  // set motion control loop to be used
  motor.controller = MotionControlType::velocity;

  // velocity PI controller parameters
  motor.PID_velocity.P = 0.25f;
  motor.PID_velocity.I = 2;
  motor.PID_velocity.D = 0;
  
  // default voltage_power_supply
  motor.voltage_limit = 12;
  
  // jerk control using voltage voltage ramp
  motor.PID_velocity.output_ramp = 10000;

  // velocity low pass filtering
  motor.LPF_velocity.Tf = 0.01f;

  // use monitoring with serial
  Serial.begin(115200);
  motor.useMonitoring(Serial);

  // initialize motor
  motor.init();
  
  // align sensor and start FOC
  motor.initFOC();

  // add commands
  command.add('T', doTarget, "target velocity");
  command.add('M', doMove270, "move 270 degrees and back");
  command.add('R', doResetZero, "reset zero point");

  _delay(1000);
}

void powerPongLoop() {

  // main FOC algorithm function
  motor.loopFOC();

  // Motion control function
  motor.move(0);

  // user communication
  command.run();
}

void doMove270(char* cmd) {
  // Use the calibrated zero position as the reference point
  zero_point = CALIBRATED_ZERO_POSITION;
  
  // Calculate the target angle for 270 degrees from the calibrated zero
  float target_angle = zero_point - (300.0 * (PI / 180.0)); // Convert degrees to radians
  
  // Rotate to 270 degrees
  while (sensor.getAngle() > target_angle) {
    motor.move(-4);
    motor.loopFOC();
  }
  
  // Stop the motor
  motor.move(0);
  delay(500000);
  
  Serial.println("FORE!");
  
  // Swing back to zero point
  while (sensor.getAngle() < zero_point) {
    motor.move(target_velocity);
    motor.loopFOC();
  }
  
  // Stop the motor
  motor.move(0);
}

void doResetZero(char* cmd) {
  // This function moves the motor to the CALIBRATED_ZERO_POSITION
  // The offset value is ignored - the motor always goes to the same calibrated position
  // To change the zero position, modify CALIBRATED_ZERO_POSITION constant above

  // Skip the first character ('R') and parse the rest as the offset value
  float offset_degrees = atof(cmd + 1);
  
  // Convert degrees to radians
  float offset_radians = offset_degrees * (PI / 180.0);

  // Print the offset for debugging
  Serial.print("Moving to CALIBRATED ZERO POSITION (radians): ");
  Serial.println(CALIBRATED_ZERO_POSITION, 4);
  Serial.print("Current position (radians): ");
  Serial.println(sensor.getAngle(), 4);

  // Calculate the new zero point by adding the offset to the current zero point
  float new_zero = CALIBRATED_ZERO_POSITION; // Always go to the calibrated zero position

  // Move to the new zero point
  float current_angle = sensor.getAngle();
  float angle_difference = new_zero - current_angle;
  
  if (angle_difference > 0) {
    while (current_angle < new_zero) {
      motor.move(4);
      motor.loopFOC();
      current_angle = sensor.getAngle();
    }
  } else {
    while (current_angle > new_zero) {
      motor.move(-4);
      motor.loopFOC();
      current_angle = sensor.getAngle();
    }
  }

  // Stop the motor
  motor.move(0);
  
}