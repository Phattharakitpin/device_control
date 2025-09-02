#include <ESP32Servo.h>        // เรียกใช้ไลบรารีสำหรับควบคุม Servo บน ESP32

Servo myservo;                 // สร้างอ็อบเจกต์ servo ชื่อ myservo
String command;                // สร้างตัวแปร String สำหรับเก็บค่าคำสั่งที่รับมาจาก Serial

void setup() {
  Serial.begin(9600);          // เริ่มต้นการสื่อสาร Serial ที่ baudrate 9600
  myservo.attach(22);          // กำหนดขาควบคุม Servo ใช้ขา GPIO 22
  pinMode(2, OUTPUT);          // กำหนดขา GPIO 2 ให้เป็นเอาต์พุต (ใช้ต่อกับ LED)
}

void loop() {
  if (Serial.available()) {                        // ตรวจสอบว่ามีข้อมูลส่งเข้ามาทาง Serial หรือไม่
    String command = Serial.readStringUntil('\n'); // อ่านข้อมูลจาก Serial จนกว่าจะเจอ '\n' (ขึ้นบรรทัดใหม่)
    command.trim();                                // ตัดช่องว่าง (space/enter) ที่เกินออกไป

    if (command == "15") {                         // ถ้าข้อมูลที่รับมาเป็น "15"
      Serial.println("Servo Motor => 15");         // แสดงข้อความใน Serial Monitor
      myservo.write(15);                           // หมุน Servo ไปที่มุม 15 องศา
      blinkLED();                                  // กระพริบ LED แบบเร็ว
    } 
    else if (command == "30") {                    // ถ้าข้อมูลที่รับมาเป็น "30"
      Serial.println("Servo Motor => 30");
      myservo.write(30);                           // หมุน Servo ไปที่ 30 องศา
      blinkLED();                                  // กระพริบ LED แบบเร็ว
    } 
    else if (command == "45") {                    // ถ้าข้อมูลที่รับมาเป็น "45"
      Serial.println("Servo Motor => 45");
      myservo.write(45);                           // หมุน Servo ไปที่ 45 องศา
      blinkLED();                                  // กระพริบ LED แบบเร็ว
    } 
    else if (command == "90") {                    // ถ้าข้อมูลที่รับมาเป็น "90"
      Serial.println("Servo Motor => 90");
      myservo.write(90);                           // หมุน Servo ไปที่ 90 องศา
      digitalWrite(2, HIGH);                       // เปิด LED ค้างไว้ (ไม่กระพริบ)
    }
    else if (command == "125") {                   // ถ้าข้อมูลที่รับมาเป็น "125"
      Serial.println("Servo Motor => 125");
      myservo.write(125);                          // หมุน Servo ไปที่ 125 องศา
      secLED();                                    // กระพริบ LED ช้า (ทุก 2 วินาที)
    }
    else if (command == "135") {                   // ถ้าข้อมูลที่รับมาเป็น "135"
      Serial.println("Servo Motor => 135");
      myservo.write(135);                          // หมุน Servo ไปที่ 135 องศา
      secLED();                                    // กระพริบ LED ช้า
    }
    else if (command == "150") {                   // ถ้าข้อมูลที่รับมาเป็น "150"
      Serial.println("Servo Motor => 150");
      myservo.write(150);                          // หมุน Servo ไปที่ 150 องศา
      secLED();                                    // กระพริบ LED ช้า
    }
    else if (command == "OFF"){                    // ถ้าข้อมูลที่รับมาเป็น "OFF"
      Serial.println("Servo Motor => 0");
      myservo.write(0);                            // หมุน Servo กลับไปที่ 0 องศา
      digitalWrite(2, LOW);                        // ปิด LED
    }
    delay(1000);                                   // หน่วงเวลา 1 วินาทีเพื่อไม่ให้ loop ทำงานเร็วเกินไป
  }
}


void blinkLED(){                                   // ฟังก์ชันสำหรับทำให้ LED กระพริบเร็ว
  
  for(int i = 0; i<5; i++){                        // ทำซ้ำ 5 รอบ
    digitalWrite(2, HIGH);                         // เปิด LED
    delay(400);                                    // หน่วงเวลา 0.4 วินาที
    digitalWrite(2, LOW);                          // ปิด LED
    delay(400);                                    // หน่วงเวลา 0.4 วินาที
  }
}

void secLED(){                                     // ฟังก์ชันสำหรับทำให้ LED กระพริบช้า
  for(int i = 0; i<5; i++){                        // ทำซ้ำ 5 รอบ
    digitalWrite(2, HIGH);                         // เปิด LED
    delay(2000);                                   // หน่วงเวลา 2 วินาที
    digitalWrite(2, LOW);                          // ปิด LED
    delay(2000);                                   // หน่วงเวลา 2 วินาที
  }
}
