import sys
import serial
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QFrame
)
from PyQt5.QtGui import QFont, QColor, QPalette
from PyQt5.QtCore import Qt, QTimer


ser = serial.Serial('COM4', 9600, timeout=1)


class SensorDisplay(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Temperature & Humidity Monitor")
        self.setFixedSize(600, 600)
        self.setStyleSheet("background-color: #f0f4f8;")

        # Layout หลัก
        layout = QVBoxLayout()
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setSpacing(30)

        # หัวข้อ
        self.title = QLabel("Sensor Data Monitor")
        self.title.setFont(QFont("Arial", 24, QFont.Bold))
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("color: #333;")

        # กรอบแสดงข้อมูล
        self.data_frame = QFrame()
        self.data_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 20px;
                padding: 30px;
                border: 2px solid #ccc;
            }
        """)
        frame_layout = QVBoxLayout()

        # ข้อมูลอุณหภูมิ
        self.temp_label = QLabel("Temperature: -- °C")
        self.temp_label.setFont(QFont("Arial", 20))
        self.temp_label.setAlignment(Qt.AlignCenter)

        # ข้อมูลความชื้น
        self.hum_label = QLabel("Humidity: -- %")
        self.hum_label.setFont(QFont("Arial", 20))
        self.hum_label.setAlignment(Qt.AlignCenter)

        frame_layout.addWidget(self.temp_label)
        frame_layout.addWidget(self.hum_label)
        self.data_frame.setLayout(frame_layout)

        layout.addWidget(self.title)
        layout.addWidget(self.data_frame)
        self.setLayout(layout)

        # Timer อ่านข้อมูลทุก 2 วินาที
        self.timer = QTimer()
        self.timer.timeout.connect(self.read_serial)
        self.timer.start(2000)

    def read_serial(self):
        try:
            if ser.in_waiting:
                line = ser.readline().decode().strip()
                if "Temp:" in line and "Hum:" in line:
                    temp = line.split("Temp:")[1].split(";")[0]
                    hum = line.split("Hum:")[1]
                    self.temp_label.setText(f"Temperature: {temp} °C")
                    self.hum_label.setText(f"Humidity: {hum} %")
        except Exception as e:
            self.temp_label.setText("Error reading data")
            self.hum_label.setText(str(e))


# เริ่มต้นโปรแกรม
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SensorDisplay()
    window.show()
    sys.exit(app.exec_())
