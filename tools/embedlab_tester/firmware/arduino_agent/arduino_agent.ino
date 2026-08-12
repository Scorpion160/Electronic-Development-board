/*
  EmbedLab Board Tester - Arduino serial agent

  Version pour Arduino Uno, Nano et Mega.
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
    PCF8574_WRITE <addr> <value>
    PCF8574_WALK <addr> <delay_ms>
    SHIFT595 <ds> <sh> <st> <value>
    WALK <delay_ms> <pin1> <pin2> ...
    LCD4_TEST <rs> <en> <d4> <d5> <d6> <d7>
    RESET_OUTPUTS

  Exemples :
    PINMODE 5 OUTPUT
    DWRITE 5 1
    AREAD A0
    SHIFT595 5 6 7 0xAA
    LCD4_TEST 2 3 4 5 6 7
*/

#include <Arduino.h>
#include <Wire.h>
#include <LiquidCrystal.h>

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

long parseNumber(const String &token) {
  String t = token;
  t.trim();
  t.toLowerCase();
  if (t.startsWith("0x")) {
    return strtol(t.c_str(), NULL, 16);
  }
  if (t.startsWith("0b")) {
    long value = 0;
    for (unsigned int i = 2; i < t.length(); i++) {
      value <<= 1;
      if (t.charAt(i) == '1') value |= 1;
    }
    return value;
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

void handlePCF8574Write(String &rest) {
  byte address = (byte)parseNumber(nextToken(rest));
  byte value = (byte)parseNumber(nextToken(rest));
  Wire.beginTransmission(address);
  Wire.write(value);
  byte error = Wire.endTransmission();
  if (error == 0) sendOk("PCF8574_WRITE");
  else sendErr("PCF8574_WRITE_FAIL");
}

void handlePCF8574Walk(String &rest) {
  byte address = (byte)parseNumber(nextToken(rest));
  int delayMs = (int)parseNumber(nextToken(rest));
  if (delayMs <= 0) delayMs = 200;
  for (byte i = 0; i < 8; i++) {
    byte value = (byte)(1 << i);
    Wire.beginTransmission(address);
    Wire.write(value);
    byte error = Wire.endTransmission();
    if (error != 0) {
      sendErr("PCF8574_WALK_FAIL");
      return;
    }
    delay(delayMs);
  }
  Wire.beginTransmission(address);
  Wire.write((byte)0x00);
  Wire.endTransmission();
  sendOk("PCF8574_WALK");
}

void handleShift595(String &rest) {
  int ds = parsePin(nextToken(rest));
  int sh = parsePin(nextToken(rest));
  int st = parsePin(nextToken(rest));
  byte value = (byte)parseNumber(nextToken(rest));

  pinMode(ds, OUTPUT);
  pinMode(sh, OUTPUT);
  pinMode(st, OUTPUT);
  digitalWrite(st, LOW);
  shiftOut(ds, sh, MSBFIRST, value);
  digitalWrite(st, HIGH);
  sendOk("SHIFT595");
}

void handleWalk(String &rest) {
  int delayMs = (int)parseNumber(nextToken(rest));
  if (delayMs <= 0) delayMs = 250;
  int pins[24];
  int count = 0;
  while (rest.length() && count < 24) {
    pins[count++] = parsePin(nextToken(rest));
  }
  if (count == 0) {
    sendErr("WALK_NO_PIN");
    return;
  }
  for (int i = 0; i < count; i++) {
    pinMode(pins[i], OUTPUT);
    digitalWrite(pins[i], LOW);
  }
  for (int i = 0; i < count; i++) {
    digitalWrite(pins[i], HIGH);
    delay(delayMs);
    digitalWrite(pins[i], LOW);
    delay(80);
  }
  sendOk("WALK");
}

void handleLCD4Test(String &rest) {
  int rs = parsePin(nextToken(rest));
  int en = parsePin(nextToken(rest));
  int d4 = parsePin(nextToken(rest));
  int d5 = parsePin(nextToken(rest));
  int d6 = parsePin(nextToken(rest));
  int d7 = parsePin(nextToken(rest));

  LiquidCrystal lcd(rs, en, d4, d5, d6, d7);
  lcd.begin(16, 2);
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("EMBEDLAB OK");
  lcd.setCursor(0, 1);
  lcd.print("LCD 1602 TEST");
  sendOk("LCD4_TEST");
}

void handleCommand(String cmdLine) {
  cmdLine.trim();
  if (!cmdLine.length()) return;

  String rest = cmdLine;
  String cmd = nextToken(rest);
  cmd.toUpperCase();

  if (cmd == "PING") {
    Serial.println("EMBEDLAB_AGENT 1.1");
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
    int value = constrain((int)parseNumber(nextToken(rest)), 0, 255);
    analogWrite(pin, value);
    sendOk("PWM");
    return;
  }

  if (cmd == "TONE") {
    int pin = parsePin(nextToken(rest));
    int freq = (int)parseNumber(nextToken(rest));
    int duration = (int)parseNumber(nextToken(rest));
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

  if (cmd == "PCF8574_WRITE") {
    handlePCF8574Write(rest);
    return;
  }

  if (cmd == "PCF8574_WALK") {
    handlePCF8574Walk(rest);
    return;
  }

  if (cmd == "SHIFT595") {
    handleShift595(rest);
    return;
  }

  if (cmd == "WALK") {
    handleWalk(rest);
    return;
  }

  if (cmd == "LCD4_TEST") {
    handleLCD4Test(rest);
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
  Serial.println("EMBEDLAB_AGENT_READY 1.1");
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
      if (lineBuffer.length() > 160) {
        lineBuffer = "";
        sendErr("LINE_TOO_LONG");
      }
    }
  }
}
