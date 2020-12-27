#!/usr/bin/env python
# -*- coding:utf-8 -*-

# 本文件只允许依赖math库
import math


def draw_line(p_list, algorithm):
    """绘制线段

    :param p_list: (list of list of int: [[x0, y0], [x1, y1]]) 线段的起点和终点坐标
    :param algorithm: (string) 绘制使用的算法，包括'DDA'和'Bresenham'，此处的'Naive'仅作为示例，测试时不会出现
    :return: (list of list of int: [[x_0, y_0], [x_1, y_1], [x_2, y_2], ...]) 绘制结果的像素点坐标列表
    """
    x0, y0 = p_list[0]
    x1, y1 = p_list[1]
    result = []
    if algorithm == 'Naive':
        if x0 == x1:
            for y in range(y0, y1 + 1):
                result.append((x0, y))
        else:
            if x0 > x1:
                x0, y0, x1, y1 = x1, y1, x0, y0
            k = (y1 - y0) / (x1 - x0)
            for x in range(x0, x1 + 1):
                result.append((x, int(y0 + k * (x - x0))))
    elif algorithm == 'DDA':
        if x0 == x1:
            if y0 > y1:
                y0, y1 = y1, y0
            result = [(x0, y) for y in range(y0, y1 + 1)]
        else:
            k = (y1 - y0) / (x1 - x0)
            if abs(k) <= 1:
                if x0 > x1:
                    x0, y0, x1, y1 = x1, y1, x0, y0
                result = [(x, round(y0 + k * (x - x0)))
                          for x in range(x0, x1 + 1)]
            else:
                if y0 > y1:
                    x0, y0, x1, y1 = x1, y1, x0, y0
                result = [(x0 + round(1 / k * (y - y0)), y)
                          for y in range(y0, y1 + 1)]
    elif algorithm == 'Bresenham':
        if x0 == x1:
            if y0 > y1:
                y0, y1 = y1, y0
            result = [(x0, y) for y in range(y0, y1 + 1)]
        else:
            result = []
            k = (y1 - y0) / (x1 - x0)
            inc = 1 if k > 0 else -1
            dy = abs(y1 - y0)
            dx = abs(x1 - x0)
            if abs(k) <= 1:
                if x0 > x1:
                    x0, y0, x1, y1 = x1, y1, x0, y0
                p = 2 * dy - dx
                y = y0
                for x in range(x0, x1 + 1):
                    if p > 0:
                        y += inc
                        p += 2 * (dy - dx)
                    else:
                        p += 2 * dy
                    result.append((x, y))
            else:
                if y0 > y1:
                    x0, y0, x1, y1 = x1, y1, x0, y0
                p = 2 * dx - dy
                x = x0
                for y in range(y0, y1 + 1):
                    if p > 0:
                        x += inc
                        p += 2 * (dx - dy)
                    else:
                        p += 2 * dx
                    result.append((x, y))
    return result


def draw_polygon(p_list, algorithm):
    """绘制多边形

    :param p_list: (list of list of int: [[x0, y0], [x1, y1], [x2, y2], ...]) 多边形的顶点坐标列表
    :param algorithm: (string) 绘制使用的算法，包括'DDA'和'Bresenham'
    :return: (list of list of int: [[x_0, y_0], [x_1, y_1], [x_2, y_2], ...]) 绘制结果的像素点坐标列表
    """
    result = []
    for i in range(len(p_list)):
        line = draw_line([p_list[i - 1], p_list[i]], algorithm)
        result += line
    return result


def draw_fold_line(p_list, algorithm):
    """绘制折线段

    :param p_list: (list of list of int: [[x0, y0], [x1, y1], [x2, y2], ...]) 折线的顶点坐标列表
    :param algorithm: (string) 绘制使用的算法，包括'DDA'和'Bresenham'
    :return: (list of list of int: [[x_0, y_0], [x_1, y_1], [x_2, y_2], ...]) 绘制结果的像素点坐标列表
    """
    result = []
    for i in range(1, len(p_list)):
        line = draw_line([p_list[i - 1], p_list[i]], algorithm)
        result += line
    return result


