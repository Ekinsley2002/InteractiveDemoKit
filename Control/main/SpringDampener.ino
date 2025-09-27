#include <SimpleFOC.h>

float spring_dampener_constant = 13.0;
float damping_constant = 3.0;
float previous_position = 0;
unsigned long previous_time = 0;
bool toggle_state = false;
float zero_position = 0.0;
float target_offset = 2.094;
unsigned long start_time = 0;
bool logging = false;
unsigned long last_log_time = 0;

void doSpringConstant(char* cmd) { navigationCommander.scalar(&spring_dampener_constant, cmd); }
void doDampingConstant(char* cmd) { navigationCommander.scalar(&damping_constant, cmd); }

void doToggleSetpoint(char* cmd) {
  toggle_state = !toggle_state;
  start_time = millis();
  last_log_time = 0;
  logging = true;
  Serial.println(F("DATA_START"));
}
void setupSpringDampener() {
  setupMotorForMode(MotionControlType::torque, 6.0f);
  zero_position = sensor.getAngle();
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
  
  if (logging && (current_time - last_log_time) >= 100 && start_time > 0) {
    last_log_time = current_time;
    Serial.print((current_time - start_time) / 1000.0, 1);
    Serial.print(",");
    Serial.println(current_position_degrees, 1);
  }
  
  if (logging && (!toggle_state || (millis() - start_time > 30000))) {
    Serial.println(F("DATA_END"));
    logging = false;
    start_time = 0;
    toggle_state = false;
  }

  navigationCommander.run();
}
void cleanupSpringDampener() {
  cleanupMotorForMode();
  resetSpringDampenerState();
}
void resetSpringDampenerState() {
  toggle_state = false;
  logging = false;
  start_time = 0;
  last_log_time = 0;
}
