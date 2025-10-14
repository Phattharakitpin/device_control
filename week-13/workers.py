# -*- coding: utf-8 -*-
import time, math, traceback
import cv2
import mediapipe as mp
from PyQt5 import QtCore

from utils import cvimg_to_qimage

class FaceScanWorker(QtCore.QThread):
    frame_signal = QtCore.pyqtSignal(object)  # QImage
    info_signal  = QtCore.pyqtSignal(str)

    def __init__(self, ser, parent=None):
        super().__init__(parent)
        self.ser = ser
        self._running = False
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

    def run(self):
        self._running = True
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
            self.info_signal.emit("Camera not available.")
            return

        sent = False
        self.info_signal.emit("Face Scan running…")

        try:
            while self._running:
                ok, frame = cap.read()
                if not ok:
                    break
                frame = cv2.flip(frame, 1)

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, 1.2, 5, minSize=(80, 80))

                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

                if len(faces) > 0 and not sent:
                    self.ser.send_angle(90)
                    self.info_signal.emit("Face detected → COM3: rotate 90°")
                    sent = True

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


class HandAxisWorker(QtCore.QThread):
    frame_signal = QtCore.pyqtSignal(object)  # QImage
    info_signal  = QtCore.pyqtSignal(str)

    def __init__(self, ser, parent=None):
        super().__init__(parent)
        self.ser = ser
        self._running = False
        self.mp_hands = mp.solutions.hands
        self.mp_draw  = mp.solutions.drawing_utils

        # stream smoothing / throttling
        self._last_sent_angle = None
        self._last_sent_time = 0.0
        self._min_delta = 2
        self._min_interval = 0.06  # ~15 Hz

    @staticmethod
    def _calc_angle(p0, p1, p2):
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
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
            self.info_signal.emit("Camera not available.")
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
                        break
                    frame = cv2.flip(frame, 1)
                    h, w, _ = frame.shape

                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    res = hands.process(rgb)

                    display_angle = 0
                    if res.multi_hand_landmarks:
                        for hand in res.multi_hand_landmarks:
                            self.mp_draw.draw_landmarks(frame, hand, self.mp_hands.HAND_CONNECTIONS)

                            wrist = hand.landmark[0]
                            thumb_tip = hand.landmark[4]
                            index_tip = hand.landmark[8]

                            p0 = (int(wrist.x*w), int(wrist.y*h))
                            p1 = (int(thumb_tip.x*w), int(thumb_tip.y*h))
                            p2 = (int(index_tip.x*w), int(index_tip.y*h))

                            angle = self._calc_angle(p0, p1, p2)
                            angle = max(0.0, min(90.0, angle))
                            display_angle = angle

                            cv2.circle(frame, p1, 8, (255, 0, 0), -1)
                            cv2.circle(frame, p2, 8, (0, 0, 255), -1)

                            self._maybe_send(angle)
                            break

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