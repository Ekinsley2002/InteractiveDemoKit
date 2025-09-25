
#include <SimpleFOC.h>

// Hardware objects
MagneticSensorSPI sensor = MagneticSensorSPI(AS5048_SPI, 10);
BLDCMotor         motor  = BLDCMotor(11);
BLDCDriver3PWM    driver = BLDCDriver3PWM(6, 5, 3, 4);

// Global navigation commander
Commander navigationCommander = Commander(Serial);

// Angle helpers - using PROGMEM for constants
#define _DEG2RAD 0.01745329251994329577f
#define _RAD2DEG 57.295779513082320876f

const float ZERO_DEG PROGMEM = 256.00f;
const float ZERO_RAD PROGMEM = 4.468f; // Pre-calculated: 256 * DEG2RAD
const float ALPHA PROGMEM = 0.15f;

const float INITIAL_ZERO_R = 4.468f;

static float angleFilt = 4.468f; // ZERO_RAD value


// Navigation state
enum NavigationState {
  MAIN_MENU,
  AFM_MODE,
  POWER_PONG_MODE,
  HAPTIC_FEEDBACK_MODE,
  SPRING_DAMPENER_MODE
};

NavigationState currentMode = MAIN_MENU;
int ledPin = 9;

// Motor overload detection variables
unsigned long lastTransitionTime = 0;
const unsigned long MIN_TRANSITION_INTERVAL = 2000;
int consecutiveFailures = 0;
const int MAX_CONSECUTIVE_FAILURES = 3;

// Motor ready state verification
bool motorReady = true;
unsigned long motorReadyTime = 0;
const unsigned long MOTOR_STABILIZATION_TIME = 500;

// EMERGENCY FAILSAFE SYSTEM
bool emergencyStop = false;

const char MOTOR_MOVING = 'Z';
const char MOTOR_NOT_MOVING = 'z'

// Navigation command functions will be defined after canTransition()

// PowerPong command functions (declarations)
void doTarget(char* cmd);
void doOffset(char* cmd);
void doResetZero(char* cmd);
void doMove270(char* cmd);
void goBack();
void cleanupPowerPong();

// SpringDampener command functions (declarations)
void doSpringConstant(char* cmd);
void doDampingConstant(char* cmd);
void doToggleSetpoint(char* cmd);

// HapticFeedback command functions (declarations)
void doNumTicks(char* cmd);
void doHapticSpringConstant(char* cmd);

// Cleanup functions
void cleanupHapticFeedback();
void cleanupSpringDampener();

// Motor control functions
void disableMotor();
bool checkMotorOverload();
void handleTransitionOverload();
bool canTransition();
void setMotorNotReady();
void setMotorReady();
bool isMotorReady();
void forceMainMenuReset();

// Shared motor setup functions to reduce code duplication
void setupMotorForMode(MotionControlType controller_type, float voltage_limit = 6.0f);
void cleanupMotorForMode();

// EMERGENCY FAILSAFE FUNCTIONS
void emergencyMotorStop();
bool checkEmergencyConditions();

// Forward declarations for navigation functions
void goToAFM(char* cmd);
void goToPowerPong(char* cmd);
void goToHapticFeedback(char* cmd);
void goToSpringDampener(char* cmd);
void goToMainMenu(char* cmd);

void resetMotorPosition();

float global_zero = INITIAL_ZERO_R; // used by AFM and power pong

// Motor control functions
void disableMotor() {
  if (motor.driver != nullptr) {
    motor.move(0);
    motor.disable();
    delay(300);
    motor.target = 0;
    motor.voltage.q = 0;
    motor.voltage.d = 0;
    motor.PID_velocity.reset();
    motor.P_angle.reset();
    motor.controller = MotionControlType::torque;
    delay(100);
  }
  setMotorNotReady();
}

void setMotorNotReady() {
  motorReady = false;
  motorReadyTime = 0;
}

void setMotorReady() {
  motorReady = true;
  motorReadyTime = millis();
}

bool isMotorReady() {
  if (!motorReady) return false;
  return (millis() - motorReadyTime) >= MOTOR_STABILIZATION_TIME;
}

void forceMainMenuReset() {
  disableMotor();
  delay(1000);
  setMotorReady();
}

// EMERGENCY FAILSAFE FUNCTIONS
void emergencyMotorStop() {
  if (motor.driver != nullptr) {
    motor.move(0);
    motor.disable();
    driver.disable();
    motor.target = 0;
    motor.voltage.q = 0;
    motor.voltage.d = 0;
  }
  emergencyStop = true;
}

bool checkEmergencyConditions() {
  if (motor.driver != nullptr) {
    if (abs(motor.voltage.q) > motor.voltage_limit * 0.95) {
      return true;
    }
  }
  return false;
}

