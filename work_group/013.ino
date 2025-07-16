#define LED_BUILTIN 2 // ประกาศตัวแปรledที่ขาที่13

void setup() {
  pinMode(LED_BUILTIN, OUTPUT); //กำหนดให้ขาพินที่13ส่งสัญญาณ
  Serial.begin(9600);
  Serial.println("พิมพ์ 1 เพื่อปิด LED");//แสดงข้อความขึ้นบรรทัดใหม่
  Serial.println("พิมพ์ 2 เพื่อเปิด LED");//แสดงข้อความขึ้นบรรทัดใหม่
  Serial.println("พิมพ์ 3 เพื่อกระพริบ LED");//แสดงข้อความขึ้นบรรทัดใหม่
}

void loop() {
  if (Serial.available() > 0) { //ตรวจสอบว่าค่าที่รับมามากกว่า0หรือไม่
    char input = Serial.read();//อ่านค่าจากตัวแปรinput ที่เป็นchar
    int num = input - '0'; //กำหนดตัวแปรintชื่อnumให้เท่ากับตัวแปรinput เพื่อแปลงจากinputที่เป็นcharเป็นint

   
    
    if (num == 1) { //ตรวจสอบถ้า numมีค่าเท่ากับ1
      digitalWrite(LED_BUILTIN, 0); //สั่งให้ขาที่13ส่งสัญญาณออกมาโดยไม่โดยไม่จ่ายไฟ
      Serial.println("LED ถูกปิดแล้ว"); //แสดงข้อความ
    } else if (num == 2) { //ตรวจสอบถ้า numมีค่าเท่ากับ2
      digitalWrite(LED_BUILTIN, 1); //สั่งให้ขาที่13ส่งสัญญาณออกมาโดยจ่ายไฟออก
      Serial.println("LED ถูกเปิดแล้ว"); //แสดงข้อความ
    } else if (num == 3) { //ตรวจสอบถ้า numมีค่าเท่ากับ3
      Serial.println("LED กำลังกระพริบ 5 ครั้ง"); //แสดงข้อความ
      for (int i = 0; i < 5; i++) { // พอเข้าเงื่อนไขเลข3 สั่งให้ทำลูปนี้5ครั้ง
        digitalWrite(LED_BUILTIN, 1); //สั่งให้ขาที่13ส่งสัญญาณออกมาโดยจ่ายไฟออก
        delay(300); //หน่วงเวลา
        digitalWrite(LED_BUILTIN, 0);//สั่งให้ขาที่13ส่งสัญญาณออกมาโดยไม่โดยไม่จ่ายไฟ
        delay(300);//หน่วงเวลา
      }
    } else {
      Serial.println("กรุณาเลือกแค่ 1-3 เท่านั้น");//ถ้าตรวจสอบแล้วไม่เข้าเงื่อนไขทั้งสามข้อข้างบนให้แสดงข้อความนี้
    }

    // แสดงเมนูอีกครั้ง
    Serial.println(); 
    Serial.println("เลือกเมนูใหม่:");
    Serial.println("1. ปิด LED");
    Serial.println("2. เปิด LED");
    Serial.println("3. กระพริบ LED");
  }
}