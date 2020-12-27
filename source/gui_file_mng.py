from PyQt5.QtWidgets import QMessageBox
from gui_item import encode_cgp, decode_cgp
from util import getFileName
import os


class FileMng:
    Accept = 1
    Reject = 2
    Fail = -1
    Cancel = 0
    CGP = 10
    BMP = 11

    def __init__(self, parent):
        self.parent = parent
        self.exist = False
        self.file_path = '未命名.cgp'

    @property
    def dir(self):
        try:
            if self.file_path:
                return os.path.dirname(os.path.abspath(self.file_path))
            return os.getcwd()
        except:
            return os.getcwd()

    @property
    def fileName(self, ext=False):
        abspath = os.path.abspath(self.file_path)
        folder, file = os.path.split(abspath)
        fname, fext = os.path.splitext(file)
        return file if ext else fname

    def new(self):
        if self.parent.need_save():
            ret = self.save(msg=f'是否保存更改到 {self.fileName} ？')
            if ret == self.Cancel or ret == self.Fail:
                return self.Cancel
        self.parent.resize_canvas(600, 600)
        self.parent.reload_items([])
        self.file_path = '未命名.cgp'
        self.exist = False

    def open(self):
        if self.parent.need_save():
            ret = self.save(msg=f'是否保存更改到 {self.fileName} ？')
            if ret == self.Cancel or ret == self.Fail:
                return self.Cancel
        file_path = getFileName(
            'open', self.parent, '打开', self.dir, 'CG Project文件 (*.cgp)')
        if file_path:
            with open(file_path, 'rb') as f:
                data = f.read()
            try:
                w, h, item_list = decode_cgp(data)
            except:
                return self.Fail
            self.parent.resize_canvas(w, h)
            self.parent.reload_items(item_list)

            self.file_path = file_path
            self.exist = True
            return self.Accept
        return self.Cancel

    def save(self, msg=''):
        file_path = self.file_path
        if msg:
            ret = QMessageBox.question(
                self.parent, self.parent.TITLE, msg, QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            if ret == QMessageBox.Discard:
                return self.Reject
            if ret == QMessageBox.Cancel:
                return self.Cancel
        if not self.exist:
            file_path = getFileName(
                'save', self.parent, '保存', self.file_path, 'CG Project文件 (*.cgp)')
        if file_path:
            data = encode_cgp(*self.parent.property())
            try:
                with open(file_path, 'wb') as f:
                    f.write(data)
            except:
                return self.Fail

            self.file_path = file_path
            self.exist = True
            return self.Accept
        return self.Cancel

    def save_as(self):
        file_path = getFileName(
            'save', self.parent, '另存为', self.file_path, 'CG Project文件 (*.cgp);;位图 (*.bmp)')
        if not file_path:
            return self.Cancel, None

        folder, file = os.path.split(file_path)
        fname, fext = os.path.splitext(file)
        if fext == '.bmp':
            self.parent.to_image().save(file_path)
            return self.Accept, self.BMP
        elif fext == '.cgp':
            data = encode_cgp(*self.parent.property())
            try:
                with open(file_path, 'wb') as f:
                    f.write(data)
            except:
                return self.Fail, None

            self.file_path = file_path
            self.exist = True
            return self.Accept, self.CGP
        return self.Cancel, None
