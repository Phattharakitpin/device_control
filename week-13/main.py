# -*- coding: utf-8 -*-
import sys, time, math, traceback
import cv2
import serial
import serial.tools.list_ports
import mediapipe as mp

from PyQt5 import QtCore, QtGui, QtWidgets

# ========================= Serial Manager =========================
class SerialManager:
    def __init__(self, port='COM3', baud=9600):
        self.port = port
        self.baud = baud
        self.ser = None
        self._connect()

    def _connect(self):
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=1)
            time.sleep(2)  # allow Arduino to reset
            print(f"[Serial] Connected to {self.port} @ {self.baud}")
        except Exception as e:
            print(f"[Serial] Could not open {self.port}: {e}")
            self.ser = None

    def is_open(self):
        return self.ser is not None and self.ser.is_open

    def send_angle(self, angle: int):
        """Send integer angle (e.g., 0..180) followed by newline."""
        angle = max(0, min(180, int(angle)))
        msg = f"{angle}\n".encode('utf-8')
        try:
            if not self.is_open():
                self._connect()
            if self.is_open():
                self.ser.write(msg)
        except Exception as e:
            print(f"[Serial] Write failed: {e}")

    def close(self):
        try:
            if self.ser and self.ser.is_open:
                self.ser.close()
                print("[Serial] Closed")
        except:
            pass


# ========================= Utilities =========================
def cvimg_to_qimage(frame_bgr):
    """Convert OpenCV BGR image to QImage for QLabel."""
    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    h, w, ch = frame_rgb.shape
    bytes_per_line = ch * w
    return QtGui.QImage(frame_rgb.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)

def open_camera_reliably(preferred_index=0, warmup_frames=5, width=1280, height=720):
    """
    พยายามเปิดกล้องอย่างทนทาน:
    - ลองหลาย backend: CAP_DSHOW, CAP_MSMF, CAP_ANY (บน Windows)
    - ลองหลาย index: preferred_index, 0..3
    - ตั้งค่า resolution และ warm-up เฟรม
    """
    backends = []
    # ลำดับ backend ที่มักได้ผลบน Windows
    if hasattr(cv2, "CAP_DSHOW"):
        backends.append(cv2.CAP_DSHOW)
    if hasattr(cv2, "CAP_MSMF"):
        backends.append(cv2.CAP_MSMF)
    backends.append(cv2.CAP_ANY)

    tried = []
    indices = [preferred_index] + [i for i in range(4) if i != preferred_index]

    for idx in indices:
        for be in backends:
            cap = cv2.VideoCapture(idx, be)
            if cap.isOpened():
                # ตั้งค่าความละเอียด (ถ้าไม่ได้ก็ไม่เป็นไร)
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

                # warm-up เฟรมเล็กน้อย
                ok_warm = True
                for _ in range(warmup_frames):
                    ok, _frame = cap.read()
                    if not ok:
                        ok_warm = False
                        break
                    time.sleep(0.02)

                if ok_warm:
                    print(f"[Camera] Opened index={idx} backend={be}")
                    return cap
                else:
                    cap.release()
                    tried.append((idx, be, "warmup-failed"))
            else:
                tried.append((idx, be, "open-failed"))

    print("[Camera] Could not open any camera. Tried:", tried)
    return None


# ========================= Face Scan Worker =========================
class FaceScanWorker(QtCore.QThread):
    frame_signal = QtCore.pyqtSignal(QtGui.QImage)
    info_signal  = QtCore.pyqtSignal(str)

    def __init__(self, ser: SerialManager, parent=None, cam_index=0):
        super().__init__(parent)
        self.ser = ser
        self._running = False
        self.cam_index = cam_index
        # Use OpenCV Haar cascade (bundled with opencv)
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades +
                                                  "haarcascade_frontalface_default.xml")

    def run(self):
        self._running = True
        cap = open_camera_reliably(preferred_index=self.cam_index)
        if cap is None or not cap.isOpened():
            self.info_signal.emit("Camera not available. (โปรดเช็คสิทธิ์/ปิดโปรแกรมที่ใช้กล้องอยู่)")
            return

        sent = False
        self.info_signal.emit("Face Scan running…")

        try:
            while self._running:
                ok, frame = cap.read()
                if not ok:
                    self.info_signal.emit("Frame grab failed. (กล้องหลุด)"); break
                frame = cv2.flip(frame, 1)

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, 1.2, 5, minSize=(80, 80))

                # draw
                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

                if len(faces) > 0 and not sent:
                    # Send 90° once when a face first appears
                    self.ser.send_angle(90)
                    self.info_signal.emit("Face detected → COM3: rotate 90°")
                    sent = True

                # show
                qimg = cvimg_to_qimage(frame)
                self.frame_signal.emit(qimg)
                self.msleep(10)
        except Exception as e:
            self.info_signal.emit(f"Face worker error: {e}")
            traceback.print_exc()
        finally:
            cap.release()
            self.info_signal.emit("Face Scan stopped.")

    def stop(self):
        self._running = False
        self.wait(500)


