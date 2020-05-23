import argparse
import logging
import os

import imageio
import numpy
from PIL import Image
from deeputils.common import progress
from deeputils.logger import setup_log


class Splitter:
    def __init__(self, file_in: str, path_out: str, shard: int = 100):
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
        self.shard = shard
        logging.info('# of frames per shard: {}'.format(self.shard))
        logging.info('Splitter is successfully initialized.')

    def run(self, show_progress=True):
        k = -1
        writer = None
        problems = []
        for i in range(self.frames):
            if show_progress:
                progress(i, self.frames)
            if i % self.shard == 0:
                if writer is not None:
                    logging.debug('Closing: %d', k)
                    writer.close()
                k += 1
                logging.debug('Opening: %d', k)
                writer = imageio.get_writer(os.path.join(self.out, '{}.mp4'.format(k)), fps=self.video.get_meta_data()['fps'])
            try:
                image = self.video.get_data(i).copy()
            except imageio.core.format.CannotReadFrameError:
                problems.append(i)
            else:
                writer.append_data(numpy.array(Image.fromarray(image).convert("RGBA")))
        if writer is not None:
            writer.close()
        if show_progress:
            print()
        for i in problems:
            logging.error('Could not read frame: %d', i)
        logging.info('All done.')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--shard', type=int, default=100, help='# of frames per shard, default: 100')
    parser.add_argument('-o', '--output', type=str, default='./output/', help='output path, default: ./output/')
    parser.add_argument('--debug', action='store_true', help='show debug information')
    parser.add_argument('input', type=str, help='input file, must be MP4 format')
    args, _ = parser.parse_known_args()
    setup_log(logging.DEBUG if args.debug else logging.INFO)
    Splitter(
        file_in=args.input,
        path_out=args.output,
        shard=args.shard
    ).run()
