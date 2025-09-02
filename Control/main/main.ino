
#include <SimpleFOC.h>

// Hardware objects
MagneticSensorSPI sensor = MagneticSensorSPI(AS5048_SPI, 10);
BLDCMotor         motor  = BLDCMotor(11);
BLDCDriver3PWM    driver = BLDCDriver3PWM(6, 5, 3, 4);

// Global navigation commander
Commander navigationCommander = Commander(Serial);

// Angle helpers
#define _DEG2RAD 0.01745329251994329577f
#define _RAD2DEG 57.295779513082320876f

//const float ZERO_DEG = 254.00f;                  // mech. reference
const float ZERO_DEG = 256.00f;
const float ZERO_RAD = ZERO_DEG * _DEG2RAD;

// Software smoother
const float  ALPHA = 0.15f;
static float angleFilt = ZERO_RAD;


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

// EMERGENCY FAILSAFE FUNCTIONS
void emergencyMotorStop();
bool checkEmergencyConditions();

// Forward declarations for navigation functions
void goToAFM(char* cmd);
void goToPowerPong(char* cmd);
void goToHapticFeedback(char* cmd);
void goToSpringDampener(char* cmd);
void goToMainMenu(char* cmd);

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
  if (motor.driver != nullptr) {
    motor.move(0);
    motor.disable();
    driver.disable();
    delay(500);
    motor.linkSensor(nullptr);
    motor.linkDriver(nullptr);
    motor.target = 0;
    motor.voltage.q = 0;
    motor.voltage.d = 0;
    motor.PID_velocity.reset();
    motor.P_angle.reset();
    motor.controller = MotionControlType::torque;
    setMotorNotReady();
    delay(1000);
    motor.linkSensor(&sensor);
    motor.linkDriver(&driver);
    setMotorReady();
  }
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
  if (consecutiveFailures >= MAX_CONSECUTIVE_FAILURES) {
    delay(5000);
    consecutiveFailures = 0;
  } else {
    delay(1000 * consecutiveFailures);
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


  randomSeed(analogRead(A0));
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
  
  Serial.println("Ready");
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
        afm_initialised = true;
      }
      runAFM();
      return;

    case POWER_PONG_MODE:
      afm_initialised = false;
      runPowerPong();
      return;

    case SPRING_DAMPENER_MODE:
      runSpringDampener();
      afm_initialised = false;
      return;

    case HAPTIC_FEEDBACK_MODE:
      runHapticFeedback();
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



void setupAFM() {
  pinMode(7, OUTPUT); digitalWrite(7, LOW);
  pinMode(LED_BUILTIN, OUTPUT); digitalWrite(LED_BUILTIN, HIGH);
  disableMotor();
  sensor.init();
  driver.voltage_power_supply = 12;
  driver.init();
  motor.linkSensor(&sensor);
  motor.linkDriver(&driver);
  motor.controller = MotionControlType::angle;
  motor.P_angle.P = 30.0f;
  motor.PID_velocity.P = 0.25f;
  motor.PID_velocity.I = 2.0f;
  motor.voltage_limit = 6.0f;
  motor.LPF_velocity.Tf = 0.01f;
  motor.voltage_sensor_align = 2;
  motor.init();
  motor.initFOC();
  motor.enable();
  motor.target = ZERO_RAD;
  delay(500);
  setMotorReady();
}

void runAFM() {
  while (currentMode == AFM_MODE) {
    navigationCommander.run();
    motor.loopFOC();
    motor.move(ZERO_RAD);
    static uint32_t t0 = 0;
    if (millis() - t0 >= 10) {
      t0 = millis();
      float rawRad = sensor.getAngle();
      angleFilt = (1.0f - ALPHA) * angleFilt + ALPHA * rawRad;
      float deltaRad = fmodf((ZERO_RAD - angleFilt) + _2PI, _2PI);
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