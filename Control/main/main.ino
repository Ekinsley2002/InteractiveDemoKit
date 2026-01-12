
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

const float INITIAL_ZERO_R = 4.295f;

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

// Motor ready state verification
bool motorReady = true;
unsigned long motorReadyTime = 0;
const unsigned long MOTOR_STABILIZATION_TIME = 500;

const char MOTOR_MOVING = 'Z';
const char MOTOR_NOT_MOVING = 'z';

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

// Shared motor setup functions to reduce code duplication
void setupMotorForMode(MotionControlType controller_type, float voltage_limit = 6.0f);
void cleanupMotorForMode();

// Forward declarations for navigation functions
void goToAFM(char* cmd);
void goToPowerPong(char* cmd);
void goToHapticFeedback(char* cmd);
void goToSpringDampener(char* cmd);
void goToMainMenu(char* cmd);

void resetMotorPosition();

float global_zero = INITIAL_ZERO_R; // used by AFM and power pong

const float AFM_ZERO = 4.511f;

// Navigation command functions
void goToAFM(char* cmd) { 
    currentMode = AFM_MODE;
    lastTransitionTime = millis();
}

void goToPowerPong(char* cmd) { 
    digitalWrite(ledPin, HIGH);
    delay(100);
    digitalWrite(ledPin, LOW);
    currentMode = POWER_PONG_MODE;
    lastTransitionTime = millis();
}

void goToHapticFeedback(char* cmd) { 
    digitalWrite(ledPin, HIGH);
    delay(100);
    digitalWrite(ledPin, LOW);
    currentMode = HAPTIC_FEEDBACK_MODE;
    lastTransitionTime = millis();
}


void goToSpringDampener(char* cmd) { 

    digitalWrite(ledPin, HIGH);
    delay(100);
    digitalWrite(ledPin, LOW);
    currentMode = SPRING_DAMPENER_MODE;
    lastTransitionTime = millis();
}

void goToMainMenu(char* cmd) { 
    digitalWrite(ledPin, HIGH);
    delay(100);
    digitalWrite(ledPin, LOW);
    resetMotorPosition();
    currentMode = MAIN_MENU;
    lastTransitionTime = millis();
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

  resetMotorPosition();
}

void loop() {
  static bool afm_initialised = false;
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
        resetMotorPosition();  
        afm_initialised = true;
      }
      runAFM();
      return;

    case POWER_PONG_MODE:
      resetMotorPosition();
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
  if (currentMode != AFM_MODE) {
    motor.controller = MotionControlType::torque;
    motor.init();
    motor.initFOC();
  }

  int rotations = 0;
  float currentAngle = sensor.getAngle();

  float newZero;
  
  // Count how many full rotations we've made POSITIVE

  if((currentMode != AFM_MODE && currentMode != SPRING_DAMPENER_MODE) || currentMode == POWER_PONG_MODE)
  {
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
    newZero = INITIAL_ZERO_R + (rotations * 2 * PI);
  }

  else if(currentMode == AFM_MODE || currentMode == SPRING_DAMPENER_MODE)
  {
    if(currentAngle > AFM_ZERO + PI) {
      while (currentAngle > AFM_ZERO + 2 * PI) {
        currentAngle -= 2 * PI;
        rotations++;
      }
    }
  
    // If spun in negative direction, note rotations
    else if(currentAngle < AFM_ZERO - PI) {
      while(currentAngle < AFM_ZERO - 2 * PI) {
        currentAngle += 2 * PI;
        rotations--;
      }
    }
  
    // Calculate new zero point accounting for rotations
    // This ensures we go to the SAME absolute position every time
    newZero = AFM_ZERO + (rotations * 2 * PI);
  }
  
  global_zero = newZero;

  // Do not move the motor for afm mode, just update global position.
  if(currentMode == AFM_MODE)
    {
      return;
    }
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
  setupMotorForMode(MotionControlType::angle, 3.0f);
  
  // Configure angle controller specific settings
  //motor.P_angle.P = 30.0f;
  //motor.PID_velocity.P = 0.25f;
  //motor.PID_velocity.I = 2.0f;
  //motor.LPF_velocity.Tf = 0.01f;
  motor.P_angle.P = 25.0f;
  motor.PID_velocity.P = 0.20f;
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
      float zeroRad = global_zero;
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