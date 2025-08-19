#include <SimpleFOC.h>

// velocity set point variable
float target_velocity = 2;
float zero_point = 0;

// instantiate the commander
Commander command = Commander(Serial);
void doTarget(char* cmd) { command.scalar(&target_velocity, cmd); }
void doMove270(char* cmd);
void doResetZero(char* cmd);

void setupPowerPong() {
  // Set D7 as ground for SimpleFOC V1.0 mini board
  int pin = 7;
  pinMode(pin, OUTPUT);
  digitalWrite(pin, LOW);

  // Initialize the onboard LED pin as an output
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);

  // Initialize magnetic sensor hardware
  sensor.init();
  
  // Link the motor to the sensor
  motor.linkSensor(&sensor);

  // Driver configuration
  driver.voltage_power_supply = 12;
  driver.init();
  
  // Link the motor and the driver
  motor.linkDriver(&driver);

  // Set motion control loop
  motor.controller = MotionControlType::velocity;

  // Velocity PI controller parameters
  motor.PID_velocity.P = 0.25f;
  motor.PID_velocity.I = 2;
  motor.PID_velocity.D = 0;
  
  // Voltage limit
  motor.voltage_limit = 12;
  
  // Jerk control using voltage ramp
  motor.PID_velocity.output_ramp = 10000;

  // Velocity low pass filtering
  motor.LPF_velocity.Tf = 0.01f;

  // Use monitoring with serial
  Serial.begin(115200);
  motor.useMonitoring(Serial);

  // Initialize motor
  motor.init();
  
  // Align sensor and start FOC
  motor.initFOC();

  // Add commands
  command.add('T', doTarget, "target velocity");
  command.add('M', doMove270, "move 270 degrees and back");
  command.add('R', doResetZero, "reset zero point");

  _delay(1000);
}

void powerPongLoop() {
  
  int code = checkCode();       // –1 means “nothing new”

  if (code >= 0) {
    switch (code) {
      case MAIN_MENU:
      case POWER_PONG:
        return;
      case AFM:
        break;
    }
  }
  // Main FOC algorithm function
  motor.loopFOC();

  // Motion control function
  motor.move(0);

  // User communication
  command.run();
}

void doMove270(char* cmd) {
  // Save the current position as the initial zero point
  float zero_point = sensor.getAngle();

  float swing_finish = zero_point + 1;

  
  // Calculate the target angle for 270 degrees
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
  
  // Swing back to swing finish
  while (sensor.getAngle() < swing_finish) {
    motor.move(target_velocity);
    motor.loopFOC();
  }
  
  // Stop the motor
  motor.move(0);
}

void doResetZero(char* cmd) {

  float offset = 0;

  // Calculate the new zero point by adding the offset to the current zero point
  float new_zero = 4.38;

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