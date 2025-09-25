#include <SimpleFOC.h>

// Forward declaration
void disableMotor();
void setMotorReady();

// Haptic tick variables
int num_ticks = 8; // Adjustable - now dynamic
float tick_angle = _2PI / 8; // Will be recalculated when num_ticks changes
float last_angle = 0;
float snap_threshold = tick_angle / 20.0; // Threshold for snapping to the nearest tick
float spring_constant = 2.5; // Proportional strength of the spring (adjustable)

// Parameter update functions
void updateNumTicks(int new_ticks) {
  if (new_ticks > 0 && new_ticks <= 50) { // Reasonable bounds
    num_ticks = new_ticks;
    tick_angle = _2PI / num_ticks;
    snap_threshold = tick_angle / 20.0;
  }
}

void updateSpringConstant(float new_constant) {
  if (new_constant > 0.0 && new_constant <= 20.0) { // Reasonable bounds
    spring_constant = new_constant;
  }
}

// Command handlers for serial communication
void doNumTicks(char* cmd) {
  int new_ticks = atoi(cmd);
  updateNumTicks(new_ticks);
}

void doHapticSpringConstant(char* cmd) {
  float new_constant = atof(cmd);
  updateSpringConstant(new_constant);
}

void setupHapticFeedback() {
  setupMotorForMode(MotionControlType::torque, 6.0f);
  Serial.println(F("Motor ready."));
  _delay(1000);
}

void hapticFeedbackLoop() {
  motor.loopFOC();
  float current_angle = motor.shaftAngle();
  float angle_diff = current_angle - last_angle;
  if (abs(angle_diff) >= tick_angle) {
    last_angle += round(angle_diff / tick_angle) * tick_angle;
    float click_voltage = (angle_diff > 0) ? 2.0 : -2.0;
    motor.move(click_voltage); 
    Serial.println(F("Haptic tick"));
  } 
  else if (abs(angle_diff) > snap_threshold) {
    float spring_force = -spring_constant * (angle_diff / abs(angle_diff)) * abs(angle_diff); 
    motor.move(spring_force);
  } 
  else {
    motor.move(0);
  }
}

void cleanupHapticFeedback() {
  cleanupMotorForMode();
}