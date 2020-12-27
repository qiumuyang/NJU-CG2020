from PIL import Image
import math
import operator
from functools import reduce


def image_contrast(img1, img2):
    image1 = Image.open(img1)
    image2 = Image.open(img2)
    h1 = image1.histogram()
    h2 = image2.histogram()
    result = math.sqrt(reduce(operator.add, list(
        map(lambda a, b: (a-b)**2, h1, h2)))/len(h1))
    return result


def image_blend(img1, img2):
    image1 = Image.open(img1)
    image2 = Image.open(img2)
    return Image.blend(image1, image2, 0.5)


if __name__ == "__main__":
    srcfolder = 'output2'
    dstfolder = 'output'
    for i in range(1, 6):
        src = f'{srcfolder}/{i}.bmp'
        dst = f'{dstfolder}/{i}.bmp'
        print(image_contrast(src, dst))
