import re


def parse_menu(structure, menubar, var):
    """

    :param structure: (string) a multi-line string which defines the Menu structure
    :param menubar: (QMenubar) QMainWindow.menuBar
    :param var: (dict) vars()/locals() of caller
    :return:
    """
    def get_indent(line):
        for i, ch in enumerate(line):
            if ch != ' ':
                return i

    def is_menu(i, lines):
        if i == len(lines) - 1:
            return False
        if get_indent(lines[i]) < get_indent(lines[i+1]):
            return True
        return False

    def find_parent(indent, tree):
        tree = [(menu, ind) for menu, ind in tree if ind < indent]
        return tree[-1][0]

    lines = [line for line in structure.split('\n') if line.strip()]
    tree = [(menubar, -1)]
    for i, line in enumerate(lines):
        if line.strip()[0] == '#':
            continue
        tokens = re.split(' +', line.strip(), 3)
        token_cnt = len(tokens)
        current_indent = get_indent(line)
        parent = find_parent(current_indent, tree)
        if tokens[0].startswith('-----'):
            parent.addSeparator()
            continue
        isMenu = is_menu(i, lines)
        varname = tokens[0] + '_menu' if isMenu else tokens[0] + '_act'
        text = tokens[1]
        shortcut = tokens[2] if token_cnt >= 3 and tokens[2] != 'None' else None
        statusTip = tokens[3] if token_cnt >= 4 and tokens[3] != 'None' else None
        tmp = parent.addMenu(text) if isMenu else parent.addAction(text)
        if shortcut:
            tmp.setShortcut(shortcut)
        if statusTip:
            tmp.setStatusTip(statusTip)
        var[varname] = tmp
        tree.append((tmp, current_indent))


STRUCTURE = '''
file 文件(&F)
    new           新建           Ctrl+N
    open          打开           Ctrl+O
    save          保存           Ctrl+S
    save_as       另存为         Ctrl+Shift+S
    -----
    resize_canvas 调整画布大小
    clear_canvas  清空画布       Ctrl+R
    -----
    exit         退出           Alt+F4
edit 编辑(&E)
    clear_select    取消选择    Ctrl+D
    -----
    undo            撤销        Ctrl+Z
    redo            重做        Ctrl+Y
    -----
    cut             剪切        Ctrl+X
    copy            复制        Ctrl+C
    paste           粘贴        Ctrl+V
    remove_item     删除        Delete
    -----
    set_color       图元颜色
draw 绘制(&D)
    line         线段
        line_naive Naive
        line_dda   DDA
        line_bresenham Bresenham
    polygon      多边形
        polygon_dda DDA
        polygon_bresenham Bresenham
    ellipse      椭圆
    curve        曲线
        curve_bezier    Bézier
        curve_b_spline  B-spline
    -----
    set_pen       设置画笔       Ctrl+P  选择画笔颜色
transform   变换(&T)
    translate       平移
    rotate          旋转
    scale           缩放
    clip            裁剪
        clip_cohen_sutherland   Cohen-Sutherland
        clip_liang_barsky       Liang-Barsky
'''

# USAGE
# 通过缩进来表现菜单栏的层次结构，使其更加直观
# 每行为一个QMenu或QAction，必要格式为：
#   变量名  标题  [快捷键]  [状态栏说明]
#   变量名使生成的对象可以使调用者获得控制权 (通过传入vars()将对象定义在调用者处)
#        自动判断是Menu还是Action，并在变量名后加_menu/_act以示区分
#   变量名为------时，会在该菜单栏下添加分割线
# *没有进行错误检查*
