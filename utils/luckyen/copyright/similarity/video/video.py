import argparse
import logging
import os
import uuid

import cv2
import imageio
import requests
from PIL import Image
from deeputils.common import progress
from deeputils.logger import setup_log
from skimage.measure import compare_ssim


class Similarity:
    def __init__(self, file_in: str, path_out: str, callback: tuple = None, task_id=None):
        self.task_id = task_id
        logging.info('Task ID: %s', self.task_id)
        self.file = file_in
        if not self.file.endswith('.mp4'):
            raise TypeError('input file must be MP4 format')
        self.out = path_out
        if not os.path.exists(self.out):
            os.makedirs(self.out)
        self.video = imageio.get_reader(self.file, 'ffmpeg')
        logging.info('# of frames: {}'.format(len(self.video)))
        self.shape = self.video.get_data(0).shape
        logging.info('Resolution: {} x {}'.format(self.shape[0], self.shape[1]))
        self.callback = callback
        if self.callback is not None:
            logging.info('Callback is enabled: %s %s', self.callback[0], self.callback[1])
        logging.info('Similarity comparator is successfully initialized.')

    def compare(self, file_in: str):
        m = cv2.imread(file_in)
        similarities = list()
        for i in range(len(self.video)):
            progress(i, len(self.video))
            if i == 720:
                try:
                    score = compare_ssim(self.video.get_data(i), m, multichannel=True)
                except imageio.core.format.CannotReadFrameError:
                    score = 0
            else:
                score = 0
            similarities.append(score)
        print()
        k = max(similarities)
        n = similarities.index(k)
        logging.info('Max similarity (%f) in frame: %d', k, n)
        Image.fromarray(self.video.get_data(n)).save(os.path.join(self.out, '{}.jpg'.format(self.task_id)))
        if self.callback is not None:
            logging.info('Sending callback...')
            return getattr(requests, self.callback[0])(self.callback[1], json={
                'msgtype': 'text',
                'text': {
                    'content': 'Similarity comparing task is finished, best frame {} with similarity {}: {}'.format(n, k, self.task_id)
                }
            })


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output', type=str, default='./', help='output path, default: ./')
    parser.add_argument('--id', type=str, default=str(uuid.uuid4()), help='task ID, a random ID will be generated if not provided')
    parser.add_argument('--debug', action='store_true', help='show debug information')
    parser.add_argument('video', type=str, help='input video, must be MP4 format')
    parser.add_argument('image', type=str, help='input image, must be JPG format')
    args, _ = parser.parse_known_args()
    setup_log(logging.DEBUG if args.debug else logging.INFO)
    Similarity(
        file_in=args.video,
        path_out=args.output,
        callback=(args.callback_method, args.callback_url) if args.callback_url else None,
        task_id=args.id
    ).compare(args.image)
