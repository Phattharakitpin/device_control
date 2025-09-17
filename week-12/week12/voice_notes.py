# voice_notes.py — ต้องพูด "สวัสดี" ก่อน ถึงจะสั่งจดโน้ตได้ + คำสั่งหยุดการทำงาน
# Python 3.10

import os, re, sys
from datetime import datetime, timedelta
import speech_recognition as sr

# ============ Config ============
USE_DAILY_FILE = False          # True = notes-YYYYMMDD.txt, False = notes.txt
LOG_DIR = "logs"                # โฟลเดอร์เก็บไฟล์โน้ต
AUTO_NOTE_MODE = False          # โหมดออโต้: จดทุกประโยคที่พูด (เมื่อปลดล็อกแล้วเท่านั้น)
USE_BUDDHIST_YEAR = False       # True = แสดงปี พ.ศ., False = ค.ศ.
SHOW_TIME_ON_HEARD = True       # พิมพ์วันเวลาในคอนโซลทุกครั้งที่ได้ยิน

# ---- Wake-word / Lock ----
REQUIRE_WAKE_WORD = True
WAKE_WORDS = ("สวัสดี", "hello")      # ต้องพูดคำพวกนี้เพื่อ "ปลดล็อก"
LOCK_WORDS = ("หยุดฟัง", "พักก่อน", "ลาก่อน", "goodbye")  # ล็อกกลับ
WAKE_TIMEOUT_SEC = 180                 # ปลดล็อกค้างไว้กี่วินาที (None/0 = ไม่หมดอายุ)

# ---- คำสั่งเสียง เปิด/ปิด โหมดออโต้ ----
CONTROL_START_WORDS = ("เริ่มจดโน้ต", "เริ่มบันทึกโน้ต", "note mode on", "start note")
CONTROL_STOP_WORDS  = ("หยุดจดโน้ต", "หยุดบันทึกโน้ต", "note mode off", "stop note")

# ---- คำสั่งหยุดการทำงาน (ปิดโปรแกรม) ----
EXIT_WORDS = (
    "หยุดการทำงาน", "หยุดทำงาน", "เลิกทำงาน", "ปิดโปรแกรม",
    "ออกจากโปรแกรม", "จบการทำงาน", "exit", "quit", "shutdown", "terminate"
)

# ---- รูปแบบคำสั่งจดโน้ตแบบชี้ชัด (TH/EN) ----
TH_NOTE = re.compile(r"^\s*(?:สั่งงาน\s*)?โน้ต\s*[:\-]?\s*(.+)$")
EN_NOTE = re.compile(r"^\s*note\s*[:\-]?\s*(.+)$", re.IGNORECASE)

# ============ Utils ============
TH_DAY = ("จันทร์","อังคาร","พุธ","พฤหัสบดี","ศุกร์","เสาร์","อาทิตย์")
def format_datetime_th(dt: datetime, use_be: bool = False) -> str:
    day_name = TH_DAY[dt.weekday()]
    year = dt.year + 543 if use_be else dt.year
    return f"{day_name} {dt:%d/%m}/{year} {dt:%H:%M:%S}"

def _notes_path() -> str:
    fname = f"notes-{datetime.now():%Y%m%d}.txt" if USE_DAILY_FILE else "notes.txt"
    if LOG_DIR:
        os.makedirs(LOG_DIR, exist_ok=True)
        return os.path.join(LOG_DIR, fname)
    return fname

def extract_note_payload(text: str) -> str | None:
    m = TH_NOTE.match(text) or EN_NOTE.match(text)
    return m.group(1).strip() if m else None

def append_note_line(message: str) -> None:
    ts = format_datetime_th(datetime.now(), USE_BUDDHIST_YEAR)
    path = _notes_path()
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {message}\n")
    print(f"📝 บันทึกแล้ว ({ts}) → {path}", flush=True)

def handle_note_command(text: str) -> bool:
    payload = extract_note_payload(text)
    if payload:
        append_note_line(payload)
        return True
    return False

