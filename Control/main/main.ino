/*FOR AFM MOVE LATER*/
#include <SimpleFOC.h>

// ──────────────────────────  Hardware objects
MagneticSensorSPI sensor = MagneticSensorSPI(AS5048_SPI, 10);
BLDCMotor         motor  = BLDCMotor(11);
BLDCDriver3PWM    driver = BLDCDriver3PWM(6, 5, 3, 4);

// ──────────────────────────  Angle helpers
#define _DEG2RAD 0.01745329251994329577f
#define _RAD2DEG 57.295779513082320876f

const float ZERO_DEG = 250.0f;                  // mech. reference
const float ZERO_RAD = ZERO_DEG * _DEG2RAD;

// ──────────────────────────  Software smoother
const float  ALPHA = 0.15f;
static float angleFilt = ZERO_RAD;


// Event constants
#define MAIN_MENU 0
#define AFM 1
#define POWER_PONG 2

/**
 * Random 0.00 – 0.10 to Serial
 * --------------------------------
 * Sends a new random float in the range 0.00–0.10 (steps of 0.01)
 * every second.
 */
void setup() {
  Serial.begin(115200);

  // Use an unconnected analog pin to add a little entropy.
  // If all your pins are in use, set a fixed seed instead (e.g., randomSeed(42)).
  randomSeed(analogRead(A0));
}

void loop() {
  static bool afm_initialised = false;     // remembers we did it once

  int code = checkCode();
  if (code < 0) return;

  switch (code) {
    case MAIN_MENU:
      afm_initialised = false;             // reset flags when you leave
      return;

    case AFM:
      if (!afm_initialised) {              // <--------------
        setupAFM();
        afm_initialised = true;
      }
      runAFM();
      return;

    case POWER_PONG:
      afm_initialised = false;
      runPowerPong();
  }
}

int checkCode() {
  if (Serial.available() == 0) return -1;   // no new byte

  int byteRead = Serial.read();             // 0–255

  switch (byteRead) {
    case MAIN_MENU:  return MAIN_MENU;
    case AFM:        return AFM;
    case POWER_PONG: return POWER_PONG;
    default:         return -1;             // unknown code
  }
}

void setupAFM() {
  pinMode(7, OUTPUT);           digitalWrite(7, LOW);
  pinMode(LED_BUILTIN, OUTPUT); digitalWrite(LED_BUILTIN, HIGH);

  Serial.begin(115200);

  sensor.init();

  driver.voltage_power_supply = 12;
  driver.init();

  motor.linkSensor(&sensor);
  motor.linkDriver(&driver);

  motor.controller           = MotionControlType::angle;
  motor.P_angle.P            = 30.0f;
  motor.PID_velocity.P       = 0.25f;
  motor.PID_velocity.I       = 2.0f;
  motor.voltage_limit        = 6.0f;
  motor.LPF_velocity.Tf      = 0.01f;

  motor.voltage_sensor_align = 2;     // alignment kick
  motor.init();
  motor.initFOC();

  motor.target = ZERO_RAD;            // park at mech zero
}

void runAFM() {

  while (true) {                   // stay here until we’re told to leave
    int code = checkCode();       // –1 means “nothing new”

    if (code >= 0) {              // only act if we *did* read something
      switch (code) {
        case MAIN_MENU:
        case POWER_PONG:
          return;                 // leave AFM mode
        case AFM:
          /* stay here */         // do nothing special
          break;
      }
    }

  motor.loopFOC();
  motor.move(ZERO_RAD);

  static uint32_t t0 = 0;
  if (millis() - t0 >= 10) {
    t0 = millis();

    /* 1. filter the raw angle */
    float rawRad = sensor.getAngle();
    angleFilt = (1.0f - ALPHA) * angleFilt + ALPHA * rawRad;

    /* 2. offset in *your* positive direction          ↓ FLIPPED SIGN */
    float deltaRad = fmodf((ZERO_RAD - angleFilt) + _2PI, _2PI); // 0 … 2π

    /* 3. squash wrap bucket and negatives to zero */
    float deltaDeg = deltaRad * _RAD2DEG;          // 0 … 360
    if (deltaDeg > 100.0f)   deltaDeg = 0.0f;      // noise around wrap
    /* if you also want any “wrong-way” motion to read 0: */
    /* if (deltaDeg < 0.05f)   deltaDeg = 0.0f; */
    Serial.println(deltaDeg, 3);
  }
  }
}

void runPowerPong() {

  int code = 2;   // Self signal as default

  setupPowerPong();

  while( code != MAIN_MENU ) {

    code = checkCode();

    if (code >= 0) {              // only act if we *did* read something
      switch (code) {
        case MAIN_MENU:
        case AFM:
          return;                 // leave Golf mode
        case POWER_PONG:
          /* stay here */         // do nothing special
          break;
      }
    }

    powerPongLoop();
  }
}