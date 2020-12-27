from gui_item import MyItem
from util import getColor

from PyQt5.QtWidgets import (
    QHBoxLayout,
    QVBoxLayout,
    QGridLayout,
    QGroupBox,
    QDialog,
    QScrollArea,
    QLabel,
    QComboBox,
    QMessageBox,
    QPushButton,
    QLineEdit,
    QApplication,
    QWidget,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIntValidator, QColor, QPalette

prm_chn = ['直线', '多边形', '椭圆', '曲线']
prm_eng = ['line', 'polygon', 'ellipse', 'curve']
prm_eng2chn = dict(zip(prm_eng, prm_chn))
prm_chn2eng = dict(zip(prm_chn, prm_eng))


class PrimitiveDialog(QDialog):
    def __init__(self, primitive: MyItem, current_name=[], parent=None) -> None:
        super().__init__(parent)

        self.original = primitive.copy()
        self.current_name = current_name
        self.p_cnt = len(primitive.p_list)
        self.p_min = 2
        self.color = QColor(0, 0, 0)
        self.NoActivateChange = False
        self.__initUI()
        self.__initPrimitive(primitive)

    def getItem(self):
        if self.exec():
            name = self.name_edit.text()
            p_type = prm_chn2eng[self.pcombo.currentText()]
            algo = self.acombo.currentText()
            algo = '' if algo == '无' else algo
            ret = MyItem(name, p_type, self._currentPoint(), self.color, algo)
            return ret if ret != self.original else None
        else:
            return None

    def _addPoint(self, force=False):
        if self.p_cnt < self.p_max or force:
            self.p_cnt += 1
            self.p_grid.addWidget(self._newlabel(self.p_cnt), self.p_cnt, 0)
            self.p_grid.addWidget(self._newLineEdit(), self.p_cnt, 1)
            self.p_grid.addWidget(self._newLineEdit(), self.p_cnt, 2)
            self._ensureValidPoint()
        else:
            QMessageBox.warning(self, '错误', '无法增加控制点',
                                QMessageBox.Ok, QMessageBox.Ok)

    def _removePoint(self, force=False):
        if self.p_cnt > self.p_min or force:
            items = [self.p_grid.itemAtPosition(
                self.p_cnt, i) for i in range(3)]
            self.p_cnt -= 1
            for item in items:
                self.p_grid.removeItem(item)
                item.widget().setParent(None)
            self._ensureValidPoint()
        else:
            QMessageBox.warning(self, '错误', '无法减少控制点',
                                QMessageBox.Ok, QMessageBox.Ok)

    def _currentPoint(self, allow_empty=False):
        ret = []
        for i in range(1, 1 + self.p_cnt):
            x = self.p_grid.itemAtPosition(i, 1).widget().text()
            y = self.p_grid.itemAtPosition(i, 2).widget().text()
            if not x or not y:
                if allow_empty:
                    ret.append([x, y])
                else:
                    raise ValueError(f'Empty Value at Line{i}')
            else:
                ret.append([int(x), int(y)])
        return ret

    def _isCutDownValid(self, downto):
        assert(downto > 0)
        pts = self._currentPoint(allow_empty=True)
        for x, y in pts[downto:]:
            if x or y:
                return False
        return True

    def _confirmCutDown(self, downto):
        ret = QMessageBox.warning(self, '警告', f'目标图元类型控制点({downto})小于当前图元({self.p_cnt})，部分坐标将被删去\n是否确认？',
                                  QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if ret == QMessageBox.No:
            return False
        return True

    def _newLineEdit(self):
        line = QLineEdit()
        line.setValidator(QIntValidator(0, 5000))
        line.setFixedSize(60, 22)
        line.textEdited.connect(self._ensureValidPoint)
        return line

    def _newlabel(self, text, size=(15, 22), align=Qt.AlignLeft):
        lb = QLabel(str(text))
        lb.setFixedSize(*size)
        lb.setAlignment(align)
        return lb

    def _resetPointList(self, p_min, p_max):
        if not self._isCutDownValid(p_max) and not self._confirmCutDown(p_max):
            self.pcombo.setCurrentText(self.primitive)
            return False
        while self.p_cnt > p_max:
            self._removePoint(force=True)
        while self.p_cnt < p_min:
            self._addPoint(force=True)
        self.p_min = p_min
        self.p_max = p_max
        return True

    def _algoChanged(self, algo):
        if self.NoActivateChange == False:
            algo = self.acombo.currentText()
            if self.pcombo.currentText() == '曲线':
                if algo == 'B-spline':
                    p_min, p_max = 4, 10
                else:
                    p_min, p_max = 2, 10
                self._resetPointList(p_min, p_max)

    def _primitiveChanged(self, primitive=None):
        cur_prm = self.pcombo.currentText() if not primitive else primitive
        cur_algo = self.pcombo.currentText()
        algo = {'直线': ['Naive', 'DDA', 'Bresenham'],
                '多边形': ['DDA', 'Bresenham'],
                '椭圆': ['无'],
                '曲线': ['Bezier', 'B-spline']}
        p_limit = {'直线': [2, 2],
                   '多边形': [2, 9999999],
                   '椭圆': [2, 2],
                   '曲线': [2, 9999999]}
        p_min, p_max = p_limit[cur_prm]
        if not self._resetPointList(p_min, p_max):
            return
        self.primitive = cur_prm
        self.NoActivateChange = True
        while self.acombo.count() > 0:
            self.acombo.removeItem(0)
        self.acombo.addItems(algo[cur_prm])
        self.NoActivateChange = False
        new_id = self.parent().get_id(
            (prm_chn2eng[self.primitive], self.original_id))
        self.name_edit.setText(new_id)

    def _setLabelColor(self, color: QColor):
        self.color = color
        palette = QPalette()
        palette.setColor(QPalette.Button, color)
        self.color_edit.setAutoFillBackground(True)
        self.color_edit.setPalette(palette)

    def _editColor(self):
        color = getColor(self, initial=self.color, title='图元颜色')
        if color.isValid():
            self._setLabelColor(color)

    def _ensureUniqueName(self, name):
        if not name or name in self.current_name:
            self.btnOk.setEnabled(False)
            self.name_label.setStyleSheet("color:red")
            self.name_edit.setStyleSheet("background-color:white;color:red")
        else:
            self.btnOk.setEnabled(True)
            self.name_label.setStyleSheet("color:black")
            self.name_edit.setStyleSheet("background-color:white;color:black")

    def _ensureValidPoint(self, text=None):
        valid = True
        for i in range(1, 1 + self.p_cnt):
            x = self.p_grid.itemAtPosition(i, 1).widget().text()
            y = self.p_grid.itemAtPosition(i, 2).widget().text()
            if not x or not y:
                valid = False
                self.p_grid.itemAtPosition(
                    i, 0).widget().setStyleSheet("color:red")
            else:
                self.p_grid.itemAtPosition(
                    i, 0).widget().setStyleSheet("color:black")
        self.btnOk.setEnabled(valid)

    def __initPrimitive(self, prm):
        if prm.id in self.current_name:
            self.current_name.remove(prm.id)
        self.original_id = prm.id
        self.primitive = prm.item_type
        self._primitiveChanged(prm_eng2chn[prm.item_type])
        self.pcombo.setCurrentText(prm_eng2chn[prm.item_type])
        self.acombo.setCurrentText(prm.algorithm if prm.algorithm else '无')
        for i, point in enumerate(prm.p_list.real):
            x, y = point
            self.p_grid.itemAtPosition(i+1, 1).widget().setText(str(x))
            self.p_grid.itemAtPosition(i+1, 2).widget().setText(str(y))
        self._setLabelColor(prm.color)
        self.name_edit.setText(prm.id)

    def __initUI(self):
        self.setModal(Qt.ApplicationModal)
        self.setWindowFlags(Qt.WindowCloseButtonHint |
                            Qt.Dialog | Qt.MSWindowsFixedSizeDialogHint)
        self.resize(300, 400)

        content = QWidget()
        self.scrollArea = QScrollArea()
        self.scrollArea.setWidget(content)
        p_grid = QGridLayout()
        p_grid.addWidget(self._newlabel('x', (60, 22), Qt.AlignCenter), 0, 1)
        p_grid.addWidget(self._newlabel('y', (60, 22), Qt.AlignCenter), 0, 2)
        for i in range(1, 1 + self.p_cnt):
            p_grid.addWidget(self._newlabel(i), i, 0)
            p_grid.addWidget(self._newLineEdit(), i, 1)
            p_grid.addWidget(self._newLineEdit(), i, 2)
        self.p_grid = p_grid
        self.scrollArea.widget().setLayout(p_grid)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.name_edit = QLineEdit()
        self.color_edit = QPushButton()
        self.color_edit.setFlat(True)
        self.color_edit.setStyleSheet("border:1px solid black;")
        self.color_edit.setFixedSize(50, 50)
        self.color_edit.setAutoFillBackground(True)
        pcombo = QComboBox()
        acombo = QComboBox()
        pcombo.setFixedWidth(100)
        acombo.setFixedWidth(100)
        pcombo.addItems(prm_chn)
        self.pcombo = pcombo
        self.acombo = acombo

        self.name_label = QLabel('名称(ID):')
        addPBtn = QPushButton('+')
        rmPBtn = QPushButton('-')
        self.addPointBtn = addPBtn
        self.rmPointBtn = rmPBtn
        btnOk = QPushButton('确定')
        btnCancel = QPushButton('取消')
        self.btnOk = btnOk
        gb = QGroupBox('控制点管理')

        hl1 = QHBoxLayout()
        hl2 = QHBoxLayout()
        hl3 = QHBoxLayout()
        hl4 = QHBoxLayout()
        vl = QVBoxLayout()
        vlgb = QVBoxLayout()

        hl1.addWidget(self.name_label)
        hl1.addWidget(self.name_edit)
        hl1.addWidget(self.color_edit)
        hl2.addWidget(QLabel('类型:'))
        hl2.addWidget(pcombo)
        hl2.addWidget(acombo)
        hl3.addWidget(addPBtn)
        hl3.addWidget(rmPBtn)
        hl4.addWidget(btnOk)
        hl4.addWidget(btnCancel)
        vlgb.addLayout(hl3)
        vlgb.addWidget(self.scrollArea)
        gb.setLayout(vlgb)
        vl.setSpacing(20)
        vl.addLayout(hl1)
        vl.addLayout(hl2)
        vl.addWidget(gb)
        vl.addLayout(hl4)
        self.setLayout(vl)
        self.setWindowTitle('图元属性')
        self.show()

        self.name_edit.textEdited.connect(self._ensureUniqueName)
        self.color_edit.clicked.connect(self._editColor)
        addPBtn.clicked.connect(self._addPoint)
        rmPBtn.clicked.connect(self._removePoint)
        btnOk.clicked.connect(self.accept)
        btnCancel.clicked.connect(self.reject)
        pcombo.currentTextChanged.connect(self._primitiveChanged)
        acombo.currentTextChanged.connect(self._algoChanged)
