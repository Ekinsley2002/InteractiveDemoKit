#include <SimpleFOC.h>

float target_velocity = 2;
float zero_point = 0;
bool powerPongExitFlag = false;
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
  
  float desired_zero = 4.38;
  while (abs(sensor.getAngle() - desired_zero) > 0.01) {
    float current_angle = sensor.getAngle();
    float error = desired_zero - current_angle;
    float move_speed = error * 2.0;
    if (move_speed > 4.0) move_speed = 4.0;
    if (move_speed < -4.0) move_speed = -4.0;
    motor.move(move_speed);
    motor.loopFOC();
  }
  motor.move(0);
  zero_point = desired_zero;
  
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
  float swing_finish = zero_point + 1;
  float target_angle = zero_point - 5.236;
  
  while (sensor.getAngle() > target_angle) {
    motor.move(-4);
    motor.loopFOC();
  }
  motor.move(0);
  delay(2000);
  
  while (sensor.getAngle() < swing_finish) {
    motor.move(target_velocity);
    motor.loopFOC();
  }
  motor.move(0);
}

void doResetZero(char* cmd) {
  float desired_zero = 4.38;
  while (abs(sensor.getAngle() - desired_zero) > 0.01) {
    float current_angle = sensor.getAngle();
    float error = desired_zero - current_angle;
    float move_speed = error * 2.0;
    if (move_speed > 4.0) move_speed = 4.0;
    if (move_speed < -4.0) move_speed = -4.0;
    motor.move(move_speed);
    motor.loopFOC();
  }
  motor.move(0);
  zero_point = desired_zero;
}

void doOffset(char* cmd) {
  float offset = atof(cmd);
  float new_zero = zero_point + offset;
  float current_angle = sensor.getAngle();
  
  if (new_zero > current_angle) {
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
  motor.move(0);
}