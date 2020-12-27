import cg_algorithms as alg
from cg_algorithms_ext import Direc
from my_plist import PList
from copy import deepcopy
from typing import Optional
from PyQt5.QtWidgets import QGraphicsItem, QWidget, QStyleOptionGraphicsItem
from PyQt5.QtGui import QPainter, QColor, QPen
from PyQt5.QtCore import QRectF, Qt, QMarginsF

type_map = {'line': 0, 'polygon': 1, 'ellipse': 2, 'curve': 3}
type_map_rev = {v: k for k, v in type_map.items()}
alg_map = {'DDA': 0, 'Bresenham': 1, 'Bezier': 2, 'B-spline': 3, '': 4}
alg_map_rev = {v: k for k, v in alg_map.items()}


class MyItem(QGraphicsItem):
    """
    自定义图元类，继承自QGraphicsItem
    """

    def __init__(self, item_id: str, item_type: str, p_list: list, color: QColor, algorithm: str = '', parent: QGraphicsItem = None):
        """

        :param item_id: 图元ID
        :param item_type: 图元类型，'line'、'polygon'、'ellipse'、'curve'等
        :param p_list: 图元参数
        :param algorithm: 绘制算法，'DDA'、'Bresenham'、'Bezier'、'B-spline'等
        :param parent:
        """
        super().__init__(parent)
        self.id = item_id           # 图元ID
        self.item_type = item_type  # 图元类型，'line'、'polygon'、'ellipse'、'curve'等
        self.p_list = PList(p_list)  # 图元参数
        self.algorithm = algorithm  # 绘制算法，'DDA'、'Bresenham'、'Bezier'、'B-spline'等
        self.color = color          # 画笔颜色
        self.selected = False

        self.in_progress = True     # 绘制中
        self.display_control_point = (self.item_type == 'curve')
        self.curve_border = []      # 曲线外框辅助

        self.dirty = True
        self.on_paint_clean = False
        self.pixels = []

    def copy(self):
        ret = MyItem(self.id, self.item_type, deepcopy(
            self.p_list), self.color, self.algorithm)
        ret.in_progress = False
        ret.display_control_point = self.display_control_point
        ret.curve_border = deepcopy(self.curve_border)
        return ret

    def update_pixel(self):
        func_map = {'line':    [alg.draw_line]*2,
                    'polygon': [alg.draw_polygon, alg.draw_fold_line],
                    'ellipse': [alg.draw_ellipse]*2,
                    'curve':   [alg.draw_curve]*2}
        func_id = 1 if self.in_progress else 0
        self.pixels = func_map[self.item_type][func_id](
            self.p_list.real, self.algorithm)
        if self.item_type == 'curve':
            # xy[0] contains all x's, xy[1] contains all y's
            xy = list(zip(*self.pixels))
            if not xy:
                self.curve_border = [0] * 4
            else:
                x, y = min(xy[0]), min(xy[1])
                w, h = max(xy[0]) - x, max(xy[1]) - y
                self.curve_border = [x, y, w, h]

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = ...) -> None:
        if self.dirty:
            self.update_pixel()
            if self.on_paint_clean:
                self.dirty = False
                self.on_paint_clean = False
        for p in self.pixels:
            painter.setPen(self.color)
            painter.drawPoint(*p)
        # the following will draw the center of primitive
        # painter.setPen(QPen(self.color, 4))
        # painter.drawPoint(*self.rectCenter())
        if (self.in_progress or self.selected) and self.display_control_point:
            for p in self.p_list.real:
                painter.setPen(QPen(QColor(255, 0, 0), 3))
                painter.drawPoint(*p)
        if self.selected:
            painter.setPen(QPen(QColor(255, 0, 0), 1, Qt.DashLine))
            painter.drawRect(self.boundingRect())

    def toggleControlPoint(self):
        self.display_control_point = not self.display_control_point

    def boundingRect(self, border=True) -> QRectF:
        if self.item_type == 'curve' and len(self.curve_border) == 4:
            x, y, w, h = self.curve_border
        else:
            xy = list(zip(*(self.p_list.real)))
            x = min(xy[0])
            y = min(xy[1])
            w = max(xy[0]) - x
            h = max(xy[1]) - y
        return QRectF(x - 1, y - 1, w + 2, h + 2) if border else QRectF(x, y, w, h)

    def wideRect(self, width=10) -> QRectF:
        rect = self.boundingRect(border=False)
        return rect.marginsAdded(QMarginsF(*[width]*4))

    def rectCenter(self) -> tuple:
        mpt = self.boundingRect(border=False).center()
        return round(mpt.x()), round(mpt.y())

    def boundingBorder(self) -> tuple:
        rect = self.boundingRect(border=False)
        pt0 = rect.bottomLeft()
        pt1 = rect.topRight()
        xs = [round(t) for t in (pt0.x(), pt1.x())]
        ys = [round(t) for t in (pt0.y(), pt1.y())]
        return sorted(xs), sorted(ys)

    def boundingPoint(self, pos) -> tuple:
        xs, ys = self.boundingBorder()
        x0, x1 = xs
        y0, y1 = ys
        x_mid = (x0 + x1) // 2
        y_mid = (y0 + y1) // 2
        candidate = {Direc.LEFT: (x0, y_mid), Direc.RIGHT: (x1, y_mid),
                     Direc.TOP: (x_mid, y0), Direc.BOTTOM: (x_mid, y1),
                     Direc.LEFT_TOP: (x0, y0), Direc.LEFT_BOTTOM: (x0, y1),
                     Direc.RIGHT_TOP: (x1, y0), Direc.RIGHT_BOTTOM: (x1, y1)}
        return candidate[pos]

    def __eq__(self, o: object) -> bool:
        assert(isinstance(o, MyItem))
        return self.id == o.id \
            and self.item_type == o.item_type \
            and self.algorithm == o.algorithm \
            and self.color.name() == o.color.name() \
            and self.p_list.real == o.p_list.real

    def noticeClean(self):
        self.on_paint_clean = True

    def noticeUpdate(self):
        self.on_paint_clean = True
        self.dirty = True

    def to_bytes(self):
        tval = type_map[self.item_type]
        aval = alg_map[self.algorithm] if self.algorithm in alg_map else 4
        cval = self.color.rgb()
        tbyte = int.to_bytes(tval, 1, 'big', signed=False)
        abyte = int.to_bytes(aval, 1, 'big', signed=False)
        cbyte = int.to_bytes(cval, 4, 'big', signed=False)
        idbyte = str.encode(self.id, encoding='utf8') + b'\x00'
        return tbyte + abyte + cbyte + plist_to_bytes(self.p_list.real) + idbyte

    @staticmethod
    def from_bytes(data: bytes):
        assert(len(data) > 6)
        tbyte = data[0:1]
        abyte = data[1:2]
        cbyte = data[2:6]
        rest = data[6:]
        tval = int.from_bytes(tbyte, 'big', signed=False)
        aval = int.from_bytes(abyte, 'big', signed=False)
        cval = int.from_bytes(cbyte, 'big', signed=False)
        plen, plist = plist_from_bytes(rest)
        idbyte = rest[plen*8+4:]
        end = idbyte.find(b'\x00')
        _id = str(idbyte[:end], encoding='utf8')
        r = (cval & 0xFF0000) >> 16
        g = (cval & 0xFF00) >> 8
        b = cval & 0xFF
        item = MyItem(_id, type_map_rev[tval], plist, QColor(
            r, g, b), alg_map_rev[aval])
        item.in_progress = False
        return item


