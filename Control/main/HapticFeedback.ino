#include <SimpleFOC.h>

// Haptic tick variables
const int num_ticks = 8; // Adjustable
const float tick_angle = _2PI / num_ticks;
float last_angle = 0;
float snap_threshold = tick_angle / 20.0; // Threshold for snapping to the nearest tick
float spring_constant = 2.5; // Proportional strength of the spring (adjustable)

void setupHapticFeedback() {
  // Set D7 as to low as a ground for the SimpleFOC V1.0 mini board
  int pin = 7;
  pinMode(pin, OUTPUT);  // Set the pin as an output
  digitalWrite(pin, LOW);  // Set the pin to LOW as ground

  // Initialize magnetic sensor hardware
  sensor.init();

  // Link the motor to the sensor
  motor.linkSensor(&sensor);

  // Power supply voltage
  driver.voltage_power_supply = 12;
  driver.init();
  motor.linkDriver(&driver);

  // Aligning voltage 
  motor.voltage_sensor_align = 5;

  // Choose FOC modulation (optional)
  motor.foc_modulation = FOCModulationType::SpaceVectorPWM;

  // Set motion control loop to be used
  motor.controller = MotionControlType::torque;

  // Use monitoring with serial 
  Serial.begin(115200);

  // Initialize motor
  motor.init();

  // Align sensor and start FOC
  motor.initFOC();

  Serial.println(F("Motor ready."));
  _delay(1000);
}

void hapticFeedbackLoop() {
  motor.loopFOC();

  // Haptic feedback logic
  float current_angle = motor.shaftAngle();

  // Calculate the angle difference to the nearest tick
  float angle_diff = current_angle - last_angle;

  if (abs(angle_diff) >= tick_angle) {
    // Update the last angle to the new tick position
    last_angle += round(angle_diff / tick_angle) * tick_angle;

    // Determine the direction of the click
    float click_voltage = (angle_diff > 0) ? 2.0 : -2.0;

    // Apply directional click force
    motor.move(click_voltage); 
    Serial.println(F("Haptic tick"));
  } 
  else if (abs(angle_diff) > snap_threshold) {
    // Apply a spring force proportional to the distance from the last tick
    float spring_force = -spring_constant * (angle_diff / abs(angle_diff)) * abs(angle_diff); 
    motor.move(spring_force);
  } 
  else {
    motor.move(0); // No movement if within the snap threshold and near the last tick
  }
}