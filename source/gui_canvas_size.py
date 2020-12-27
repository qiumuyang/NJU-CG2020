import sys
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QVBoxLayout,
    QGroupBox,
    QDialog,
    QLabel,
    QRadioButton,
    QCheckBox,
    QPushButton,
    QSpinBox,
    QApplication,
)
from PyQt5.QtCore import Qt

W_MAX = 1000
W_MIN = 100
H_MAX = 1000
H_MIN = 100


class CanvasSizeDialog(QDialog):
    def __init__(self, width, height) -> None:
        super().__init__()

        self.size = (width, height)
        self.__initUI()

    def __reset_spinbox(self):
        if self.opt1.isChecked():
            w0 = round(W_MIN / self.size[0] * 100)
            w1 = round(W_MAX / self.size[0] * 100)
            h0 = round(H_MIN / self.size[1] * 100)
            h1 = round(H_MAX / self.size[1] * 100)
            self.sb1.setRange(w0, w1)
            self.sb2.setRange(h0, h1)
            self.sb1.setValue(100)
            self.sb2.setValue(100)
        else:
            self.sb1.setRange(W_MIN, W_MAX)
            self.sb2.setRange(H_MIN, H_MAX)
            self.sb1.setValue(self.size[0])
            self.sb2.setValue(self.size[1])

    def __keep_aspect_ratio(self):
        if self.cb.isChecked():
            ratio = self.size[1] / self.size[0]
            if self.sender() == self.sb1:
                self.sb2.setValue(round(self.sb1.value() * ratio))
            else:
                self.sb1.setValue(round(self.sb2.value() / ratio))

    def getSize(self):
        if self.exec():
            return self.opt1.isChecked(), self.sb1.value(), self.sb2.value()
        else:
            return None

    def __initUI(self):
        self.setModal(Qt.ApplicationModal)
        self.setWindowFlags(Qt.WindowCloseButtonHint |
                            Qt.Dialog | Qt.MSWindowsFixedSizeDialogHint)

        hl1 = QHBoxLayout()
        hl2 = QHBoxLayout()
        hl3 = QHBoxLayout()
        hl4 = QHBoxLayout()
        vlgb = QVBoxLayout()
        vl = QVBoxLayout()

        self.opt1 = QRadioButton('百分比', self)
        self.opt2 = QRadioButton('像素', self)
        self.opt1.setChecked(True)
        cmd1 = QPushButton('确定')
        cmd2 = QPushButton('取消')

        lb1 = QLabel('依据:', self)
        lb2 = QLabel('水平:', self)
        lb3 = QLabel('垂直:', self)
        self.sb1 = QSpinBox(self)
        self.sb1.setMaximumWidth(100)
        self.sb2 = QSpinBox(self)
        self.sb2.setMaximumWidth(100)
        self.__reset_spinbox()
        self.cb = QCheckBox('保持纵横比(&M)', self)
        self.cb.setChecked(True)

        hl1.addWidget(lb1)
        hl1.addWidget(self.opt1)
        hl1.addWidget(self.opt2)

        hl2.addStretch(1)
        hl2.addWidget(lb2, 2)
        hl2.addWidget(self.sb1, 2)

        hl3.addStretch(1)
        hl3.addWidget(lb3, 2)
        hl3.addWidget(self.sb2, 2)

        hl4.addStretch(1)
        hl4.addWidget(cmd1)
        hl4.addWidget(cmd2)

        gb = QGroupBox('画布大小')
        vlgb.addLayout(hl1)
        vlgb.addLayout(hl2)
        vlgb.addLayout(hl3)
        gb.setLayout(vlgb)
        vl.addWidget(gb, 4)
        vl.addWidget(self.cb, 1)
        vl.addStretch(1)
        vl.addLayout(hl4, 1)

        self.setLayout(vl)
        self.resize(280, 340)
        self.setWindowTitle('调整画布大小')
        self.show()

        cmd1.clicked.connect(self.accept)
        cmd2.clicked.connect(self.reject)
        self.opt1.clicked.connect(self.__reset_spinbox)
        self.opt2.clicked.connect(self.__reset_spinbox)
        self.cb.clicked.connect(self.__keep_aspect_ratio)
        self.sb1.valueChanged.connect(self.__keep_aspect_ratio)
        self.sb2.valueChanged.connect(self.__keep_aspect_ratio)