# ========================= Hand Axis Worker =========================
class HandAxisWorker(QtCore.QThread):
    frame_signal = QtCore.pyqtSignal(QtGui.QImage)
    info_signal  = QtCore.pyqtSignal(str)

    def __init__(self, ser: SerialManager, parent=None, cam_index=0):
        super().__init__(parent)
        self.ser = ser
        self._running = False
        self.cam_index = cam_index
        self.mp_hands = mp.solutions.hands
        self.mp_draw  = mp.solutions.drawing_utils

        # Send throttling
        self._last_sent_angle = None
        self._last_sent_time = 0.0
        self._min_delta = 2          # degrees change threshold
        self._min_interval = 0.06    # ~15 Hz

    @staticmethod
    def _calc_angle(p0, p1, p2):
        # angle between vectors p0->p1 and p0->p2
        v1 = (p1[0]-p0[0], p1[1]-p0[1])
        v2 = (p2[0]-p0[0], p2[1]-p0[1])
        dot = v1[0]*v2[0] + v1[1]*v2[1]
        mag1 = math.hypot(*v1)
        mag2 = math.hypot(*v2)
        if mag1 == 0 or mag2 == 0:
            return 0.0
        cosv = max(-1.0, min(1.0, dot / (mag1 * mag2)))
        return math.degrees(math.acos(cosv))

    def _maybe_send(self, angle):
        now = time.time()
        if (self._last_sent_angle is None or
            abs(angle - self._last_sent_angle) >= self._min_delta) and \
           (now - self._last_sent_time) >= self._min_interval:
            self.ser.send_angle(int(angle))
            self._last_sent_angle = angle
            self._last_sent_time = now

    def run(self):
        self._running = True
        cap = open_camera_reliably(preferred_index=self.cam_index)
        if cap is None or not cap.isOpened():
            self.info_signal.emit("Camera not available. (โปรดเช็คสิทธิ์/ปิดโปรแกรมที่ใช้กล้องอยู่)")
            return

        self.info_signal.emit("Hand Axis running…")
        try:
            with self.mp_hands.Hands(
                min_detection_confidence=0.7,
                min_tracking_confidence=0.7,
                max_num_hands=1
            ) as hands:

                while self._running:
                    ok, frame = cap.read()
                    if not ok:
                        self.info_signal.emit("Frame grab failed. (กล้องหลุด)"); break
                    frame = cv2.flip(frame, 1)
                    h, w, _ = frame.shape

                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    res = hands.process(rgb)

                    display_angle = 0
                    if res.multi_hand_landmarks:
                        for hand in res.multi_hand_landmarks:
                            self.mp_draw.draw_landmarks(
                                frame, hand, self.mp_hands.HAND_CONNECTIONS)

                            wrist = hand.landmark[0]
                            thumb_tip = hand.landmark[4]
                            index_tip = hand.landmark[8]

                            p0 = (int(wrist.x*w), int(wrist.y*h))
                            p1 = (int(thumb_tip.x*w), int(thumb_tip.y*h))
                            p2 = (int(index_tip.x*w), int(index_tip.y*h))

                            # Compute angle and clamp 0..90 for motor
                            angle = self._calc_angle(p0, p1, p2)
                            angle = max(0.0, min(90.0, angle))
                            display_angle = angle

                            # Draw helper points
                            cv2.circle(frame, p1, 8, (255, 0, 0), -1)
                            cv2.circle(frame, p2, 8, (0, 0, 255), -1)

                            # Throttled, de-noised sending
                            self._maybe_send(angle)
                            break  # only first hand

                    cv2.putText(frame, f"Angle: {int(display_angle)} deg (0-90)",
                                (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

                    qimg = cvimg_to_qimage(frame)
                    self.frame_signal.emit(qimg)
                    self.msleep(6)
        except Exception as e:
            self.info_signal.emit(f"Hand worker error: {e}")
            traceback.print_exc()
        finally:
            cap.release()
            self.info_signal.emit("Hand Axis stopped.")

    def stop(self):
        self._running = False
        self.wait(500)


# ========================= Main Window =========================
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Face/Hand Control → COM3")
        self.resize(980, 700)

        self.ser = SerialManager(port="COM3", baud=9600)

        # Widgets
        self.video_label = QtWidgets.QLabel()
        self.video_label.setAlignment(QtCore.Qt.AlignCenter)
        self.video_label.setMinimumSize(800, 500)
        self.video_label.setStyleSheet("background:#111; color:#ccc;")

        self.btn_face  = QtWidgets.QPushButton("Face Scan (Start)")
        self.btn_hand  = QtWidgets.QPushButton("Hand Axis (Start)")
        self.status    = QtWidgets.QLabel("Ready.")
        self.status.setStyleSheet("color:#0a0;")

        # Layout
        btn_row = QtWidgets.QHBoxLayout()
        btn_row.addWidget(self.btn_face)
        btn_row.addWidget(self.btn_hand)
        wrapper = QtWidgets.QVBoxLayout()
        wrapper.addWidget(self.video_label, 1)
        wrapper.addLayout(btn_row)
        wrapper.addWidget(self.status)

        central = QtWidgets.QWidget()
        central.setLayout(wrapper)
        self.setCentralWidget(central)

        # Workers
        self.face_worker = None
        self.hand_worker = None

        # Signals
        self.btn_face.clicked.connect(self.toggle_face)
        self.btn_hand.clicked.connect(self.toggle_hand)

    # ---------- UI Helpers ----------
    def set_status(self, text, ok=True):
        self.status.setText(text)
        self.status.setStyleSheet(f"color:{'#0a0' if ok else '#f55'};")

    def show_frame(self, qimg: QtGui.QImage):
        pix = QtGui.QPixmap.fromImage(qimg).scaled(
            self.video_label.width(), self.video_label.height(),
            QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation
        )
        self.video_label.setPixmap(pix)

    # ---------- Toggle Handlers ----------
    def toggle_face(self):
        # Stop hand if running
        if self.hand_worker is not None:
            self.stop_hand()

        if self.face_worker is None:
            self.start_face()
        else:
            self.stop_face()

    def toggle_hand(self):
        # Stop face if running
        if self.face_worker is not None:
            self.stop_face()

        if self.hand_worker is None:
            self.start_hand()
        else:
            self.stop_hand()

    # ---------- Start/Stop Workers ----------
    def start_face(self):
        # เลือก index ที่อยากลองก่อน (0) สามารถเปลี่ยนเป็น 1/2 ได้ภายหลัง
        self.face_worker = FaceScanWorker(self.ser, cam_index=0)
        self.face_worker.frame_signal.connect(self.show_frame)
        self.face_worker.info_signal.connect(lambda m: self.set_status(m, ok=True))
        self.face_worker.finished.connect(lambda: self._face_finished())
        self.face_worker.start()
        self.btn_face.setText("Face Scan (Stop)")
        self.set_status("Face Scan started.")

    def stop_face(self):
        if self.face_worker:
            self.face_worker.stop()
            self.face_worker = None
            self.btn_face.setText("Face Scan (Start)")
            self.set_status("Face Scan stopped.")

    def _face_finished(self):
        self.face_worker = None
        self.btn_face.setText("Face Scan (Start)")

    def start_hand(self):
        self.hand_worker = HandAxisWorker(self.ser, cam_index=0)
        self.hand_worker.frame_signal.connect(self.show_frame)
        self.hand_worker.info_signal.connect(lambda m: self.set_status(m, ok=True))
        self.hand_worker.finished.connect(lambda: self._hand_finished())
        self.hand_worker.start()
        self.btn_hand.setText("Hand Axis (Stop)")
        self.set_status("Hand Axis started.")

    def stop_hand(self):
        if self.hand_worker:
            self.hand_worker.stop()
            self.hand_worker = None
            self.btn_hand.setText("Hand Axis (Start)")
            self.set_status("Hand Axis stopped.")

    def _hand_finished(self):
        self.hand_worker = None
        self.btn_hand.setText("Hand Axis (Start)")

    def closeEvent(self, event):
        try:
            if self.face_worker: self.face_worker.stop()
            if self.hand_worker: self.hand_worker.stop()
            self.ser.close()
        finally:
            super().closeEvent(event)


# ========================= Entry =========================
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