bool checkMotorOverload() {
  // Simple overload check - just voltage limit
  if (motor.driver != nullptr) {
    if (abs(motor.voltage.q) > motor.voltage_limit * 0.9) {
      return true;
    }
  }
  return false;
}

void handleTransitionOverload() {
  consecutiveFailures++;
  delay(1000 * consecutiveFailures);
  if (consecutiveFailures >= MAX_CONSECUTIVE_FAILURES) {
    consecutiveFailures = 0;
  }
}

bool canTransition() {
  unsigned long now = millis();
  if (now - lastTransitionTime < MIN_TRANSITION_INTERVAL) {
    delay(MIN_TRANSITION_INTERVAL - (now - lastTransitionTime));
  }
  if (checkMotorOverload()) {
    handleTransitionOverload();
    return false;
  }
  // Only block if motor is completely not ready (not just not stabilized)
  if (!motorReady) {
    return false;
  }
  // Extra safety: if coming from main menu, ensure reset is complete
  if (currentMode == MAIN_MENU) {
    if (now - lastTransitionTime < 2000) {  // Wait 2 seconds after main menu reset
      return false;
    }
  }
  return true;
}

// Navigation command functions
void goToAFM(char* cmd) { 
  if (canTransition()) {
    digitalWrite(ledPin, HIGH);
    delay(100);
    digitalWrite(ledPin, LOW);
    currentMode = AFM_MODE;
    lastTransitionTime = millis();
    consecutiveFailures = 0; // Reset on successful transition
  }
}

void goToPowerPong(char* cmd) { 
  if (canTransition()) {
    digitalWrite(ledPin, HIGH);
    delay(100);
    digitalWrite(ledPin, LOW);
    currentMode = POWER_PONG_MODE;
    lastTransitionTime = millis();
    consecutiveFailures = 0;
  }
}

void goToHapticFeedback(char* cmd) { 
  if (canTransition()) {
    digitalWrite(ledPin, HIGH);
    delay(100);
    digitalWrite(ledPin, LOW);
    currentMode = HAPTIC_FEEDBACK_MODE;
    lastTransitionTime = millis();
    consecutiveFailures = 0;
  }
}

void goToSpringDampener(char* cmd) { 
  if (canTransition()) {
    digitalWrite(ledPin, HIGH);
    delay(100);
    digitalWrite(ledPin, LOW);
    currentMode = SPRING_DAMPENER_MODE;
    lastTransitionTime = millis();
    consecutiveFailures = 0;
  }
}

void goToMainMenu(char* cmd) { 
  if (canTransition()) {
    digitalWrite(ledPin, HIGH);
    delay(100);
    digitalWrite(ledPin, LOW);
    
    // Force complete motor reset when going to main menu
    forceMainMenuReset();
    
    currentMode = MAIN_MENU;
    lastTransitionTime = millis();
    consecutiveFailures = 0;
  }
}


void setup() {
  Serial.begin(115200);


  pinMode(ledPin, OUTPUT); 
  digitalWrite(ledPin, LOW);
  
  // Initialize global commander with all commands
  navigationCommander.add('A', goToAFM, "");
  navigationCommander.add('P', goToPowerPong, "");
  navigationCommander.add('H', goToHapticFeedback, "");
  navigationCommander.add('S', goToSpringDampener, "");
  navigationCommander.add('M', goToMainMenu, "");
  
  // Add PowerPong commands
  navigationCommander.add('T', doTarget, "");
  navigationCommander.add('O', doOffset, "");
  navigationCommander.add('R', doResetZero, "");
  navigationCommander.add('G', doMove270, "");
  navigationCommander.add('E', goBack, "");
  
  // Add SpringDampener commands
  navigationCommander.add('K', doSpringConstant, "");
  navigationCommander.add('D', doDampingConstant, "");
  navigationCommander.add('Q', doToggleSetpoint, "");
  
  // Add HapticFeedback commands
  navigationCommander.add('n', doNumTicks, "");
  navigationCommander.add('k', doHapticSpringConstant, "");
  
  bool 

  setMotorReady();
}

void loop() {
  static bool afm_initialised = false;
  
  // EMERGENCY FAILSAFE CHECK
  if (checkEmergencyConditions()) {
    emergencyMotorStop();
    currentMode = MAIN_MENU;
    setMotorNotReady();
  }

  switch (currentMode) {
    case MAIN_MENU:
      afm_initialised = false;
      while (currentMode == MAIN_MENU) {
        navigationCommander.run();
        delay(10);
      }
      return;

    case AFM_MODE:
      if (!afm_initialised) {
        setupAFM();
        resetMotorPosition();  // ← Move HERE, after setupAFM()
        afm_initialised = true;
      }
      runAFM();
      return;

    case POWER_PONG_MODE:
      afm_initialised = false;
      runPowerPong();
      resetMotorPosition();  // ← Move HERE, after runPowerPong() sets up motor
      return;

    case SPRING_DAMPENER_MODE:
      runSpringDampener();
      resetMotorPosition();  // ← Move HERE, after runSpringDampener() sets up motor
      afm_initialised = false;
      return;

    case HAPTIC_FEEDBACK_MODE:
      runHapticFeedback();
      resetMotorPosition();  // ← Move HERE, after runHapticFeedback() sets up motor
      afm_initialised = false;
      return;
  }
}

