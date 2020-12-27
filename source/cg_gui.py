#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys

from gui_menu import parse_menu, STRUCTURE
from gui_canvas import MyCanvas, Status, get_path
from gui_canvas_size import CanvasSizeDialog
from gui_file_mng import FileMng
from util import getColor

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    qApp,
    QGraphicsScene,
    QListWidget,
    QHBoxLayout,
    QWidget,
    QMessageBox,
    QPushButton,
    QToolButton,
    QMenu,
)
from PyQt5.QtGui import QPainter, QPalette, QColor, QImage, QIcon
from PyQt5.QtCore import QEvent, QSize, Qt


class MainWindow(QMainWindow):
    """
    主窗口类
    """
    TITLE = 'CG Project'

    def __init__(self):
        super().__init__()
        self.chosen_draw_act = None
        self.chosen_trans_act = None

        # 使用QListWidget来记录已有的图元，并用于选择图元。注：这是图元选择的简单实现方法，更好的实现是在画布中直接用鼠标选择图元
        self.list_widget = QListWidget(self)
        self.list_widget.setMinimumWidth(200)

        # 使用QGraphicsView作为画布
        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(0, 0, 600, 600)
        self.canvas_widget = MyCanvas(self.scene, self)
        # scrollbar will appear if set exactly to 600
        self.canvas_widget.setFixedSize(603, 603)
        self.canvas_widget.main_window = self
        self.canvas_widget.list_widget = self.list_widget
        self.list_widget.setFocusProxy(self.canvas_widget)
        self.filemng = FileMng(self)

        # 设置菜单栏
        menubar = self.menuBar()
        parse_menu(STRUCTURE, menubar, vars(self))

        self.init_toolbar()
        self.init_dict()
        self.init_icon()
        self.init_action()

        # 初始化编辑菜单栏
        self.update_edit_validity()
        self.init_action_validity()

        # 连接信号和槽函数
        self.exit_act.triggered.connect(self.closeEvent)
        self.new_act.triggered.connect(self.new_action)
        self.open_act.triggered.connect(self.open_action)
        self.save_act.triggered.connect(self.save_action)
        self.save_as_act.triggered.connect(self.save_as_action)
        self.resize_canvas_act.triggered.connect(self.resize_canvas_action)
        self.clear_canvas_act.triggered.connect(self.clear_canvas)
        self.set_pen_act.triggered.connect(self.set_pen_color)
        self.set_color_act.triggered.connect(self.set_item_color)
        self.clear_select_act.triggered.connect(
            self.canvas_widget.clear_selection)
        self.undo_act.triggered.connect(self.canvas_widget.undo_action)
        self.redo_act.triggered.connect(self.canvas_widget.redo_action)
        self.copy_act.triggered.connect(self.canvas_widget.copy_action)
        self.cut_act.triggered.connect(self.canvas_widget.cut_action)
        self.paste_act.triggered.connect(self.canvas_widget.paste_action)
        self.remove_item_act.triggered.connect(
            self.canvas_widget.remove_selected_item)
        self.canvas_widget.actionChanged.connect(self.update_undoredo)
        self.canvas_widget.itemSelectionChanged.connect(
            self.update_edit_validity)
        self.canvas_widget.itemSelectionChanged.connect(
            self.update_color)
        self.canvas_widget.clipBoardChanged.connect(
            lambda: self.paste_act.setEnabled(not not self.canvas_widget.clip_board))
        self.list_widget.itemSelectionChanged.connect(
            self.canvas_widget.selection_changed)
        self.list_widget.itemDoubleClicked.connect(
            self.canvas_widget.item_property_dialog)

        # 设置主窗口的布局
        self.hbox_layout = QHBoxLayout()
        self.hbox_layout.addWidget(self.canvas_widget)
        self.hbox_layout.addWidget(self.list_widget, stretch=1)
        self.central_widget = QWidget()
        self.central_widget.setLayout(self.hbox_layout)
        self.setCentralWidget(self.central_widget)
        self.statusBar().showMessage('空闲')
        self.resize(600, 600)
        self.update_window_title()

    def init_action(self):
        # 设置相关QAction
        for action in self.draw_act + self.trans_act:
            action.setCheckable(True)
            action.toggled.connect(self.action_toggled)

    def init_toolbar(self):
        toolbar = self.addToolBar('')
        toolbar.setAllowedAreas(Qt.TopToolBarArea)
        toolbar.setFloatable(False)
        toolbar.setMovable(False)
        toolbar.setContextMenuPolicy(Qt.PreventContextMenu)
        self.toolButton = []
        for item in [self.line_menu, self.polygon_menu, self.ellipse_act, self.curve_menu,
                     self.translate_act, self.rotate_act, self.scale_act, self.clip_menu]:
            button = QToolButton()
            button.setCheckable(True)
            button.toggled.connect(self.action_toggled)
            button.setFocusPolicy(Qt.NoFocus)
            if isinstance(item, QMenu):
                button.setMenu(item)
                button.setPopupMode(QToolButton.MenuButtonPopup)
            if item == self.translate_act:
                toolbar.addSeparator()
            toolbar.addWidget(button)
            self.toolButton.append(button)
        color = QPushButton()
        color.setFocusPolicy(Qt.NoFocus)
        color.setFixedSize(toolbar.iconSize())
        color.setFlat(True)
        # fix initial with empty color
        # FIXED: fix by setting background color at the beginning,
        #        and resetting background afterwards
        color.setStyleSheet("border:1px solid black; background-color: black")
        color.setAutoFillBackground(True)
        color.clicked.connect(
            lambda: self.set_pen_color() if not self.canvas_widget.selected_id else self.set_item_color())
        self.toolColor = color
        toolbar.addSeparator()
        toolbar.addWidget(color)

    def init_icon(self):
        icons = [QIcon(get_path(f'{name}.png')) for name in
                 ['line', 'polygon', 'ellipse', 'curve',
                  'translate', 'rotate', 'scale', 'clip']]
        targets = [self.line_menu, self.polygon_menu, self.ellipse_act, self.curve_menu,
                   self.translate_act, self.rotate_act, self.scale_act, self.clip_menu]
        for i in range(len(icons)):
            targets[i].setIcon(icons[i])
            self.toolButton[i].setIcon(icons[i])

    def init_action_validity(self):
        self.paste_act.setEnabled(not not self.canvas_widget.clip_board)
        self.undo_act.setEnabled(self.canvas_widget.stack.undoValid())
        self.redo_act.setEnabled(self.canvas_widget.stack.redoValid())

    def init_dict(self):
        self.draw_act = [self.line_naive_act, self.line_dda_act, self.line_bresenham_act,
                         self.polygon_dda_act, self.polygon_bresenham_act,
                         self.ellipse_act, self.curve_bezier_act, self.curve_b_spline_act]
        self.trans_act = [self.translate_act, self.rotate_act, self.scale_act,
                          self.clip_cohen_sutherland_act, self.clip_liang_barsky_act]
        self.toolbar_map = dict(zip(self.toolButton,
                                    [self.line_dda_act, self.polygon_dda_act, self.ellipse_act, self.curve_bezier_act,
                                     self.translate_act, self.rotate_act, self.scale_act, self.clip_liang_barsky_act]))
        t_toolbar = [self.toolButton[0], self.toolButton[0], self.toolButton[0],
                     self.toolButton[1], self.toolButton[1],
                     self.toolButton[2], self.toolButton[3], self.toolButton[3],
                     self.toolButton[4], self.toolButton[5], self.toolButton[6],
                     self.toolButton[7], self.toolButton[7]]
        self.menu_map = dict(zip(self.draw_act+self.trans_act, t_toolbar))
        self.status_alg = dict(zip(self.draw_act,
                                   [('line', 'Naive'), ('line', 'DDA'), ('line', 'Bresenham'),
                                    ('polygon', 'DDA'), ('polygon', 'Bresenham'),
                                    ('ellipse', ''), ('curve', 'Bezier'), ('curve', 'B-spline')]))
        self.status_alg.update(dict(zip(self.trans_act,
                                        [('translate', ''), ('rotate', ''), ('scale', ''),
                                         ('clip', 'Cohen-Sutherland'), ('clip', 'Liang-Barsky')])))
        self.status_tip = dict(zip(self.draw_act + self.trans_act,
                                   ['Naive算法绘制线段', 'DDA算法绘制线段', 'Bresenham算法绘制线段',
                                    'DDA算法绘制多边形', 'Bresenham算法绘制多边形',
                                    '绘制椭圆', '绘制Bézier曲线', '绘制B-spline曲线',
                                    '平移变换', '旋转变换', '缩放变换',
                                    'Cohen-Sutherland算法裁剪线段', 'Liang-Barsky算法裁剪线段']))

    def get_id(self, restrict=None):
        ''' 
        :param restrict: (String|Primitive, String|old_id) set which kind of primitive_id should return
        '''
        current_list = [self.list_widget.item(
            i).text() for i in range(self.list_widget.count())]
        primitives = self.get_draw_args()[0] if not restrict else restrict[0]
        i = 1
        _id = f'{primitives}{i}'
        while _id in current_list:
            if restrict and _id == restrict[1]:
                break
            i += 1
            _id = f'{primitives}{i}'
        return _id

    def property(self):
        return round(self.scene.width()), round(self.scene.height()), list(self.canvas_widget.item_dict.values())

    def need_save(self):
        return self.canvas_widget.stack.needSave()

    def new_action(self):
        self.filemng.new()
        self.clear_action_selection()
        self.update_window_title()

    def open_action(self):
        ret = self.filemng.open()
        if ret == FileMng.Fail:
            QMessageBox.warning(self, '错误', '该文件不是合法的cgp文件', QMessageBox.Ok)
        self.clear_action_selection()
        self.update_window_title()

    def save_action(self):
        ret = self.filemng.save()
        if ret == FileMng.Fail:
            QMessageBox.warning(self, '错误', '保存失败', QMessageBox.Ok)
        if ret == FileMng.Accept:
            self.canvas_widget.stack.setCheckpoint()
            self.update_undoredo()

    def save_as_action(self):
        ret, ftype = self.filemng.save_as()
        if ret == FileMng.Fail:
            QMessageBox.warning(self, '错误', '保存失败', QMessageBox.Ok)
        if ret == FileMng.Accept and ftype == FileMng.CGP:
            self.canvas_widget.stack.setCheckpoint()
        self.update_undoredo()

    def to_image(self) -> QImage:
        self.canvas_widget.clear_selection()
        graphicsScene = self.scene
        graphicsScene.setBackgroundBrush(QColor(255, 255, 255))
        img = QImage(QSize(self.scene.width(),
                           self.scene.height()), QImage.Format_RGB32)
        painter = QPainter(img)
        graphicsScene.render(painter)
        painter.end()
        return img

    def resize_canvas_action(self):
        ret = CanvasSizeDialog(
            self.scene.width(), self.scene.height()).getSize()
        if ret:
            isPercent = ret[0]
            if not isPercent:
                w, h = ret[1], ret[2]
            else:
                w = round(self.scene.width() * ret[1] / 100)
                h = round(self.scene.height() * ret[2] / 100)
            self.resize_canvas(w, h)

    def resize_canvas(self, w, h):
        max_w = 1500
        max_h = 900
        canvas_w = min(max_w, w)
        canvas_h = min(max_h, h)
        self.canvas_widget.setFixedSize(canvas_w + 3, canvas_h + 3)
        self.scene.setSceneRect(0, 0, w, h)

    def reload_items(self, items):
        self.canvas_widget.stack.clear()
        self.canvas_widget.clear(do_record=False)
        self.update_undoredo()
        for item in items:
            self.canvas_widget.add_item(
                item, add_to_scene=True, do_record=False)

    def clear_canvas(self):
        ret = QMessageBox.warning(self, '警告', '确定要清空画布吗',
                                  QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Cancel)
        if ret == QMessageBox.Ok:
            self.canvas_widget.clear()

    def closeEvent(self, event):
        if self.need_save():
            isEvent = isinstance(event, QEvent)
            ret = self.filemng.save('想要保存画布吗？')
            if ret == FileMng.Cancel and isEvent:
                event.ignore()
            elif ret == FileMng.Reject or ret == FileMng.Accept:
                event.accept() if isEvent else qApp.quit()
        else:
            qApp.quit()

    def set_pen_color(self):
        color = getColor(
            self, initial=self.canvas_widget.color, title='画笔颜色')
        if color.isValid():
            self.canvas_widget.set_color(
                color.red(), color.green(), color.blue())
            self.update_color()

    def set_item_color(self):
        color = getColor(
            self, initial=self.canvas_widget.selected_item.color, title='图元颜色')
        if color.isValid():
            self.canvas_widget.set_item_color(
                color.red(), color.green(), color.blue())
            self.update_color()

    def update_color(self):
        if self.canvas_widget.selected_id:
            color = self.canvas_widget.selected_item.color
        else:
            color = self.canvas_widget.color
        self.toolColor.setStyleSheet("border:1px solid black;")
        palette = QPalette()
        palette.setColor(QPalette.Button, color)
        self.toolColor.setAutoFillBackground(True)
        self.toolColor.setPalette(palette)

    def update_edit_validity(self, p_type=''):
        enabled = not not self.list_widget.selectedItems()
        edit = ['clear_select_act', 'remove_item_act', 'set_color_act', 'translate_act',
                'rotate_act', 'scale_act', 'clip_menu', "copy_act", "cut_act"]
        ebutton = self.toolButton[4:]
        self.clear_select_act.setVisible(enabled)
        for x in edit:
            vars(self)[x].setEnabled(enabled)
        for b in ebutton:
            b.setEnabled(enabled)
        if not p_type:
            for widget in self.trans_act + ebutton:
                self._safe_setChecked(widget, False)
                if self.chosen_draw_act == widget:
                    self.chosen_draw_act = None
                if self.chosen_trans_act == widget:
                    self.chosen_trans_act = None
        if p_type == 'ellipse':
            self.toolButton[-3].setEnabled(False)  # rotate
            self._safe_setChecked(self.toolButton[-3], False)
            self.rotate_act.setEnabled(False)
            self._safe_setChecked(self.rotate_act, False)
        if p_type != 'line':
            self.toolButton[-1].setEnabled(False)  # clip
            self._safe_setChecked(self.toolButton[-1], False)
            self.clip_menu.setEnabled(False)
            self._safe_setChecked(self.clip_cohen_sutherland_act, False)
            self._safe_setChecked(self.clip_liang_barsky_act, False)
        self.canvas_widget.start_draw()

    def update_window_title(self):
        name = self.filemng.fileName
        saveflag = '*' if self.need_save() else ''
        self.setWindowTitle(name + saveflag + ' - ' + self.TITLE)

    def update_undoredo(self):
        self.undo_act.setEnabled(self.canvas_widget.stack.undoValid())
        self.redo_act.setEnabled(self.canvas_widget.stack.redoValid())
        self.update_window_title()

    def get_status(self):
        if self.chosen_draw_act:
            return Status.DRAW
        if self.chosen_trans_act:
            return Status.TRANSFORM
        return Status.EMPTY

    def get_draw_args(self):
        return self.status_alg[self.chosen_draw_act] if self.chosen_draw_act else ('', '')

    def get_trans_args(self):
        return self.status_alg[self.chosen_trans_act] if self.chosen_trans_act else ('', '')

    def _safe_setChecked(self, object, value):
        object.toggled.disconnect()
        object.setChecked(value)
        object.toggled.connect(self.action_toggled)

    def clear_action_selection(self):
        for action in self.draw_act + self.trans_act:
            self._safe_setChecked(action, False)
        for button in self.toolButton:
            self._safe_setChecked(button, False)
        self.chosen_draw_act = None
        self.chosen_trans_act = None
        self.canvas_widget.start_draw()
        self.statusBar().showMessage('空闲')

    def action_toggled(self):
        self.canvas_widget.finish_draw()
        toggled = self.sender().isChecked()
        isToolbar = self.sender() in self.toolButton
        menuSender = self.sender(
        ) if not isToolbar else self.toolbar_map[self.sender()]
        toolSender = self.sender(
        ) if isToolbar else self.menu_map[self.sender()]
        isDraw = menuSender in self.draw_act
        self._safe_setChecked(menuSender, toggled)
        self._safe_setChecked(toolSender, toggled)
        # setChecked will emit signal [toggled],
        # thus calling action_toggled again
        if toggled:
            # Menu
            for action in self.draw_act + self.trans_act:
                if action != menuSender:
                    self._safe_setChecked(action, False)
            # Toolbar
            for button in self.toolButton:
                if button != toolSender:
                    self._safe_setChecked(button, False)

            self.chosen_draw_act = menuSender if isDraw else None
            self.chosen_trans_act = menuSender if not isDraw else None
            self.statusBar().showMessage(self.status_tip[menuSender])
        else:
            if isDraw:
                self.chosen_draw_act = None
            else:
                self.chosen_trans_act = None
            self.statusBar().showMessage('空闲')
        if isDraw:
            self.canvas_widget.start_draw()
        else:
            self.canvas_widget.start_transform()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec_())
