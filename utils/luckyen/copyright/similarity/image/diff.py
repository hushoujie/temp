import argparse
import logging

import cv2
import numpy
from PIL import Image, ImageOps
from deeputils.logger import setup_log


class DiffSimilarity:
    def __init__(self, f_base: str):
        self.image_base = cv2.imread(f_base)

    def compare(self, f_quote: str, output=None):
        images = [self.image_base.copy(), cv2.imread(f_quote)]
        shape_min = (min([i.shape[1] for i in images]), min([i.shape[0] for i in images]))
        logging.debug('Comparing size: %s', shape_min)
        for i in range(len(images)):
            images[i] = numpy.array(Image.fromarray(images[i]).resize(shape_min, Image.ANTIALIAS))
        img = ImageOps.invert(Image.fromarray(images[1] - images[0], 'RGB'))
        img.save(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true', help='show debug information')
    parser.add_argument('-o', '--output', type=str, default='output.png', help='output file path, default: output.png')
    parser.add_argument('image1', type=str, help='image 1')
    parser.add_argument('image2', type=str, help='image 2')
    args, _ = parser.parse_known_args()
    setup_log(logging.DEBUG if args.debug else logging.INFO)
    DiffSimilarity(f_base=args.image1).compare(args.image2, args.output)
