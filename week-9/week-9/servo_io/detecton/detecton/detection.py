import face_recognition
import cv2
import serial
import time
import numpy as np
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ---------------------- ตั้งค่า Serial ----------------------
arduino = serial.Serial('COM3', 9600, timeout=1)
time.sleep(2)

# ---------------------- โหลดรูปเจ้าของหลายคน ----------------------
known_face_encodings = []
known_face_names = []

# เก็บเป็นอาเรย์ [ไฟล์รูป, ชื่อ]
people = [
    ("user.jpg", "Phattharakit pinkaew"),
    ("fah.jpg", "Thirapaht Oumkratok"),
]

for img_path, name in people:
    image = face_recognition.load_image_file(img_path)
    encoding = face_recognition.face_encodings(image)
    known_face_encodings.append(encoding[0])
    known_face_names.append(name)

# ---------------------- เปิดกล้อง ----------------------
video_capture = cv2.VideoCapture(0)

while True:
    ret, frame = video_capture.read()
    if not ret:
        continue

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    rgb_frame = np.array(rgb_frame, dtype=np.uint8)

    face_locations = face_recognition.face_locations(rgb_frame)
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    if len(face_encodings) == 0:
        # ถ้าไม่เจอหน้าเลย → ส่ง C ไปล็อก
        arduino.write(b'C')
    else:
        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.35)
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)

            best_match_index = np.argmin(face_distances)

            if matches[best_match_index]:
                name = known_face_names[best_match_index]
                color = (0, 255, 0)  # เขียว
                arduino.write(b'O')  # ปลดล็อก
            else:
                name = "Unknown"
                color = (0, 0, 255)  # แดง
                arduino.write(b'C')  # ล็อก

            # วาดกรอบ + ชื่อ
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX,
                        0.9, color, 2)

    cv2.imshow('Video', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

video_capture.release()
arduino.close()
cv2.destroyAllWindows()