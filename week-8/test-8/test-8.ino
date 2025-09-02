#include <ESP32Servo.h>
Servo myservo;
String command;          // เก็บคำสั่งล่าสุด
unsigned long previousMillis = 0; //เก็บเวลาที่พึ่งกระพิบไฟ 
const long interval = 3000 ; // 0.4 วินาที เก็บเวลาเอาไว้กระพิบ
bool ledState = LOW;       // สถานะไฟ

void setup() {
  Serial.begin(9600);
  myservo.attach(32);
  pinMode(2, OUTPUT);
}

void loop() {
  // อ่าน Serial
  if (Serial.available()) {
    command = Serial.readStringUntil('\n');
    command.trim();

    // คำสั่งปรับมุม
    if (command == "15" || command == "30" || command == "60" || 
        command == "90" || command == "115"|| command == "125"|| command == "145") {
      myservo.write(command.toInt());

    } else if (command == "15" || command == "30" || command == "60" || 
        command == "90" || command == "115"|| command == "125") {
      myservo.write(command.toInt());
      digitalWrite(2, HIGH);   // ไฟติดค้าง
      delay(3000);
      digitalWrite(2, HIGH);   // ไฟติดค้าง
      delay(3000);     
      
    } else if (command == "0") {
      myservo.write(0);
      digitalWrite(2, LOW);    // ไฟดับ
    }
  }

  // จัดการไฟกระพริบ (สำหรับคำสั่ง 15–90)
  if (command == "145") {
    unsigned long currentMillis = millis();
    if (currentMillis - previousMillis >= interval) {
      previousMillis = currentMillis;
      ledState = !ledState;              // สลับสถานะ
      digitalWrite(2, ledState);
    }
  }
}