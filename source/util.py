from PyQt5.QtWidgets import QColorDialog, QFileDialog, QDialog
from PyQt5.QtGui import QColor
import platform
import sys
import re

isLinux = platform.system() == 'Linux'
epsilon = sys.float_info.epsilon


def get_ext(filt):
    match = re.search(r'\((.+)\)', filt)
    return match.group(1)[1:]


def getColor(context, initial, title):
    if not isLinux:
        return QColorDialog.getColor(initial=initial, title=title)
    dlg = QColorDialog(initial, context)
    dlg.setWindowTitle(title)
    dlg.setOption(QColorDialog.DontUseNativeDialog)
    color = QColor()
    if dlg.exec() == QDialog.Accepted:
        color = dlg.currentColor()
    return color


def getFileName(mode, context, caption, directory, tfilter):
    if not isLinux:
        if mode == 'save':
            file_path, file_type = QFileDialog.getSaveFileName(
                context, caption, directory, tfilter)
            return file_path
        elif mode == 'open':
            file_path, file_type = QFileDialog.getOpenFileName(
                context, caption, directory, tfilter)
            return file_path
        else:
            raise ValueError
    dlg = QFileDialog(context, caption, directory, tfilter)
    if mode == 'save':
        mode = QFileDialog.AcceptSave
    elif mode == 'open':
        mode = QFileDialog.AcceptOpen
    else:
        raise ValueError
    dlg.setAcceptMode(mode)
    dlg.setViewMode(QFileDialog.List)
    dlg.setOption(QFileDialog.DontUseNativeDialog)
    if dlg.exec() == QDialog.Accepted:
        filt = dlg.selectedNameFilter()
        ext = get_ext(filt)
        ret = dlg.selectedFiles()[0]
        if not ret.endswith(ext):
            ret += ext
        return ret
    return ''