def maybe_auto_note(text: str) -> bool:
    """
    1) เปิด/ปิดโหมดออโต้
    2) คำสั่ง 'โน้ต …/Note …'
    3) ถ้าออโต้เปิดอยู่ -> จดทุกอย่าง
    คืน True ถ้ามีการจดหรือจัดการบางอย่างแล้ว
    """
    global AUTO_NOTE_MODE
    norm = text.strip().lower()

    # 1) Toggle auto-note mode
    if any(norm.startswith(cmd.lower()) for cmd in CONTROL_START_WORDS):
        AUTO_NOTE_MODE = True
        print("🟢 Auto-note: ON — จะจดทุกประโยคที่พูด (ขณะปลดล็อก)", flush=True)
        return True
    if any(norm.startswith(cmd.lower()) for cmd in CONTROL_STOP_WORDS):
        AUTO_NOTE_MODE = False
        print("🔴 Auto-note: OFF — จะจดเฉพาะที่สั่ง 'โน้ต'", flush=True)
        return True

    # 2) Explicit note command
    if handle_note_command(text):
        print("✅ จดโน้ต (แบบสั่งงาน)", flush=True)
        return True

    # 3) Auto-note all utterances
    if AUTO_NOTE_MODE and norm:
        append_note_line(text.strip())
        print("✅ จดโน้ต (ออโต้หลังพูด)", flush=True)
        return True

    return False

# ======== Exit helpers (ปิดโปรแกรม) ========
def is_exit_command(text: str) -> bool:
    norm = text.strip().lower()
    return any(norm.startswith(cmd.lower()) for cmd in EXIT_WORDS)

def graceful_exit():
    # จดบรรทัดสรุปในไฟล์โน้ต แล้วปิดโปรแกรมอย่างสุภาพ
    try:
        append_note_line("— จบเซสชัน —")
    except Exception:
        pass
    print("👋 จบการทำงาน เรียบร้อย บ๊ายบาย", flush=True)

# ============ Wake state ============
_wake_until: datetime | None = None

def _is_awake() -> bool:
    if not REQUIRE_WAKE_WORD:
        return True
    if _wake_until is None:
        return False
    return datetime.now() < _wake_until

def _extend_wake():
    global _wake_until
    if not REQUIRE_WAKE_WORD:
        return
    if WAKE_TIMEOUT_SEC and WAKE_TIMEOUT_SEC > 0:
        _wake_until = datetime.now() + timedelta(seconds=WAKE_TIMEOUT_SEC)
    else:
        _wake_until = datetime.max

def _wake():
    _extend_wake()
    left = "ไม่จำกัดเวลา" if _wake_until == datetime.max else f"{WAKE_TIMEOUT_SEC}s"
    print(f"🔓 ปลดล็อกแล้ว (รับคำสั่งจดโน้ต) — หมดอายุใน {left}", flush=True)

def _sleep():
    global _wake_until
    _wake_until = None
    print("🔒 ล็อกแล้ว — ต้องพูด 'สวัสดี' เพื่อปลดล็อกอีกครั้ง", flush=True)

def _strip_prefix(text: str, prefix: str) -> str:
    if text.lower().startswith(prefix.lower()):
        return text[len(prefix):].lstrip(" ,:;-—")
    return text

def handle_with_wake(text: str) -> bool:
    """
    จัดการ wake/lock + ส่งต่อไปยัง maybe_auto_note ถ้า 'ปลดล็อก' แล้ว
    คืน True ถ้าเราจัดการบางอย่าง (ปลดล็อก/ล็อก/จดโน้ต) เสร็จในฟังก์ชันนี้
    คืน False ถ้ายังไม่ได้ทำอะไรเกี่ยวกับโน้ต -> เผื่อให้คำสั่งอื่นไปต่อ
    """
    norm = text.strip().lower()

    # 0) คำสั่งล็อกกลับ
    if any(norm.startswith(cmd.lower()) for cmd in LOCK_WORDS):
        _sleep()
        return True

    # 1) ตรวจ wake word
    for w in WAKE_WORDS:
        if norm.startswith(w.lower()):
            _wake()
            # ถ้าพูดแบบ "สวัสดี โน้ต …" ให้ตัด "สวัสดี" ออกแล้วประมวลผลต่อ
            remainder = _strip_prefix(text, w)
            if remainder:
                _extend_wake()
                return maybe_auto_note(remainder)
            return True  # แค่ปลดล็อกเฉยๆ

    # 2) ถ้ายังไม่ปลดล็อก → ไม่อนุญาตคำสั่งโน้ต (แต่ปล่อยให้คำสั่งอื่นๆ ไปต่อ)
    if not _is_awake():
        print("🔒 ต้องพูด 'สวัสดี' ก่อน ถึงจะเริ่มสั่งให้จดโน้ตได้", flush=True)
        return False

    # 3) ปลดล็อกอยู่ → ต่ออายุ และส่งต่อไป handler ของโน้ต
    _extend_wake()
    return maybe_auto_note(text)

