import sys, os, sqlite3, datetime
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import Qt

DB_PATH = os.path.join(os.path.dirname(__file__), "congrate.db")

class Main(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("congrate.ui", self)

        # เมื่อกด Enter หรือกดปุ่มจะทำงานทันที
        self.lineEdit.returnPressed.connect(self.scan_rfid)
        self.pushButton.clicked.connect(self.scan_rfid)

        # ตั้งค่า Table
        self.tableWidget.setColumnCount(4)
        self.tableWidget.setHorizontalHeaderLabels(["รหัส","คำนำหน้า","ชื่อ","นามสกุล"])
        self.tableWidget.horizontalHeader().setStretchLastSection(True)

    def scan_rfid(self):
        rfid_code = self.lineEdit.text().strip()
        if not rfid_code:
            return

        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        cur.execute("""
            SELECT student_id, prefix, fname, lname 
            FROM student
            WHERE rfid=? OR student_id=?
        """, (rfid_code, rfid_code))
        result = cur.fetchone()

        if not result:
            QtWidgets.QMessageBox.warning(self, "ไม่พบข้อมูล", f"ไม่พบรหัส: {rfid_code}")
            con.close()
            self.lineEdit.clear()   # เคลียร์ช่องทันทีเพื่อรอรับค่าใหม่
            return

        # แสดงข้อมูลในตาราง UI
        self.tableWidget.setRowCount(1)
        for c, val in enumerate(result):
            self.tableWidget.setItem(0, c, QtWidgets.QTableWidgetItem(str(val)))

        # บันทึกการสแกนลง check_in
        student_id = result[0]
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur.execute("SELECT COALESCE(MAX(id),0)+1 FROM check_in")
        next_id = cur.fetchone()[0]
        cur.execute("INSERT INTO check_in(id, student_id, time_in) VALUES (?,?,?)",
                    (next_id, student_id, now))
        con.commit()
        con.close()

        # เคลียร์รหัสทันทีเพื่อรอรับค่าใหม่
        self.lineEdit.clear()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    win = Main()
    win.setWindowTitle("RFID Check-In")
    win.show()
    sys.exit(app.exec_())
