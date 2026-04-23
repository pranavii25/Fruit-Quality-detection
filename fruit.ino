#include <Wire.h>
#include <LiquidCrystal_I2C.h>

#define BUZZER_PIN 14

// I2C LCD address (most common: 0x27 or 0x3F)
LiquidCrystal_I2C lcd(0x27, 16, 2);

String incomingData = "";

void setup() {
  Serial.begin(9600);

  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);

  lcd.init();
  lcd.backlight();

  lcd.setCursor(0, 0);
  lcd.print("Fruit Quality");
  lcd.setCursor(0, 1);
  lcd.print("System Ready");
  delay(2000);
  lcd.clear();

  Serial.println("ESP32 Ready");
}

void loop() {
  if (Serial.available()) {
    incomingData = Serial.readStringUntil('\n');
    incomingData.trim();

    // Expected format:
    // Fresh,68.84,5-7,SAFE
    // Rotten,88.10,0,NOT_EATABLE

    int i1 = incomingData.indexOf(',');
    int i2 = incomingData.indexOf(',', i1 + 1);
    int i3 = incomingData.indexOf(',', i2 + 1);

    if (i1 == -1 || i2 == -1 || i3 == -1) return;

    String quality = incomingData.substring(0, i1);
    String confidence = incomingData.substring(i1 + 1, i2);
    String days = incomingData.substring(i2 + 1, i3);
    String status = incomingData.substring(i3 + 1);

    // -------- LCD DISPLAY --------
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Q:");
    lcd.print(quality);

    lcd.setCursor(10, 0);
    lcd.print(confidence.substring(0, 4));
    lcd.print("%");

    lcd.setCursor(0, 1);
    lcd.print("Days:");
    lcd.print(days);

    // -------- BUZZER LOGIC --------
    if (quality == "Rotten") {
      digitalWrite(BUZZER_PIN, HIGH);
      delay(2000);                 // buzzer ON for 2 sec
      digitalWrite(BUZZER_PIN, LOW);
    } else {
      digitalWrite(BUZZER_PIN, LOW);
    }

    // Debug
    Serial.println("Received: " + incomingData);
  }
}
