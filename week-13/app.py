import sys
from PyQt5 import QtWidgets, uic, QtGui, QtCore


from serial_manager import SerialManager


class MainWindow(QtWidgets.QMainWindow):
    def _init(self):
        super()._init_()
        uic.loadUi("main_window.ui", self)
        
        
        
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())