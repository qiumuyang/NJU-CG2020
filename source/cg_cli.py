#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import os
import cg_algorithms as alg
import numpy as np
from PIL import Image


DRAW = ['Line', 'Polygon', 'Ellipse', 'Curve']
DRAW_FUNC = {shape.lower(): vars(
    alg)[f'draw_{shape.lower()}'] for shape in DRAW}
TRANSFORM = ['translate', 'rotate', 'scale', 'clip']
TRANSFORM_FUNC = {trans: vars(alg)[trans] for trans in TRANSFORM}


def parse_num(num: str):
    '''str -> int/float/str

    :param num: str
    :return: str | int | float
    '''
    if num.isdigit() or (num[1:].isdigit() and num[0] == '-'):
        return int(num)
    if all(tok.isdigit() for tok in num.split('.', 1)):
        return float(num)
    return num


if __name__ == '__main__':
    input_file = sys.argv[1] if len(sys.argv) > 1 else None
    output_dir = sys.argv[2] if len(sys.argv) > 2 else input('output_dir: ')
    os.makedirs(output_dir, exist_ok=True)

    item_dict = {}
    pen_color = np.zeros(3, np.uint8)
    width = 0
    height = 0

    fp = open(input_file, 'r') if input_file else sys.stdin
    for line in fp.readlines():
        line = line.strip()
        if line.startswith('#') or not line:
            continue
        line = line.split(' ')
        if line[0] == 'resetCanvas':
            width = int(line[1])
            height = int(line[2])
            item_dict = {}
        elif line[0] == 'saveCanvas':
            save_name = line[1]
            canvas = np.zeros([height, width, 3], np.uint8)
            canvas.fill(255)
            for item_type, p_list, algorithm, color in item_dict.values():
                if item_type in DRAW_FUNC:
                    pixels = DRAW_FUNC[item_type](p_list, algorithm)
                    for x, y in pixels:
                        canvas[y, x] = color
            Image.fromarray(canvas).save(os.path.join(
                output_dir, save_name + '.bmp'), 'bmp')
        elif line[0] == 'setColor':
            pen_color[0] = int(line[1])
            pen_color[1] = int(line[2])
            pen_color[2] = int(line[3])
        elif line[0][:4] == 'draw' and line[0][4:] in DRAW:
            item_type = line[0][4:].lower()
            item_id = line[1]
            digits = [int(s) for s in line[2:] if s.isdigit()]
            d1 = [d for i, d in enumerate(digits) if i % 2 == 0]
            d2 = [d for i, d in enumerate(digits) if i % 2 == 1]
            p_list = list(zip(d1, d2))
            algorithm = line[-1] if item_type != 'ellipse' else None
            item_dict[item_id] = [item_type, p_list,
                                  algorithm, np.array(pen_color)]
        elif line[0] in TRANSFORM:
            item_id = line[1]
            if line[0] == 'rotate' and item_dict[item_id][0] == 'ellipse':
                # unable to rotate ellipse
                pass
            else:
                args = [parse_num(s) for s in line[2:]]
                original_p_list = item_dict[item_id][1]
                args.insert(0, original_p_list)
                p_list = TRANSFORM_FUNC[line[0]](*args)
                if not p_list:  # line-clip
                    item_dict.pop(item_id)
                else:
                    item_dict[item_id][1] = p_list

    if fp != sys.stdin:
        fp.close()