def plist_to_bytes(p_list) -> bytes:
    length = len(p_list)
    data = int.to_bytes(length, 4, 'big', signed=False)
    for x, y in p_list:
        data += int.to_bytes(x, 4, 'big', signed=True)
        data += int.to_bytes(y, 4, 'big', signed=True)
    return data


def plist_from_bytes(data):
    length = int.from_bytes(data[0:4], 'big', signed=False)
    ret = []
    idx = 0
    while idx < length:
        start = idx * 8 + 4
        if start + 8 >= len(data):
            raise RuntimeError
        x = int.from_bytes(data[start:start+4], 'big', signed=True)
        y = int.from_bytes(data[start+4:start+8], 'big', signed=True)
        ret.append([x, y])
        idx += 1
    return length, ret


def decode_cgp(data):
    cgp = data[0:4]
    w = int.from_bytes(data[5:8], 'big', signed=False)
    h = int.from_bytes(data[8:12], 'big', signed=False)
    cnt = int.from_bytes(data[12:16], 'big', signed=False)
    start = 16
    ret = []
    if cgp != b'CGPJ':
        raise RuntimeError
    for i in range(cnt):
        item = MyItem.from_bytes(data[start:])
        ret.append(item)
        start += len(item.to_bytes())
    return w, h, ret


def encode_cgp(w, h, items):
    head = b'CGPJ' + \
        int.to_bytes(w, 4, 'big', signed=False) + \
        int.to_bytes(h, 4, 'big', signed=False) + \
        int.to_bytes(len(items), 4, 'big', signed=False)
    body = b''
    for item in items:
        body += item.to_bytes()
    return head + body


if __name__ == "__main__":
    item1 = MyItem('item1', 'polygon', [[-10, 10], [15, 15], [25, 15], [100, 200], [300, 900]],
                   QColor(255, 0, 128), 'Bresenham')
    item2 = MyItem('item2', 'ellipse', [[100, 200], [400, 6000]],
                   QColor(0, 255, 128), '')
    bs = item1.to_bytes()
    print(len(bs), bs)
    item = MyItem.from_bytes(bs)
    print(item.id, item.item_type, item.algorithm,
          item.color.name(), item.p_list)
    fb = encode_cgp(600, 500, [item1, item2])
    print(fb)
    w, h, lis = decode_cgp(fb)
    print(lis[0] == item1)
    print(lis[1] == item2)
