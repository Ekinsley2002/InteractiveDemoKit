#include <SimpleFOC.h>

// velocity set point variable
float target_velocity = 2;
float zero_point = 0;

// Exit flag for PowerPong loop
bool powerPongExitFlag = false;

// Use global navigation commander (declared in main.ino)
void doTarget(char* cmd) { navigationCommander.scalar(&target_velocity, cmd); }
void doMove270(char* cmd);
void doResetZero(char* cmd);
void doOffset(char* cmd);
void goBack();

void setupPowerPong() {
  powerPongExitFlag = false;
  pinMode(7, OUTPUT);
  digitalWrite(7, LOW);
  disableMotor();
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);
  sensor.init();
  motor.linkSensor(&sensor);
  driver.voltage_power_supply = 12;
  driver.init();
  motor.linkDriver(&driver);
  motor.controller = MotionControlType::velocity;
  motor.PID_velocity.P = 0.25f;
  motor.PID_velocity.I = 2;
  motor.PID_velocity.D = 0;
  motor.voltage_limit = 12;
  motor.PID_velocity.output_ramp = 10000;
  motor.LPF_velocity.Tf = 0.01f;
  motor.useMonitoring(Serial);
  motor.init();
  motor.initFOC();
  motor.enable();
  motor.target = 0;
  motor.voltage.q = 0;
  motor.voltage.d = 0;
  delay(500);
  setMotorReady();
  doResetZero('R0'); // 
  _delay(1000);
}

void goBack() {
  digitalWrite(ledPin, HIGH);
  powerPongExitFlag = true;
}

void cleanupPowerPong() {
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
}

bool powerPongLoop() {
  if (powerPongExitFlag) {
    return false;
  }
  motor.loopFOC();
  motor.move(0);
  navigationCommander.run();
  return true;
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
  delay(2000);
  
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

void doOffset(char* cmd) {
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