def draw_ellipse(p_list, algorithm=None):
    """绘制椭圆（采用中点圆生成算法）

    :param p_list: (list of list of int: [[x0, y0], [x1, y1]]) 椭圆的矩形包围框对角顶点坐标
    :param algorithm: (None) 统一接口形式占位用
    :return: (list of list of int: [[x_0, y_0], [x_1, y_1], [x_2, y_2], ...]) 绘制结果的像素点坐标列表
    """
    x0, y0 = p_list[0]
    x1, y1 = p_list[1]
    result = []
    if x0 > x1:
        x0, x1 = x1, x0
    if y0 > y1:
        y0, y1 = y1, y0
    rx = (x1 - x0) / 2
    ry = (y1 - y0) / 2
    x, y = 0, ry
    quadrant = [(x, y)]

    p = ry**2 - rx**2*ry + rx**2/4
    while ry**2*x < rx**2*y:
        if p < 0:
            p += 2*ry**2*x + 3*ry**2
        else:
            p += 2*ry**2*x + 3*ry**2 + 2*rx**2*(1 - y)
            y -= 1
        x += 1
        quadrant.append((x, y))

    p = ry**2*(x + 0.5)**2 + rx**2*(y - 1)**2 - rx**2*ry**2
    while y > 0:
        if p <= 0:
            p += (-2)*rx**2*y + 3*rx**2 + 2*ry**2*(1 + x)
            x += 1
        else:
            p += (-2)*rx**2*y + 3*rx**2
        y -= 1
        quadrant.append((x, y))

    xm = (x0 + x1) / 2
    ym = (y0 + y1) / 2
    # when x0 + x1 is odd, round() will continuously get some int with 0.5,
    # if not subtracted by a small value, we'll get round(0.5), round(1.5), round(2.5), ...
    # they'll be rounded to 0, 2, 2, ...,
    # which will cause a discrete effect as shown in example.
    # FROM https://docs.python.org/3.8/library/functions.html?highlight=round#round :
    # The behavior of round() for floats can be surprising:
    # for example, round(2.675, 2) gives 2.67 instead of the expected 2.68.
    # This is not a bug: it’s a result of the fact that
    # most decimal fractions can’t be represented exactly as a float.
    result = [(round(nx * x + xm - 0.001), round(ny * y + ym - 0.001))
              for x, y in quadrant for nx in (-1, 1) for ny in (-1, 1)]
    return result


def draw_curve(p_list, algorithm, p_cnt=300):
    """绘制曲线

    :param p_list: (list of list of int: [[x0, y0], [x1, y1], [x2, y2], ...]) 曲线的控制点坐标列表
    :param algorithm: (string) 绘制使用的算法，包括'Bezier'和'B-spline'（三次均匀B样条曲线，曲线不必经过首末控制点）
    :param p_cnt: (int) 曲线取样点个数
    :return: (list of list of int: [[x_0, y_0], [x_1, y_1], [x_2, y_2], ...]) 绘制结果的像素点坐标列表
    """
    result = []
    if algorithm == 'Bezier':
        for u in range(p_cnt):
            u = u / p_cnt
            plist = [(x, y) for x, y in p_list]
            for r in range(len(plist)):
                for i in range(len(plist)-1-r):
                    x0, y0 = plist[i]
                    x1, y1 = plist[i+1]
                    x = (1-u) * x0 + u * x1
                    y = (1-u) * y0 + u * y1
                    plist[i] = (x, y)
            x, y = plist[0]
            result.append((round(x), round(y)))
    elif algorithm == 'B-spline':
        def base_func(i, k, u):
            if k == 1:
                return i <= u < i + 1
            return (u - i)/(k - 1)*base_func(i, k-1, u) + (i + k - u)/(k - 1)*base_func(i+1, k-1, u)

        k = 4
        for u in range(p_cnt):
            u = u / p_cnt * len(p_list)
            if u < k - 1:
                continue
            x, y = 0, 0
            for i in range(len(p_list)):
                b = base_func(i, k, u)
                x += p_list[i][0] * b
                y += p_list[i][1] * b
            result.append((round(x), round(y)))

    # use this func to connect the discrete points
    return draw_fold_line(result, 'DDA')


def translate(p_list, dx, dy):
    """平移变换

    :param p_list: (list of list of int: [[x0, y0], [x1, y1], [x2, y2], ...]) 图元参数
    :param dx: (int) 水平方向平移量
    :param dy: (int) 垂直方向平移量
    :return: (list of list of int: [[x_0, y_0], [x_1, y_1], [x_2, y_2], ...]) 变换后的图元参数
    """
    return [[x + dx, y + dy] for x, y in p_list]


