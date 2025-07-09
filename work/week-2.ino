#define LED_BUILTIN 2
void setup() {
  Serial.begin(9600);      
  pinMode(LED_BUILTIN, OUTPUT);     
}

void loop() {
  Serial.print("สวัสดี Phattharakit pinkarw\n");   
  digitalWrite(LED_BUILTIN, 1);
  Serial.print("light ...");
  delay(1000);

  digitalWrite(LED_BUILTIN, 0);
  Serial.print("not light ...");
  delay(1000);
}