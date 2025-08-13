# include <SimpleFOC.h>

// velocity set point variable
float target_velocity = 2;
float zero_point = 0;

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
  // Save the current position as the initial zero point
  zero_point = sensor.getAngle();
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
  
  // Swing back to zero point
  while (sensor.getAngle() < zero_point) {
    motor.move(target_velocity);
    motor.loopFOC();
  }
  
  // Stop the motor
  motor.move(0);
}

void doResetZero(char* cmd) {

  // Directly convert the command to a float offset
  float offset = atof(cmd);

  // Print the offset for debugging
  Serial.print("Moving to Offset: ");
  Serial.println(offset, 4);

  // Calculate the new zero point by adding the offset to the current zero point
  float new_zero = zero_point + offset;

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