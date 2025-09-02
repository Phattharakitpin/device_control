#include <ESP32Servo.h>

Servo myservo;
char user_input;

void setup() {
  Serial.begin(9600);
  myservo.attach(22);
  Serial.println("Enter angle: 1, 2, 3 or 4");
}

void loop() {
  if (Serial.available() > 0) {
    user_input = Serial.read();
    if (user_input == '0') {
      Serial.println("Servo Motor => 0");
      myservo.write(0);
    } 
    else if (user_input == '1') {
      Serial.println("Servo Motor => 90");
      myservo.write(90);
    } 
    else if (user_input == '2') {
      Serial.println("Servo Motor => 180");
      myservo.write(180);
    } 
    else if (user_input == '3') { 
      Serial.println("Servo Motor => 30");
      myservo.write(30);
    }else if (user_input == '4') { 
      Serial.println("Servo Motor => 120");
      myservo.write(120);
      }
    delay(1000);
  }
}
