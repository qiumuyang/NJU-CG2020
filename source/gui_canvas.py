import cg_algorithms as alg
from cg_algorithms_ext import p_normalize, to_border, Direc, calculate_angle, p_box_dist
from gui_item import MyItem
from gui_primitive import PrimitiveDialog
from my_plist import PList
from op_stack import OpStack, Action
from util import isLinux

import os
from copy import deepcopy
from enum import Enum
from PyQt5.QtWidgets import QGraphicsView, QListWidgetItem, QMessageBox
from PyQt5.QtGui import QPen, QMouseEvent, QKeyEvent, QColor, QCursor, QPixmap
from PyQt5.QtCore import QPoint, QRectF, Qt, pyqtSignal


def get_path(name):
    return os.path.join(os.path.dirname(__file__), 'resource', name)


class Status(Enum):
    EMPTY = 0
    DRAW = 1
    TRANSFORM = 2


class MyCanvas(QGraphicsView):
    """
    画布窗体类，继承自QGraphicsView，采用QGraphicsView、QGraphicsScene、QGraphicsItem的绘图框架
    """

    itemSelectionChanged = pyqtSignal(str)
    clipBoardChanged = pyqtSignal()
    actionChanged = pyqtSignal()

    def __init__(self, *args):
        super().__init__(*args)
        self.main_window = None
        self.list_widget = None
        self.item_dict = {}

        self.status = ''
        # for DRAW
        self.temp_algorithm = ''
        self.temp_id = ''
        self.temp_item = None
        self.color = QColor(0, 0, 0)

        # for TRANSFORM
        self.last_scale = None
        self.temp_pos = None
        self.temp_point = None
        self.temp_direc = None
        self.temp_rect = None

        # for undo/redo/copy/paste
        self.stack = OpStack(self)
        self.clip_board = None

        self.RotateCursor = QCursor(QPixmap(get_path('r_cursor.png')), -1, -1)
        self.CrossCursor = QCursor(QPixmap(get_path('d_cursor.png')), -1, -1)
        target = 15
        self.SizeHorCursor = QCursor(QPixmap(get_path('sizeh.png')).scaledToWidth(
            target*2**0.5, Qt.SmoothTransformation), -1, -1)
        self.SizeVerCursor = QCursor(QPixmap(get_path('sizev.png')).scaledToHeight(
            target*2**0.5, Qt.SmoothTransformation), -1, -1)
        self.SizeFDiagCursor = QCursor(QPixmap(get_path('sizefd.png')).scaled(
            target, target, transformMode=Qt.SmoothTransformation), -1, -1)
        self.SizeBDiagCursor = QCursor(QPixmap(get_path('sizebd.png')).scaled(
            target, target, transformMode=Qt.SmoothTransformation), -1, -1)
        self.setMouseTracking(True)

    def row_of_item(self, item_id):
        for row in range(self.list_widget.count()):
            if self.list_widget.item(row).text() == item_id:
                return row
        return None

    @property
    def selected_list_row(self):
        return self.row_of_item(self.selected_id)

    @property
    def selected_id(self) -> str:
        selecteds = self.list_widget.selectedItems()
        return selecteds[0].text() if selecteds else ''

    @property
    def selected_item(self):
        return self.item_dict[self.selected_id] if self.selected_id else None

    def is_current_primivite(self, p_type):
        if self.selected_id:
            return self.selected_item.item_type == p_type
        return False

    def set_color(self, r, g, b):
        self.color = QColor(r, g, b)
        if self.temp_item:
            self.temp_item.color = self.color
            self.updateScene([self.sceneRect()])

    # Atomic
    def set_item_color(self, r, g, b):
        color = QColor(r, g, b)
        if self.selected_id:
            self.stack.do(Action(
                Action.COLOR, item_id=self.selected_id, color=(QColor(self.selected_item.color), QColor(color))))
            self.selected_item.color = color
            self.selected_item.noticeUpdate()
            self.updateScene([self.sceneRect()])

    def start_draw(self):
        type, algorithm = self.main_window.get_draw_args()
        item_id = self.main_window.get_id()
        self.status = type
        self.temp_algorithm = algorithm
        self.temp_id = item_id

    def start_transform(self):
        self.status, self.temp_algorithm = self.main_window.get_trans_args()

    def finish_draw(self, clicked=False):
        if self.temp_item:
            if clicked:
                # DoubleClick Trigger mouseReleaseEvent as well,
                # the first click will add a point to primitive,
                # so remove the point added by that Event
                if self.status == 'polygon':
                    self.temp_item.p_list.pop()
                    if len(self.temp_item.p_list) > 2:
                        self.temp_item.p_list.pop()
                elif self.status == 'curve':
                    if self.temp_algorithm == 'Bezier' and len(self.temp_item.p_list) > 2:
                        # the last control point shouldn't be poped
                        self.temp_item.p_list.pop(-2)
                    elif self.temp_algorithm == 'B-spline':
                        self.temp_item.p_list.pop(-1)
                    if self.temp_algorithm == 'B-spline' and len(self.temp_item.p_list) < 4:
                        self.scene().removeItem(self.temp_item)
                        self.temp_item = None
                        QMessageBox.warning(self, '错误', '三次B-spline曲线需要至少4个控制点',
                                            QMessageBox.Ok, QMessageBox.Ok)
                        return

            self.temp_item.in_progress = False
            self.add_item(self.temp_item)
            self.temp_item = None

    def finish_transform(self):
        self.last_scale = [self.temp_pos, self.temp_point]
        self.temp_pos = None
        self.temp_direc = None
        self.temp_point = None
        if self.temp_rect:
            self.scene().removeItem(self.temp_rect)
        self.temp_rect = None

    # Atomic
    def clear(self, do_record=True):
        if not self.item_dict:
            return
        if do_record:
            self.stack.do(Action(
                Action.ITEMS, items=[item.copy() for item in self.item_dict.values()]))
        self.item_dict = {}
        self.scene().clear()
        self.list_widget.clear()

    # Atomic
    def add_item(self, item, add_to_scene=False, do_record=True):
        assert(item.id)
        assert(item.id not in self.item_dict)
        if add_to_scene:
            self.scene().addItem(item)
        item.noticeClean()
        self.updateScene([self.sceneRect()])
        self.item_dict[item.id] = item
        self.list_widget.addItem(item.id)
        if do_record:
            self.stack.do(Action(
                Action.ITEM, item=(None, item.copy())))

    # Atomic
    def remove_item(self, item_id, do_record=True):
        assert(item_id in self.item_dict)
        rm_item = self.item_dict.pop(item_id)
        self.scene().removeItem(rm_item)
        self.updateScene([self.sceneRect()])
        self.list_widget.takeItem(self.row_of_item(item_id)).setSelected(False)
        if do_record:
            self.stack.do(Action(
                Action.ITEM, item=(rm_item.copy(), None)))

    def remove_selected_item(self):
        if self.selected_item:
            self.main_window.statusBar().showMessage('')
            self.remove_item(self.selected_id)

    # Atomic
    def item_property_dialog(self, listItem: QListWidgetItem, do_record=True):
        item_id = listItem.text()
        ret = PrimitiveDialog(self.item_dict[item_id], current_name=[
                              key for key in self.item_dict], parent=self.main_window).getItem()
        if ret:
            self.last_scale = None

            new_item = ret
            new_item.selected = self.item_dict[item_id].selected
            new_item.in_progress = self.item_dict[item_id].in_progress

            rm_item = self.item_dict.pop(item_id)
            self.scene().removeItem(rm_item)
            self.item_dict[new_item.id] = new_item
            self.list_widget.item(self.row_of_item(item_id)
                                  ).setText(new_item.id)
            self.scene().addItem(new_item)
            new_item.noticeUpdate()
            self.updateScene([self.sceneRect()])
            self.clear_selection()
            if do_record:
                self.stack.do(Action(
                    Action.ITEM, item=(rm_item.copy(), new_item.copy())))

    def undo_action(self):
        if self.stack.undoValid():
            action = self.stack.undo()
            if action.type == Action.ITEM:
                before = action.item[0].copy() if action.item[0] else None
                after = action.item[1].copy() if action.item[1] else None
                if after:
                    self.remove_item(after.id, do_record=False)
                if before:
                    self.add_item(before, add_to_scene=True, do_record=False)
            elif action.type == Action.TRANSFORM:
                _id = action.item_id
                before = deepcopy(action.p_list[0])
                self.item_dict[_id].p_list = before
                self.item_dict[_id].noticeUpdate()
            elif action.type == Action.COLOR:
                _id = action.item_id
                before = QColor(action.color[0])
                self.item_dict[_id].color = before
                self.item_dict[_id].noticeUpdate()
            elif action.type == Action.ITEMS:
                for item in action.items:
                    self.add_item(item.copy(), add_to_scene=True,
                                  do_record=False)
            self.updateScene([self.sceneRect()])

    def redo_action(self):
        if self.stack.redoValid():
            action = self.stack.redo()
            if action.type == Action.ITEM:
                before = action.item[0].copy() if action.item[0] else None
                after = action.item[1].copy() if action.item[1] else None
                if before:
                    self.remove_item(before.id, do_record=False)
                if after:
                    self.add_item(after, add_to_scene=True, do_record=False)
            elif action.type == Action.TRANSFORM:
                _id = action.item_id
                after = deepcopy(action.p_list[1])
                self.item_dict[_id].p_list = after
                self.item_dict[_id].noticeUpdate()
            elif action.type == Action.COLOR:
                _id = action.item_id
                after = QColor(action.color[1])
                self.item_dict[_id].color = after
                self.item_dict[_id].noticeUpdate()
            elif action.type == Action.ITEMS:
                self.clear(do_record=False)
            self.updateScene([self.sceneRect()])

    def copy_action(self):
        if self.selected_id:
            copy_item = self.selected_item.copy()
            copy_item.selected = False
            self.clip_board = copy_item
            self.clipBoardChanged.emit()

    def cut_action(self):
        if self.selected_id:
            self.copy_action()
            self.remove_selected_item()

    def paste_action(self):
        if self.clip_board:
            new_item = self.clip_board.copy()
            new_item.id = self.main_window.get_id((new_item.item_type, None))
            self.add_item(new_item, add_to_scene=True)
            self.set_selection(new_item.id)

    def set_selection(self, item_id):
        if item_id in self.item_dict:
            self.item_dict[item_id].selected = True
            self.list_widget.item(self.row_of_item(item_id)).setSelected(True)
            self.updateScene([self.sceneRect()])

    def clear_selection(self):
        if self.selected_id:
            self.main_window.statusBar().showMessage('')
            self.selected_item.selected = False
            self.list_widget.item(self.selected_list_row).setSelected(False)
            self.updateScene([self.sceneRect()])

    def selection_changed(self):
        if self.selected_id:
            self.main_window.statusBar().showMessage('图元选择： %s' % self.selected_id)
            for item in self.item_dict.values():
                item.selected = False
            self.selected_item.selected = True
            self.updateScene([self.sceneRect()])
            self.itemSelectionChanged.emit(self.selected_item.item_type)
        else:
            self.itemSelectionChanged.emit('')

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if (event.button() != Qt.LeftButton):
            return
        pos = self.mapToScene(event.localPos().toPoint())
        x = int(pos.x())
        y = int(pos.y())
        self.main_window.statusBar().showMessage(f'{x}, {y}像素')
        status = self.main_window.get_status()
        if status == Status.DRAW:  # draw
            if not self.temp_item:
                self.start_draw()
                self.clear_selection()
                if self.status:
                    self.temp_item = MyItem(self.temp_id, self.status, [
                                            [x, y], [x, y]], self.color, self.temp_algorithm)
                    self.scene().addItem(self.temp_item)
            elif self.status == 'curve':
                # Add new Control Point for curve
                if self.temp_algorithm == 'Bezier':
                    self.temp_item.p_list.insert(-1, [x, y])
                elif self.temp_algorithm == 'B-spline':
                    self.temp_item.p_list.append([x, y])
            self.updateScene([self.sceneRect()])
        elif status == Status.TRANSFORM:  # transform
            if self.selected_id:
                self.start_transform()
                if self.status == 'translate':
                    if self.selected_item.boundingRect(border=False).contains(QPoint(x, y)):
                        self.temp_pos = (x, y)
                elif self.status == 'scale':
                    direct = to_border(
                        self.selected_item.boundingBorder(), [x, y])
                    if direct != Direc.EMPTY:
                        self.temp_pos = self.selected_item.boundingPoint(
                            direct.direc)
                        self.temp_direc = direct
                        self.temp_point = self.selected_item.boundingPoint(
                            (~direct).direc)
                    if self.last_scale and self.last_scale[1] == self.temp_point:
                        self.temp_pos = self.last_scale[0]
                elif self.status == 'rotate':
                    if not self.selected_item.boundingRect(border=False).contains(QPoint(x, y)):
                        self.temp_pos = (x, y)
                        self.temp_point = self.selected_item.rectCenter()
                elif self.status == 'clip':
                    self.temp_pos = (x, y)
                    self.temp_rect = self.scene().addRect(
                        QRectF(x, y, 0, 0), QPen(QColor(0, 0, 0), 1, Qt.DashLine))
        elif status == Status.EMPTY:  # choose primitive
            items = [item for item in self.item_dict.values()
                     if item.wideRect().contains(QPoint(x, y))]
            if items:
                item = min(items, key=lambda i: p_box_dist(
                    (x, y), i.wideRect()))
                self.clear_selection()
                self.set_selection(item.id)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if (event.button() != Qt.LeftButton):
            return
        pos = self.mapToScene(event.localPos().toPoint())
        x = int(pos.x())
        y = int(pos.y())
        self.main_window.statusBar().showMessage(f'{x}, {y}像素')
        if self.status in ['polygon', 'curve']:
            self.finish_draw(clicked=True)
        self.updateScene([self.sceneRect()])
        super().mouseDoubleClickEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        is_norm = (event.modifiers() == Qt.ShiftModifier)
        pos = self.mapToScene(event.localPos().toPoint())
        x = int(pos.x())
        y = int(pos.y())
        self.main_window.statusBar().showMessage(f'{x}, {y}像素')
        point = [x, y]
        if event.buttons() == Qt.LeftButton:
            if self.temp_item:
                if self.status in ['line', 'ellipse']:
                    self.temp_item.p_list[1] = p_normalize(
                        is_norm, self.status, self.temp_item.p_list[0], point)
                elif self.status == 'polygon':
                    self.temp_item.p_list[-1] = point
                elif self.status == 'curve' and self.temp_algorithm == 'Bezier':
                    self.temp_item.p_list[-1 if len(self.temp_item.p_list)
                                          == 2 else -2] = point
                elif self.status == 'curve' and self.temp_algorithm == 'B-spline':
                    self.temp_item.p_list[-1] = point
            elif self.temp_pos:
                if self.status == 'translate':
                    x0, y0 = self.temp_pos
                    self.transform('translate', dx=x-x0, dy=y-y0)
                    self.temp_pos = (x, y)
                elif self.status == 'scale':
                    x0, y0 = self.temp_pos
                    xp, yp = self.temp_point
                    sx, sy = 1, 1
                    if self.temp_direc.isHorizontal:
                        sx = (x - xp) / (x0 - xp) if x0 != xp else 0.01
                    if self.temp_direc.isVertical:
                        sy = (y - yp) / (y0 - yp) if y0 != yp else 0.01
                    self.transform(
                        'scale', center=self.temp_point, sx=sx, sy=sy, set=True)
                elif self.status == 'rotate':
                    ret = calculate_angle(
                        self.temp_pos, point, self.temp_point)
                    self.transform('rotate', center=self.temp_point, r=ret)
                    self.temp_pos = (x, y)
                elif self.status == 'clip':
                    x0, y0 = self.temp_pos
                    x0, x1 = (x0, x) if x0 < x else (x, x0)
                    y0, y1 = (y0, y) if y0 < y else (y, y0)
                    self.temp_rect.setRect(x0, y0, x1 - x0, y1 - y0)
        self.handleCursor(QPoint(x, y))
        self.updateScene([self.sceneRect()])
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if (event.button() != Qt.LeftButton):
            return
        pos = self.mapToScene(event.localPos().toPoint())
        x = int(pos.x())
        y = int(pos.y())
        if self.temp_item:
            if self.status in ['line', 'ellipse']:
                self.finish_draw()
            elif self.status == 'polygon' and self.temp_item:
                self.temp_item.p_list[-1] = [x, y]
                self.temp_item.p_list.append([x, y])
            elif self.status == 'curve' and self.temp_item:
                if self.temp_algorithm == 'Bezier':
                    self.temp_item.p_list[-1 if len(self.temp_item.p_list)
                                          == 2 else -2] = [x, y]
                elif self.temp_algorithm == 'B-spline':
                    self.temp_item.p_list[-1] = [x, y]
        elif self.temp_pos:
            if self.status == 'clip':
                rect = self.temp_rect.rect()
                box = [rect.left(), rect.top(), rect.right(), rect.bottom()]
                box = [round(i) for i in box]
                self.transform('clip', box=box, algorithm=self.temp_algorithm)
            self.finish_transform()
        self.updateScene([self.sceneRect()])
        super().mouseReleaseEvent(event)

    # Atomic
    def transform(self, t_type, **kwargs):
        if self.selected_id:
            p_type = self.selected_item.item_type
            p_list = self.selected_item.p_list
            center = self.selected_item.rectCenter(
            ) if 'center' not in kwargs else kwargs['center']
            isset = kwargs['set'] if 'set' in kwargs else False
            ret = []
            if t_type == 'translate':
                ret = alg.translate(
                    p_list.real, kwargs['dx'], kwargs['dy'])
            elif t_type == 'rotate':
                ret = deepcopy(p_list)
                ret.rotate(center, kwargs['r']) if p_type != 'ellipse' else ret
            elif t_type == 'scale':
                ret = deepcopy(p_list)
                if isset:
                    ret.scale_set(center, kwargs['sx'], kwargs['sy'])
                else:
                    ret.scale(center, kwargs['sx'], kwargs['sy'])
            elif t_type == 'clip':
                ret = alg.clip(
                    p_list.real, *kwargs['box'], kwargs['algorithm'])
                if not ret:
                    ret = QMessageBox.warning(self, '警告', '未裁剪有效部分，将移除该线段。\n是否裁剪？',
                                              QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Cancel)
                    if ret == QMessageBox.Ok:
                        self.remove_selected_item()
                        self.updateScene([self.sceneRect()])
                    return
            self.stack.do(Action(
                Action.TRANSFORM, item_id=self.selected_id, p_list=[deepcopy(p_list), deepcopy(ret)], t_type=t_type))
            self.selected_item.p_list = PList(ret)
            self.selected_item.noticeUpdate()
            self.updateScene([self.sceneRect()])

    def keyPressEvent(self, event: QKeyEvent) -> None:
        key = event.key()
        if key == Qt.Key_Left:
            self.transform('translate', dx=-1, dy=0)
        elif key == Qt.Key_Right:
            self.transform('translate', dx=1, dy=0)
        elif key == Qt.Key_Up:
            self.transform('translate', dx=0, dy=-1)
        elif key == Qt.Key_Down:
            self.transform('translate', dx=0, dy=1)
        elif key in [Qt.Key_Less, Qt.Key_Comma]:
            self.transform('rotate', r=359.5)
        elif key in [Qt.Key_Greater, Qt.Key_Period]:
            self.transform('rotate', r=0.5)
        elif key in [Qt.Key_Plus, Qt.Key_Equal]:
            self.transform('scale', sx=1.05, sy=1.05)
        elif key in [Qt.Key_Minus, Qt.Key_Underscore]:
            self.transform('scale', sx=0.95238, sy=0.95238)
        elif key == Qt.Key_Backtab:
            if self.selected_item:
                self.selected_item.toggleControlPoint()
                self.updateScene([self.sceneRect()])
            elif self.temp_item:
                self.temp_item.toggleControlPoint()
                self.updateScene([self.sceneRect()])
        elif key == Qt.Key_Tab:
            if self.selected_item:
                next_id = (self.selected_list_row + 1) % len(self.item_dict)
                self.clear_selection()
                self.set_selection(self.list_widget.item(next_id).text())
        elif key == Qt.Key_Space:
            self.finish_draw()
            self.finish_transform()
            self.clear_selection()
            self.main_window.clear_action_selection()
        super().keyPressEvent(event)

    def handleCursor(self, point: QPoint):
        cursor = Qt.ArrowCursor
        if self.sceneRect().contains(point):
            if self.status in ['line', 'polygon', 'ellipse', 'curve']:
                cursor = self.CrossCursor
            elif self.selected_id and self.status:
                if self.status == 'translate' and \
                        self.selected_item.boundingRect(border=False).contains(point):
                    cursor = Qt.SizeAllCursor
                elif self.status == 'rotate':
                    # not started yet
                    if not self.temp_pos and not self.selected_item.boundingRect(border=False).contains(point):
                        cursor = self.RotateCursor
                    if self.temp_pos:
                        cursor = self.RotateCursor
                elif self.status == 'scale':
                    direct = to_border(
                        self.selected_item.boundingBorder(), [point.x(), point.y()])
                    if direct in [Direc.RIGHT_BOTTOM, Direc.LEFT_TOP]:
                        cursor = (self if isLinux else Qt).SizeFDiagCursor
                    elif direct in [Direc.LEFT_BOTTOM, Direc.RIGHT_TOP]:
                        cursor = (self if isLinux else Qt).SizeBDiagCursor
                    elif direct in [Direc.LEFT, Direc.RIGHT]:
                        cursor = (self if isLinux else Qt).SizeHorCursor
                    elif direct in [Direc.TOP, Direc.BOTTOM]:
                        cursor = (self if isLinux else Qt).SizeVerCursor
                elif self.status == 'clip':
                    cursor = self.CrossCursor
            elif not self.status:
                for item in self.item_dict.values():
                    if item.wideRect().contains(point):
                        cursor = Qt.PointingHandCursor
                        break
        self.setCursor(cursor)
