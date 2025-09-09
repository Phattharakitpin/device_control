#include <ESP32Servo.h>

Servo myservo;

void setup() {
  Serial.begin(9600);
  myservo.attach(32);  // GPIO 32
}

void loop() {
  if (Serial.available()) {
    String data = Serial.readStringUntil('\n'); 
    int val = data.toInt();

    // รีเซ็ตมุมถ้าเกิน 90
    if (val < 0) val = 0;
    if (val > 90) val = 0;

    myservo.write(val);
  }
}