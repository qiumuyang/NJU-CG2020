from copy import deepcopy
from cg_algorithms import rotate, scale
from util import epsilon


def p_diff(p1, p2):
    return sum(abs(p1[i] - p2[i]) for i in range(2))


class PList(list):
    def __init__(self, data=[]):
        super().__init__(data)
        self.__reset()
        if isinstance(data, PList):
            self.r = data.r
            self.rc = deepcopy(data.rc)
            self.sx = data.sx
            self.sy = data.sy
            self.sc = deepcopy(data.sc)

    @property
    def real(self):
        sx = self.sx
        sy = self.sy
        scaled = scale(self, *self.sc, sx, sy) if self.sc else self
        rotated = rotate(scaled, *self.rc, self.r) if self.rc else scaled
        return rotated

    def rotate(self, center, r):
        if not self.rc:
            self.r = r
            self.rc = center
        elif p_diff(center, self.rc) < 5 and not self.sc:
            self.r += r
        else:
            self.update()
            self.r = r
            self.rc = center

    def scale(self, center, sx, sy):
        if not self.sc:
            self.sx = sx
            self.sy = sy
            self.sc = center
        elif p_diff(center, self.sc) < 5 and not self.rc:
            next_sx = self.sx * sx
            next_sy = self.sy * sy
            self.sx = next_sx if abs(next_sx) > epsilon else self.sx
            self.sy = next_sy if abs(next_sy) > epsilon else self.sy
        else:
            self.update()
            self.sx = sx
            self.sy = sy
            self.sc = center

    def scale_set(self, center, sx, sy):
        if self.rc or (self.sc and p_diff(center, self.sc) > 5):
            self.update()
        sx if abs(sx) > epsilon else (epsilon if sx > 0 else -epsilon)
        sy if abs(sy) > epsilon else (epsilon if sy > 0 else -epsilon)
        self.sx = sx
        self.sy = sy
        self.sc = center

    def __reset(self):
        self.r = 0
        self.rc = None
        self.sx = 1
        self.sy = 1
        self.sc = None

    def update(self):
        self.__init__(self.real)

    def __repr__(self) -> str:
        content = super().__repr__()
        tail = ''
        if self.rc:
            tail += f'\n\trotate: {self.rc} {self.r}°'
        if self.sc:
            tail += f'\n\tscale: {self.sc} {self.sx} {self.sy}'
        return content + tail


if __name__ == "__main__":
    p1 = PList([[50, 100], [100, 100], [100, 50], [50, 50]])
    p1.r = 90
    p1.rc = [50, 75]
    print(p1)
    p1.update()
    print(p1)
