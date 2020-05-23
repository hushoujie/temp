import argparse
import logging
import random
import os

from PIL import Image, ImageDraw, ImageFont
from deeputils.common import random_chars
from deeputils.logger import setup_log

PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS_PATH = PATH + '/image/fonts/mono.ttf'

class SSIS:
    @staticmethod
    def __blank(rgb):
        if rgb[0] == 0 and rgb[1] == 0 and rgb[2] == 0:
            return True
        elif rgb[0] == 255 and rgb[1] == 255 and rgb[2] == 255:
            return True

    @staticmethod
    def __int_to_bin(rgb):
        """
        Convert an integer tuple to a binary (string) tuple
        :param rgb: an integer tuple, e.g.: (220, 110, 96)
        :return: a string tuple, e.g.: ("00101010", "11101011", "00010110")
        """
        return ('{0:08b}'.format(rgb[0]),
                '{0:08b}'.format(rgb[1]),
                '{0:08b}'.format(rgb[2]))

    @staticmethod
    def __bin_to_int(rgb):
        """
        Convert a binary (string) tuple to an integer tuple
        :param rgb: a string tuple: e.g.: ("00101010", "11101011", "00010110")
        :return: an int tuple, e.g.: (220, 110, 96)
        """
        r, g, b = rgb
        return (int(r, 2),
                int(g, 2),
                int(b, 2))

    @staticmethod
    def __merge_rgb(rgb1, rgb2):
        """
        Merge two RGB tuples
        :param rgb1: a string tuple, e.g.: ("00101010", "11101011", "00010110")
        :param rgb2: another string tuple, e.g.: ("00101010", "11101011", "00010110")
        :return: an integer tuple with the two RGB values merged
        """
        r1, g1, b1 = rgb1
        r2, g2, b2 = rgb2
        rgb = (r1[:4] + r2[4:],
               g1[:4] + g2[4:],
               b1[:4] + b2[4:])
        return rgb

    @staticmethod
    def merge(img1, img2):
        # Check the images dimensions
        if img2.size[0] > img1.size[0] or img2.size[1] > img1.size[1]:
            raise ValueError('image 2 should not be larger than image 1')
        # Get the pixel map of the two images
        pixel_map1 = img1.load()
        pixel_map2 = img2.load()
        # Create a new image that will be outputted
        new_image = Image.new(img1.mode, img1.size)
        pixels_new = new_image.load()
        for i in range(img1.size[0]):
            for j in range(img1.size[1]):
                rgb1 = SSIS.__int_to_bin(pixel_map1[i, j])
                # Use original pixel as default
                rgb2 = rgb1
                # Check if the pixel map position is valid for the second image
                if i < img2.size[0] and j < img2.size[1]:
                    if not SSIS.__blank(pixel_map2[i, j]):
                        # Information is valid if not black or white
                        rgb2 = SSIS.__int_to_bin(pixel_map2[i, j])
                # Merge the two pixels and convert it to a integer tuple
                rgb = SSIS.__merge_rgb(rgb1, rgb2)
                pixels_new[i, j] = SSIS.__bin_to_int(rgb)
        return new_image

    @staticmethod
    def extract(img):
        # Load the pixel map
        pixel_map = img.load()
        # Create the new image and load the pixel map
        new_image = Image.new(img.mode, img.size)
        pixels_new = new_image.load()
        # Tuple used to store the image original size
        original_size = img.size
        for i in range(img.size[0]):
            for j in range(img.size[1]):
                # Get the RGB (as a string tuple) from the current pixel
                r, g, b = SSIS.__int_to_bin(pixel_map[i, j])
                # Extract the last 4 bits (corresponding to the hidden image)
                # Concatenate 4 zero bits because we are working with 8 bit
                rgb = (r[4:] + '0000',
                       g[4:] + '0000',
                       b[4:] + '0000')
                # Convert it to an integer tuple
                pixels_new[i, j] = SSIS.__bin_to_int(rgb)
                # If this is a 'valid' position, store it
                # as the last valid position
                if pixels_new[i, j] != (0, 0, 0):
                    original_size = (i + 1, j + 1)
        # Crop the image based on the 'valid' pixels
        new_image = new_image.crop((0, 0, original_size[0], original_size[1]))
        return new_image

    @staticmethod
    def secret(resolution, font_path=FONTS_PATH, chars=16):
        img = Image.new('RGB', resolution, color=(255, 255, 255))
        font = ImageFont.truetype(font_path, size=int(resolution[0] / 2 / chars))
        d = ImageDraw.Draw(img)
        for i in range(chars):
            d.text(
                (random.randrange(0, resolution[0]), random.randrange(0, resolution[0])),
                random_chars(1),
                fill=(random.randrange(0, 255), random.randrange(0, 255), random.randrange(0, 255)),
                font=font
            )
        return img


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true', help='show debug information')
    parser.add_argument('-i', '--img', type=str, help='image path, must in .jpg format')
    parser.add_argument('-p', '--path', type=str, default='.', help='output file path, default: .')
    parser.add_argument('-w', '--words', type=int, default=16, help='# of watermarks, default: 16')
    parser.add_argument('-f', '--font', type=str, default='./fonts/mono.ttf', help='font path, default: ./fonts/mono.ttf')
    parser.add_argument('action', type=str, choices=['encode', 'decode'], help='action, encode or decode')
    args, _ = parser.parse_known_args()
    setup_log(logging.DEBUG if args.debug else logging.INFO)
    ssis = SSIS()
    ssis_image = Image.open(args.img)
    if args.action == 'encode':
        ssis_secret = ssis.secret(ssis_image.size, args.font, args.words)
        ssis_secret.save('{}/secret.png'.format(args.path))
        ssis.merge(ssis_image, ssis_secret).save('{}/output.jpg'.format(args.path), format='JPEG', subsampling=0, quality=100)
    elif args.action == 'decode':
        ssis.extract(ssis_image).save('{}/extract.png'.format(args.path))
