import argparse
import logging

import cv2
import numpy
from PIL import Image
from deeputils.logger import setup_log
from skimage.metrics import variation_of_information


class EntropySimilarity:
    def __init__(self, f_base: str):
        self.image_base = cv2.imread(f_base)


    def compare(self, f_quote: str):
        images = [self.image_base.copy(), cv2.imread(f_quote)]
        shape_min = (min([i.shape[1] for i in images]), min([i.shape[0] for i in images]))
        logging.debug('Comparing size: %s', shape_min)
        for i in range(len(images)):
            images[i] = Image.fromarray(images[i]).resize(shape_min, Image.ANTIALIAS)
            images[i] = numpy.array(images[i])
        return numpy.mean(variation_of_information(images[0], images[1]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true', help='show debug information')
    parser.add_argument('image1', type=str, help='image 1')
    parser.add_argument('image2', type=str, help='image 2')
    args, _ = parser.parse_known_args()
    setup_log(logging.DEBUG if args.debug else logging.INFO)
    print(EntropySimilarity(f_base=args.image1).compare(args.image2))
