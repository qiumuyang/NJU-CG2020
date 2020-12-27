import math


k_225 = math.sqrt(2) - 1
k_675 = math.sqrt(2) + 1


class Direc:
    EMPTY = 0
    LEFT = 1
    RIGHT = 2
    TOP = 4
    BOTTOM = 8
    LEFT_TOP = 5
    RIGHT_TOP = 6
    LEFT_BOTTOM = 9
    RIGHT_BOTTOM = 10

    def __init__(self, dire):
        self.direc = dire

    def __eq__(self, o: object) -> bool:
        if isinstance(o, int):
            return self.direc == o
        if isinstance(o, Direc):
            return self.direc == o.direc

    def __add__(self, o: object):
        if isinstance(o, int):
            return Direc(o | self.direc)
        if isinstance(o, Direc):
            return Direc(o.direc | self.direc)

    def __invert__(self):
        tmp = 0
        if self.direc & self.LEFT:
            tmp |= self.RIGHT
        if self.direc & self.RIGHT:
            tmp |= self.LEFT
        if self.direc & self.TOP:
            tmp |= self.BOTTOM
        if self.direc & self.BOTTOM:
            tmp |= self.TOP
        return Direc(tmp)

    @property
    def isVertical(self):
        return self.direc & self.TOP or self.direc & self.BOTTOM

    @property
    def isHorizontal(self):
        return self.direc & self.LEFT or self.direc & self.RIGHT


def calculate_angle(pt1, pt2, vertex):
    '''计算两边夹角

    :param pt1, pt2: ((int, int)) 确定角两边所在直线的点坐标
    :param vertex: ((int, int)) 角顶点坐标
    :return: (int) 夹角大小(角度制)
    '''
    dist1, dist2 = [
        math.sqrt((pt[0]-vertex[0])**2 + (pt[1]-vertex[1])**2) for pt in [pt1, pt2]]
    dist_pt = math.sqrt((pt1[0] - pt2[0])**2 + (pt1[1] - pt2[1])**2)
    if dist1 == 0 or dist2 == 0:
        return 0
    cos = (dist1**2 + dist2**2 - dist_pt**2) / (2*dist1*dist2)
    try:
        arc = math.acos(cos)
    except:
        return 0
    theta = arc * 360 / (2*math.pi)  # should not round
    vec = [tuple(pt[i] - vertex[i] for i in range(2)) for pt in [pt1, pt2]]
    dot_mult = vec[0][0]*vec[1][1] - vec[0][1]*vec[1][0]
    return theta if dot_mult > 0 else -1*theta


def p_normalize(do_norm, primitive, p0, p1):
    '''点坐标规则化

    :param do_norm: (bool) 是否进行规则化
    :param primitive: (str) 图元类型
    :param p0, p1: ((int, int)) 基准点与待规则化点坐标
    '''
    if not do_norm:
        return p1
    if primitive == 'ellipse':
        d = min(abs(p1[i] - p0[i]) for i in range(2))
        return [p0[i] + d if p1[i] > p0[i] else p0[i] - d for i in range(2)]
    elif primitive == 'line':
        x0, y0 = p0
        x1, y1 = p1
        if x0 == x1:
            return p1
        k = (y0 - y1) / (x0 - x1)
        if abs(k) <= k_225:
            return (x1, y0)
        elif abs(k) <= k_675:
            if k > 0:
                return (int((y1 - y0 + x0 + x1)/2), int((y1 + y0 - x0 + x1)/2))
            else:
                return (int((y0 - y1 + x0 + x1)/2), int((y1 + y0 + x0 - x1)/2))
        else:
            return (x0, y1)
    return p1


def to_border(border, p) -> Direc:
    thres = 10
    x_lim, y_lim = border
    x, y = p
    direc = Direc(Direc.EMPTY)
    dl = abs(x - x_lim[0])
    dr = abs(x - x_lim[1])
    dt = abs(y - y_lim[0])
    db = abs(y - y_lim[1])
    if x < x_lim[0] - thres \
            or x > x_lim[1] + thres \
            or y < y_lim[0] - thres \
            or y > y_lim[1] + thres:
        return direc
    hdirec = Direc.LEFT if dl < dr else Direc.RIGHT
    vdirec = Direc.TOP if dt < db else Direc.BOTTOM
    dh = min(dl, dr)
    dv = min(dt, db)
    if dh < thres:
        direc += hdirec
    if dv < thres:
        direc += vdirec
    return direc


def p_box_dist(point, rect):
    pt0 = rect.bottomLeft()
    pt1 = rect.topRight()
    xs = [round(t) for t in (pt0.x(), pt1.x())]
    ys = [round(t) for t in (pt0.y(), pt1.y())]
    dists = [abs(point[j] - axis[i])
             for i in range(2) for j, axis in enumerate([xs, ys])]
    return min(dists)
