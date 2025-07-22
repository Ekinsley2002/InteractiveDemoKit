

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
  int code = checkCode();
  if (code < 0) return;      // nothing new

  switch (code) {
    case MAIN_MENU:  return;               // or break;
    case AFM:        runAFM(); return;     // add return/break to stop fall-through
    case POWER_PONG: runPowerPong();
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
    // random(0, 11) gives an integer 0‒10 inclusive.
    int raw = random(0, 11);

    // Convert to float in the desired range: 0 ➜ 0.00, 10 ➜ 0.10.
    float value = raw / 100.0;

    // Print with exactly two decimal places.
    Serial.println(value, 2);

    delay(10);   // wait 1 s before the next value
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