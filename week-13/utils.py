import cv2
from PyQt5.QtGui import QImage

def cvimg_to_qimage(frame_bgr):
    frame_bgr = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    h, w, ch = frame_bgr.shape
    bytes_per_line = ch * w
    return QtGui.QImage(frame_bgr.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)