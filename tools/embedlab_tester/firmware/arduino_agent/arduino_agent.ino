/*
  EmbedLab Board Tester - Arduino serial agent

  Version MVP pour Arduino Uno, Nano et Mega.
  Le PC envoie des commandes serie terminees par \n.

  Commandes principales :
    PING
    PINMODE <pin> OUTPUT|INPUT|INPUT_PULLUP
    DWRITE <pin> 0|1
    DREAD <pin>
    AREAD <pin>
    PWM <pin> <0..255>
    TONE <pin> <freq> <duration_ms>
    NOTONE <pin>
    I2C_SCAN

  Exemples :
    PINMODE 5 OUTPUT
    DWRITE 5 1
    AREAD A0
*/

#include <Arduino.h>
#include <Wire.h>

String lineBuffer;

int parsePin(const String &token) {
  String t = token;
  t.trim();
  t.toUpperCase();
  if (t.length() >= 2 && t.charAt(0) == 'A') {
    int n = t.substring(1).toInt();
    return A0 + n;
  }
  return t.toInt();
}

String nextToken(String &line) {
  line.trim();
  int idx = line.indexOf(' ');
  if (idx < 0) {
    String out = line;
    line = "";
    return out;
  }
  String out = line.substring(0, idx);
  line = line.substring(idx + 1);
  line.trim();
  return out;
}

void sendOk(const String &msg = "") {
  Serial.print("OK");
  if (msg.length()) {
    Serial.print(' ');
    Serial.print(msg);
  }
  Serial.println();
}

void sendErr(const String &msg) {
  Serial.print("ERR ");
  Serial.println(msg);
}

void handleI2CScan() {
  Wire.begin();
  Serial.print("I2C");
  int count = 0;
  for (byte address = 1; address < 127; address++) {
    Wire.beginTransmission(address);
    byte error = Wire.endTransmission();
    if (error == 0) {
      Serial.print(' ');
      Serial.print("0x");
      if (address < 16) Serial.print('0');
      Serial.print(address, HEX);
      count++;
    }
  }
  Serial.print(" COUNT=");
  Serial.println(count);
}

void handleCommand(String cmdLine) {
  cmdLine.trim();
  if (!cmdLine.length()) return;

  String rest = cmdLine;
  String cmd = nextToken(rest);
  cmd.toUpperCase();

  if (cmd == "PING") {
    Serial.println("EMBEDLAB_AGENT 1.0");
    return;
  }

  if (cmd == "PINMODE") {
    String pinToken = nextToken(rest);
    String modeToken = nextToken(rest);
    modeToken.toUpperCase();
    int pin = parsePin(pinToken);
    if (modeToken == "OUTPUT") pinMode(pin, OUTPUT);
    else if (modeToken == "INPUT") pinMode(pin, INPUT);
    else if (modeToken == "INPUT_PULLUP") pinMode(pin, INPUT_PULLUP);
    else { sendErr("BAD_MODE"); return; }
    sendOk("PINMODE");
    return;
  }

  if (cmd == "DWRITE") {
    int pin = parsePin(nextToken(rest));
    int value = nextToken(rest).toInt();
    digitalWrite(pin, value ? HIGH : LOW);
    sendOk("DWRITE");
    return;
  }

  if (cmd == "DREAD") {
    int pin = parsePin(nextToken(rest));
    int value = digitalRead(pin);
    Serial.print("DREAD ");
    Serial.println(value);
    return;
  }

  if (cmd == "AREAD") {
    int pin = parsePin(nextToken(rest));
    int value = analogRead(pin);
    Serial.print("AREAD ");
    Serial.println(value);
    return;
  }

  if (cmd == "PWM") {
    int pin = parsePin(nextToken(rest));
    int value = constrain(nextToken(rest).toInt(), 0, 255);
    analogWrite(pin, value);
    sendOk("PWM");
    return;
  }

  if (cmd == "TONE") {
    int pin = parsePin(nextToken(rest));
    int freq = nextToken(rest).toInt();
    int duration = nextToken(rest).toInt();
    if (duration > 0) tone(pin, freq, duration);
    else tone(pin, freq);
    sendOk("TONE");
    return;
  }

  if (cmd == "NOTONE") {
    int pin = parsePin(nextToken(rest));
    noTone(pin);
    sendOk("NOTONE");
    return;
  }

  if (cmd == "I2C_SCAN") {
    handleI2CScan();
    return;
  }

  if (cmd == "RESET_OUTPUTS") {
    for (int p = 2; p <= 13; p++) {
      pinMode(p, OUTPUT);
      digitalWrite(p, LOW);
    }
    sendOk("RESET_OUTPUTS");
    return;
  }

  sendErr("UNKNOWN_COMMAND");
}

void setup() {
  Serial.begin(115200);
  Wire.begin();
  delay(500);
  Serial.println("EMBEDLAB_AGENT_READY 1.0");
}

void loop() {
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\n' || c == '\r') {
      if (lineBuffer.length()) {
        handleCommand(lineBuffer);
        lineBuffer = "";
      }
    } else {
      lineBuffer += c;
      if (lineBuffer.length() > 120) {
        lineBuffer = "";
        sendErr("LINE_TOO_LONG");
      }
    }
  }
}
