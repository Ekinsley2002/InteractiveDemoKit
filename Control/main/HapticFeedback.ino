#include <SimpleFOC.h>

// Forward declaration
void disableMotor();
void setMotorReady();

// Haptic tick variables
const int num_ticks = 8; // Adjustable
const float tick_angle = _2PI / num_ticks;
float last_angle = 0;
float snap_threshold = tick_angle / 20.0; // Threshold for snapping to the nearest tick
float spring_constant = 2.5; // Proportional strength of the spring (adjustable)

void setupHapticFeedback() {
  pinMode(7, OUTPUT);
  digitalWrite(7, LOW);
  disableMotor();
  sensor.init();
  motor.linkSensor(&sensor);
  driver.voltage_power_supply = 12;
  driver.init();
  motor.linkDriver(&driver);
  motor.voltage_sensor_align = 5;
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