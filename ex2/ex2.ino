//EX2

void setup() {
  Serial.begin(9600);
  Serial.println("Start");
}

void loop() {
  for(int greenRoad=1; greenRoad<=4; greenRoad++) {
    Road(greenRoad);
    delay(3000);  // รอระหว่างรอบเพื่อให้ดูผลชัดเจน
  }
  Serial.println("Phattharakit Pinkaew")
  Serial.println("&");
  Serial.println("Loop back to start");
  
  delay(3000);  // รอก่อนเริ่ม loop ใหม่
}

//Road Circuit
void Road(int greenRoad){
  for(int road=1; road<=4; road++){
    Serial.println(road);
    if(road == greenRoad){
      Serial.println("is Green");
    } else {
      Serial.println("is Red");
    }
  }
}