def rotate(p_list, x, y, r):
    """旋转变换（除椭圆外）

    :param p_list: (list of list of int: [[x0, y0], [x1, y1], [x2, y2], ...]) 图元参数
    :param x: (int) 旋转中心x坐标
    :param y: (int) 旋转中心y坐标
    :param r: (int) 逆时针旋转角度（°） # Original: 顺时针
    :return: (list of list of int: [[x_0, y_0], [x_1, y_1], [x_2, y_2], ...]) 变换后的图元参数
    """
    arc = r / 360 * 2 * math.pi
    cos = math.cos(arc)
    sin = math.sin(arc)
    return [(round((x0 - x)*cos - (y0 - y)*sin + x),
             round((x0 - x)*sin + (y0 - y)*cos + y)) for x0, y0 in p_list]


def scale(p_list, x, y, sx, sy=None):
    """缩放变换

    :param p_list: (list of list of int: [[x0, y0], [x1, y1], [x2, y2], ...]) 图元参数
    :param x: (int) 缩放中心x坐标
    :param y: (int) 缩放中心y坐标
    :param sx: (float) x方向缩放倍数
    :param sy: (float) y方向缩放倍数
    :return: (list of list of int: [[x_0, y_0], [x_1, y_1], [x_2, y_2], ...]) 变换后的图元参数
    """
    sy = sx if not sy else sy
    return [(round((x0 - x)*sx + x), round((y0 - y)*sy + y)) for x0, y0 in p_list]


def clip(p_list, x_min, y_min, x_max, y_max, algorithm):
    """线段裁剪

    :param p_list: (list of list of int: [[x0, y0], [x1, y1]]) 线段的起点和终点坐标
    :param x_min: 裁剪窗口左上角x坐标
    :param y_min: 裁剪窗口左上角y坐标
    :param x_max: 裁剪窗口右下角x坐标
    :param y_max: 裁剪窗口右下角y坐标
    :param algorithm: (string) 使用的裁剪算法，包括'Cohen-Sutherland'和'Liang-Barsky'
    :return: (list of list of int: [[x_0, y_0], [x_1, y_1]]) 裁剪后线段的起点和终点坐标
    """
    x0, y0 = p_list[0]
    x1, y1 = p_list[1]
    if x_min > x_max:
        x_max, x_min = x_min, x_max
    if y_min > y_max:
        y_max, y_min = y_min, y_max
    if algorithm == 'Cohen-Sutherland':
        LEFT, RIGHT, UP, DOWN = 8, 4, 2, 1

        def encode(x, y):
            ret = 0
            ret |= LEFT * (x < x_min)
            ret |= RIGHT * (x > x_max)
            ret |= UP * (y < y_min)
            ret |= DOWN * (y > y_max)
            return ret

        code0 = encode(x0, y0)
        code1 = encode(x1, y1)
        if (code0 & code1):  # not any part inside box
            return []
        while code0 or code1:
            if not code0:
                x0, y0, x1, y1 = x1, y1, x0, y0
            flag = encode(x0, y0)
            if flag & LEFT or flag & RIGHT:
                x = x_min if flag & LEFT else x_max
                y = round((y0 - y1) / (x0 - x1) *
                          (x - x1) + y1) if x0 != x1 else y0
            elif flag & UP or flag & DOWN:
                y = y_min if flag & UP else y_max
                x = round((x0 - x1) / (y0 - y1) *
                          (y - y1) + x1) if y0 != y1 else x0
            else:
                x, y = x0, y0
            x0, y0 = x, y
            code0 = encode(x0, y0)
            code1 = encode(x1, y1)
            if (code0 & code1):
                return []
    elif algorithm == 'Liang-Barsky':
        ps = [x0 - x1, x1 - x0, y0 - y1, y1 - y0]
        qs = [x0 - x_min, x_max - x0, y0 - y_min, y_max - y0]
        u_min, u_max = 0, 1
        for p, q in zip(ps, qs):
            if p == 0:
                if q < 0:
                    return []
            elif p < 0:
                u_min = max(u_min, q/p)
            else:
                u_max = min(u_max, q/p)
            if u_min > u_max:
                return []
        dx, dy = x1 - x0, y1 - y0
        if u_max < 1:
            x1, y1 = round(x0 + u_max*dx), round(y0 + u_max*dy)
        if u_min > 0:
            x0, y0 = round(x0 + u_min*dx), round(y0 + u_min*dy)
    return [(x0, y0), (x1, y1)]