void runHapticFeedback() {
  setupHapticFeedback();
  while(currentMode == HAPTIC_FEEDBACK_MODE) {
    navigationCommander.run();
    hapticFeedbackLoop();
  }
  cleanupHapticFeedback();
}


void runSpringDampener() {
  setupSpringDampener();
  while(currentMode == SPRING_DAMPENER_MODE) {
    navigationCommander.run();
    springDampenerLoop();
  }
  cleanupSpringDampener();
}

void resetMotorPosition() {
  // First, ensure motor is initialized
  if (motor.driver == nullptr) {
    return;
  }
  
  // Store original controller type
  MotionControlType originalController = motor.controller;
  
  // Switch to torque control and reinitialize
  motor.controller = MotionControlType::torque;
  motor.init();
  motor.initFOC();
  
  int rotations = 0;
  float currentAngle = sensor.getAngle();
  
  // Count how many full rotations we've made POSITIVE
  if(currentAngle > INITIAL_ZERO_R + PI) {
    while (currentAngle > 2 * PI + INITIAL_ZERO_R) {
      currentAngle -= 2 * PI;
      rotations++;
    }
  }

  // If spun in negative direction, note rotations
  else if(currentAngle < INITIAL_ZERO_R - PI) {
    while(currentAngle < 2 * PI - INITIAL_ZERO_R) {
      currentAngle += 2 * PI;
      rotations--;
    }
  }
  
  // Calculate new zero point accounting for rotations
  // This ensures we go to the SAME absolute position every time
  float newZero = INITIAL_ZERO_R + (rotations * 2 * PI);
  
  global_zero = newZero;

  while (abs(currentAngle - newZero) > 0.01) {

    if(currentAngle < newZero) {
      motor.move(0.5);
    }

    else if(currentAngle > newZero) {
      motor.move(-0.5);
    }

    motor.loopFOC();

    currentAngle = sensor.getAngle();
  }
  
  
  motor.move(0);
  
  // Restore original controller type and reinitialize
  motor.controller = originalController;
  motor.init();
  motor.initFOC();
}

void setupAFM() {
  pinMode(LED_BUILTIN, OUTPUT); digitalWrite(LED_BUILTIN, HIGH);
  setupMotorForMode(MotionControlType::angle, 6.0f);
  
  // Configure angle controller specific settings
  motor.P_angle.P = 30.0f;
  motor.PID_velocity.P = 0.25f;
  motor.PID_velocity.I = 2.0f;
  motor.LPF_velocity.Tf = 0.01f;
  
  // Set target for angle controller
  motor.target = global_zero;
}

void runAFM() {
  while (currentMode == AFM_MODE) {
    navigationCommander.run();
    motor.loopFOC();
    motor.move(global_zero);
    static uint32_t t0 = 0;
    if (millis() - t0 >= 10) {
      t0 = millis();
      float rawRad = sensor.getAngle();
      float alpha = pgm_read_float(&ALPHA);
      angleFilt = (1.0f - alpha) * angleFilt + alpha * rawRad;
      float zeroRad = pgm_read_float(&ZERO_RAD);
      float deltaRad = fmodf((zeroRad - angleFilt) + _2PI, _2PI);
      float deltaDeg = deltaRad * _RAD2DEG;
      if (deltaDeg > 100.0f) deltaDeg = 0.0f;
      Serial.println(deltaDeg, 3);
    }
  }
}

void runPowerPong() {
  setupPowerPong();
  while (currentMode == POWER_PONG_MODE) {
    navigationCommander.run();
    if (!powerPongLoop()) {
      cleanupPowerPong();
      return;
    }
  }
  cleanupPowerPong();
}

// Shared motor setup function to reduce code duplication
void setupMotorForMode(MotionControlType controller_type, float voltage_limit) {
  pinMode(7, OUTPUT);
  digitalWrite(7, LOW);
  disableMotor();
  sensor.init();
  motor.linkSensor(&sensor);
  driver.voltage_power_supply = 12;
  driver.voltage_limit = voltage_limit;
  motor.voltage_limit = voltage_limit;
  driver.init();
  motor.linkDriver(&driver);
  motor.voltage_sensor_align = 2;
  motor.foc_modulation = FOCModulationType::SpaceVectorPWM;
  motor.controller = controller_type;
  motor.init();
  motor.initFOC();
  motor.enable();
  motor.target = 0;
  motor.voltage.q = 0;
  motor.voltage.d = 0;
  delay(500);
  setMotorReady();
}

void cleanupMotorForMode() {
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