# ============ Mic Loop ============
def mic_loop():
    r = sr.Recognizer()
    with sr.Microphone() as mic:
        r.adjust_for_ambient_noise(mic, duration=0.6)
        now_str = format_datetime_th(datetime.now(), USE_BUDDHIST_YEAR)
        print("🎙️ พร้อมฟัง — ต้องพูด 'สวัสดี' ก่อน แล้วค่อย 'โน้ต …' หรือเปิด/ปิดออโต้", flush=True)
        print("   ตัวอย่าง: 'สวัสดี โน้ต เปลี่ยนสายไฟเส้นที่สาม'", flush=True)
        print("   พูด 'หยุดการทำงาน' หรือ 'exit' เพื่อปิดโปรแกรม", flush=True)
        print(f"⌚ ตอนนี้: {now_str}", flush=True)

        while True:
            try:
                audio = r.listen(mic, timeout=6, phrase_time_limit=10)
                try:
                    text = r.recognize_google(audio, language="th-TH")
                except sr.UnknownValueError:
                    text = r.recognize_google(audio, language="en-US")

                ts = format_datetime_th(datetime.now(), USE_BUDDHIST_YEAR)
                if SHOW_TIME_ON_HEARD:
                    print(f"[{ts}] ได้ยิน: {text}", flush=True)
                else:
                    print("ได้ยิน:", text, flush=True)

                # ====== เช็คคำสั่ง 'หยุดการทำงาน' ก่อนเสมอ (ไม่ต้องปลดล็อก) ======
                if is_exit_command(text):
                    graceful_exit()
                    break  # ออกจากลูปเพื่อปิดโปรแกรม

                # ====== กรองด้วย wake word ก่อนสำหรับการจดโน้ต ======
                if handle_with_wake(text):
                    continue

                # ====== คำสั่งอื่น ๆ ของคุณวางต่อจากนี้ ======
                # if text.startswith("อย่างอื่น"): ...

            except sr.WaitTimeoutError:
                print("…เงียบอยู่ ไม่มีเสียงเข้าไมค์", flush=True)
            except sr.UnknownValueError:
                print("ยังฟังไม่ชัด ลองพูดใหม่ได้เลย", flush=True)
            except KeyboardInterrupt:
                print("\n⏹️ ถูกยกเลิกจากคีย์บอร์ด (Ctrl+C) — ปิดโปรแกรม", flush=True)
                break
            except Exception as e:
                print("❗ Error:", e, flush=True)

# ============ Main ============
if __name__ == "__main__":
    # โหมดทดสอบเร็วจาก CLI
    #   python voice_notes.py --test "สวัสดี โน้ต เปลี่ยนสายไฟเส้นที่สาม"
    #   python voice_notes.py --test "หยุดการทำงาน"
    if len(sys.argv) > 1 and sys.argv[1] in ("--test", "-t"):
        payload = " ".join(sys.argv[2:])
        if payload:
            if is_exit_command(payload):
                graceful_exit()
            elif not handle_with_wake(payload):
                print("ℹ️ (TEST) ยังไม่จด — เพราะยังไม่ปลดล็อกด้วย 'สวัสดี'", flush=True)
        sys.exit(0)

    print("🚀 Booting voice notes…", flush=True)
    mic_loop()
