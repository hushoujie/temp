import argparse
import io
import json
import logging

import imageio
from PIL import Image, ImageEnhance, ImageOps
from deeputils.common import progress
from deeputils.logger import setup_log


class Decoder:
    def __init__(self, file_in: str, file_out: str, positions: list, locations: list, resolution: tuple, font_size: int):
        self.file = file_in
        if not self.file.endswith('.mp4'):
            raise TypeError('input file must be MP4 format')
        self.out = file_out
        self.video = imageio.get_reader(self.file, 'ffmpeg')
        logging.info('# of frames: {}'.format(self.video.count_frames()))
        self.resolution = resolution
        logging.info('Original resolution: {} x {}'.format(self.resolution[0], self.resolution[1]))
        self.shape = self.video.get_data(0).shape
        logging.info('Current resolution: {} x {}'.format(self.shape[0], self.shape[1]))
        self.positions = positions
        self.locations = locations
        self.font_size = font_size
        logging.info('Decoder is successfully initialized.')

    def run(self, frame_start, show_progress=True):
        scale_factor = (int(self.font_size * 2 * self.shape[0] / self.resolution[0]), int(self.font_size * 2 * self.shape[1] / self.resolution[1]))
        image_output = Image.new('RGBA', (len(self.positions) * scale_factor[0], len(self.locations[0]) * scale_factor[1]))
        for i in range(self.video.count_frames()):
            if show_progress:
                progress(i, self.video.count_frames())
            now = i + frame_start
            if now in self.positions:
                k = self.positions.index(now)
                for j in range(len(self.locations[k])):
                    image_decoded = self.decode(self.video.get_data(i), self.locations[k][j], self.resolution)
                    image_output.paste(image_decoded, (k * scale_factor[0], j * scale_factor[1]))
        if show_progress:
            print()
        image_output.save(self.out)
        logging.info('All done.')

    def decode(self, image, location, resolution):
        image_pil = Image.fromarray(image)
        original_width = resolution[1]
        original_height = resolution[0]
        x = image_pil.size[0] / original_width
        y = image_pil.size[1] / original_height
        x_min = location[0] * x - int(self.font_size * 0.5) * x
        y_min = location[1] * y - int(self.font_size * 0.5) * y
        x_max = location[0] * x + int(self.font_size * 1.5) * x
        y_max = location[1] * y + int(self.font_size * 1.5) * y
        image_crop = ImageEnhance.Contrast(ImageOps.invert(image_pil.crop((x_min, y_min, x_max, y_max)))).enhance(2)
        return image_crop


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--conf', type=str, required=True, help='configuration file')
    parser.add_argument('-s', '--start', type=int, default=0, help='starting frame of the original video')
    parser.add_argument('-o', '--output', type=str, default='output.png', help='output path, default: output.png')
    parser.add_argument('--greyscale', action='store_true', help='convert to greyscale image')
    parser.add_argument('--debug', action='store_true', help='show debug information')
    parser.add_argument('input', type=str, help='input file, must be MP4 format')
    args, _ = parser.parse_known_args()
    setup_log(logging.DEBUG if args.debug else logging.INFO)
    with io.open(args.conf, 'r', encoding='utf8') as f:
        conf = '\n'.join([i for i in f.readlines()])
    conf = json.loads(conf)
    Decoder(
        file_in=args.input,
        file_out=args.output,
        positions=conf['positions'],
        locations=conf['locations'],
        resolution=(conf['resolution'][0], conf['resolution'][1]),
        font_size=conf['font']['size']
    ).run(frame_start=args.start)
