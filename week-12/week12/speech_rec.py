import re, speech_recognition as sr

stopped = False  # ธงหยุดการทำงาน

r = sr.Recognizer()
with sr.Microphone() as mic:
    r.adjust_for_ambient_noise(mic, duration=0.6)
    print("พูดว่า 'หยุด' เพื่อหยุด | 'เริ่ม' เพื่อทำงานต่อ | 'ออก' เพื่อปิด")
    print("ตัวอย่าง: 'สวัสดี หมุนมอเตอร์ ไปที่ 90 องศา'")

    while True:
        try:
            audio = r.listen(mic, timeout=6, phrase_time_limit=10)
            text = r.recognize_google(audio, language="th-TH").strip()
            print("ได้ยิน :", text)

            # ===== คำสั่งควบคุมโหมด =====
            if "ออก" in text or "ปิดโปรแกรม" in text:
                print("จบโปรแกรม ลาก่อน 👋")
                break

            if "หยุด" in text or "stop" in text.lower():
                stopped = True
                print("**หยุดการทำงานแล้ว**")
                # TODO: ใส่คำสั่งหยุดอุปกรณ์จริงตรงนี้ (เช่น ส่งสัญญาณไป ESP32)
                continue

            if "เริ่ม" in text or "ทำงานต่อ" in text or "start" in text.lower():
                stopped = False
                print("**กลับมาทำงานต่อแล้ว**")
                # TODO: สั่งให้อุปกรณ์เริ่มทำงานต่อ
                continue

            # ถ้าอยู่โหมดหยุด ไม่ประมวลผลคำสั่งอื่น
            if stopped:
                print("(หยุดอยู่) ถ้าจะทำงานต่อให้พูดว่า 'เริ่ม'")
                continue

            # ===== โหมดเดิม: เริ่มด้วย 'สวัสดี' แล้วดึงเลขมุม =====
            if text.startswith("สวัสดี"):
                cmd = text.replace("สวัสดี", "", 1).strip()
                m = re.search(r"(\d+)", cmd)
                angle = int(m.group(1)) if m else None
                print("สวัสดี : ", cmd, " | มุม : ", angle)

                # TODO: ถ้าต้องการ ส่ง angle ไปอุปกรณ์ที่นี่
                # เช่น ส่ง Serial: "ANGLE <ค่า>"

        except sr.WaitTimeoutError:
            print("ไม่มีสียงพูดมาได้เลยค่ะ")
        except sr.UnknownValueError:
            print("โอเครพูดมาได้เลยค่ะ.....")
        except Exception as e:
            print("เกิดข้อผิดพลาด:", e)
    