import argparse
import io
import json
import logging
import os
import platform
import random
import string
from datetime import datetime

import imageio
import numpy
from PIL import Image, ImageDraw, ImageFont
from deeputils.common import progress
from deeputils.logger import setup_log


class Encoder:
    def __init__(self, file_in: str, path_out: str, strength: int = 32, duplicates: int = 1, font_path: str = os.path.join(os.path.dirname(__file__), '..', 'fonts', 'mono.ttf'), font_size: int = 12, alpha=120, copies=1, ciphers=string.digits):
        self.file = file_in
        if not self.file.endswith('.mp4'):
            raise TypeError('input file must be MP4 format')
        logging.info('Input file: %s', self.file)
        self.out = path_out
        if not os.path.exists(self.out):
            os.makedirs(self.out)
        self.video = imageio.get_reader(self.file, 'ffmpeg')
        self.frames = self.video.count_frames()
        logging.info('# of frames: %d', self.frames)
        self.shape = self.video.get_data(0).shape
        logging.info('Resolution: %d x %d', self.shape[0], self.shape[1])
        logging.info('# of copies: {}'.format(copies))
        logging.info('Ciphers: {}'.format(''.join(ciphers)))
        self.ciphers = list()
        while len(ciphers) < strength:
            ciphers += ciphers
        for i in range(copies):
            c = ciphers.copy()
            random.shuffle(c)
            self.ciphers.append(c[:strength])
        self.font = {
            'path': font_path,
            'size': font_size
        }
        self.alpha = alpha
        self.positions = list(range(self.frames))
        random.shuffle(self.positions)
        self.positions = self.positions[:strength]
        self.positions.sort()
        self.locations = list()
        logging.info('# of locations per frame: {}'.format(duplicates))
        for i in range(strength):
            locations = list()
            for j in range(duplicates):
                locations.append((
                    random.randint(self.font['size'] * 2, self.shape[1] - self.font['size'] * 2),
                    random.randint(self.font['size'] * 2, self.shape[0] - self.font['size'] * 2)
                ))
            self.locations.append(locations)
        with io.open(os.path.join(self.out, 'conf.json'), 'w', encoding='utf8') as f:
            json.dump({
                't': datetime.now().timestamp(),
                'handler': platform.node(),
                'input': file_in,
                'length': self.frames,
                'resolution': self.video.get_data(0).shape,
                'font': self.font,
                'alpha': self.alpha,
                'ciphers': [''.join(i) for i in self.ciphers],
                'positions': self.positions,
                'locations': self.locations,
            }, f, indent=2, ensure_ascii=False)
        logging.info('Encoder is successfully initialized.')

    def run(self, show_progress=True):
        copies = len(self.ciphers)
        writers = [imageio.get_writer(os.path.join(self.out, '{}.mp4'.format(i)), fps=self.video.get_meta_data()['fps']) for i in range(copies)]
        problems = []
        for i in range(self.frames):
            if show_progress:
                progress(i, self.frames)
            try:
                image = self.video.get_data(i).copy()
            except imageio.core.format.CannotReadFrameError:
                problems.append(i)
                image = imageio.core.util.Image(numpy.empty((self.shape[0], self.shape[1], 3), dtype=numpy.uint8))
            for j in range(copies):
                if i in self.positions:
                    k = self.positions.index(i)
                    m = self.encode(image, self.ciphers[j][k], self.locations[k])
                else:
                    m = Image.fromarray(image).convert("RGBA")
                writers[j].append_data(numpy.array(m))
        for i in range(copies):
            writers[i].close()
        if show_progress:
            print()
        for i in problems:
            logging.error('Could not read frame: %d', i)
        logging.info('All done.')

    def encode(self, image, cipher, locations: list):
        image_bg = Image.fromarray(image).convert("RGBA")
        image_mask = Image.new('RGBA', Image.fromarray(image).size, (255, 255, 255, 0))
        image_ds = ImageDraw.Draw(image_mask)
        for location in locations:
            pixel = image_bg.getpixel(location)
            image_ds.text(location, cipher, font=ImageFont.truetype(self.font['path'], self.font['size']), fill=(255 - pixel[0], 255 - pixel[1], 255 - pixel[2], self.alpha))
        return Image.alpha_composite(image_bg, image_mask)


def init_ciphers(mode):
    ciphers = {
        'en': list(string.ascii_letters + string.digits),
        'jp': list('あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわゐゑをん' + 'アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヰヱヲン'),
        'symbol': list('●')
    }
    return ciphers[mode]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--length', type=int, default=10, help='encryption key length, default: 10')
    parser.add_argument('-k', '--locations', type=int, default=1, help='# of locations per frame, default: 1')
    parser.add_argument('-f', '--font', type=str, default='mono', choices=['mono', 'jp'], help='font (mono or jp), default: mono')
    parser.add_argument('-y', '--symbol', type=str, default='en', choices=['en', 'jp', 'symbol'], help='font (en, jp, or symbol), default: en')
    parser.add_argument('-s', '--size', type=int, default=12, help='font size, default: 12')
    parser.add_argument('-c', '--copy', type=int, default=1, help='# of copies, default: 1')
    parser.add_argument('-o', '--output', type=str, default='./output/', help='output path, default: ./output/')
    parser.add_argument('--debug', action='store_true', help='show debug information')
    parser.add_argument('input', type=str, help='input file, must be MP4 format')
    args, _ = parser.parse_known_args()
    setup_log(logging.DEBUG if args.debug else logging.INFO)
    Encoder(
        file_in=args.input,
        path_out=args.output,
        strength=args.length,
        duplicates=args.locations,
        font_path=os.path.join(os.path.dirname(__file__), '..', 'fonts', '{}.ttf'.format(args.font)),
        font_size=args.size,
        copies=args.copy,
        ciphers=init_ciphers(args.symbol)
    ).run()
