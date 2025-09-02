#include <SimpleFOC.h>

float spring_dampener_constant = 13.0;
float damping_constant = 3.0;
float previous_position = 0;
unsigned long previous_time = 0;
bool toggle_state = false;
float zero_position = 0.8;
float target_offset = 2.094;
unsigned long start_time = 0;
bool logging = false;
unsigned long last_log_time = 0;

void doSpringConstant(char* cmd) { navigationCommander.scalar(&spring_dampener_constant, cmd); }
void doDampingConstant(char* cmd) { navigationCommander.scalar(&damping_constant, cmd); }

void doToggleSetpoint(char* cmd) {
  toggle_state = !toggle_state;
  start_time = millis();
  logging = true;
  Serial.println("S");
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
  float desired_zero = 0.8;
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
  zero_position = desired_zero;
  navigationCommander.add('K', doSpringConstant, "");
  navigationCommander.add('D', doDampingConstant, "");
  navigationCommander.add('Q', doToggleSetpoint, "");
  resetSpringDampenerState();
}
void springDampenerLoop() {
  motor.loopFOC();
      float current_position = motor.shaftAngle();
      float current_position_degrees = current_position * (180.0 / PI);
      unsigned long current_time = millis();
      
      float velocity = 0.0;
      if (current_time != previous_time) {
        velocity = (current_position - previous_position) / ((current_time - previous_time) / 1000.0);
      }

      float target_position = toggle_state ? zero_position + target_offset : zero_position;
      float spring_voltage = spring_dampener_constant * (target_position - current_position);
      float damping_voltage = -damping_constant * velocity;

      float motor_voltage = spring_voltage + damping_voltage;
      motor.move(motor_voltage);
      previous_position = current_position;
      previous_time = current_time;
                if (logging && millis() - last_log_time >= 100 && start_time > 0) {
                  last_log_time = millis();
                  Serial.print((current_time - start_time) / 1000.0, 3);
                  Serial.print(",");
                  Serial.println(current_position_degrees, 3);
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
  last_log_time = 0;
  previous_position = 0;
  previous_time = 0;
}
