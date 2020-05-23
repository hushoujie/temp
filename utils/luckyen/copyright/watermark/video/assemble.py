import argparse
import io
import json
import logging
import os
import platform
from datetime import datetime

import imageio
import numpy
from PIL import Image
from deeputils.common import progress, Dict2StrSafe
from deeputils.logger import setup_log


class Shard(Dict2StrSafe):
    def __init__(self, file_video: str, file_conf: str, seq: int = None):
        self.v = file_video
        self.c = file_conf
        self.id = seq


class Assembler:
    def __init__(self, shards_in: list, shard_out: Shard):
        self.shards = shards_in
        for i in self.shards:
            if not isinstance(i, Shard):
                raise TypeError('shards_in must be a list of Shard')
            elif not i.v.endswith('.mp4'):
                raise TypeError('input file must be MP4 format')
        logging.info('# of input files: %d', len(self.shards))
        self.out = shard_out
        logging.info('Assembler is successfully initialized.')

    def run(self, show_progress=True):
        writer = None
        conf = {
            't': datetime.now().timestamp(),
            'handler': platform.node(),
            'input': [],
            'length': 0,
            'resolution': None,
            'font': {
                'size': None
            },
            'ciphers': '',
            'positions': [],
            'locations': []
        }
        problems = []
        for i in range(len(self.shards)):
            if show_progress:
                progress(i, len(self.shards))
            # Video
            video = imageio.get_reader(self.shards[i].v, 'ffmpeg')
            shape = video.get_data(0).shape
            if writer is None:
                writer = imageio.get_writer(self.out.v, fps=video.get_meta_data()['fps'])
            for j in range(video.count_frames()):
                try:
                    image = video.get_data(j).copy()
                except imageio.core.format.CannotReadFrameError:
                    problems.append('Could not read frame: {} => {}'.format(i, j))
                    image = imageio.core.util.Image(numpy.empty((shape[0], shape[1], 3), dtype=numpy.uint8))
                writer.append_data(numpy.array(Image.fromarray(image).convert("RGBA")))
            # Conf
            with io.open(self.shards[i].c, 'r', encoding='utf8') as f:
                c = '\n'.join([j for j in f.readlines()])
            c = json.loads(c)
            if conf['resolution'] is None:
                conf['resolution'] = c['resolution'].copy()
            elif conf['resolution'] != c['resolution']:
                problems.append('Resolution does not match: {} ({}) => {}'.format(i, c['resolution'], conf['resolution']))
            if conf['font']['size'] is None:
                conf['font']['size'] = c['font']['size']
            elif conf['font']['size'] != c['font']['size']:
                problems.append('Font size does not match: {} ({}) => {}'.format(i, c['font']['size'], conf['font']['size']))
            conf['input'].append(self.shards[i].__dict__)
            conf['ciphers'] += c['ciphers'][self.shards[i].id]
            conf['positions'] += [j + conf['length'] for j in c['positions']]
            conf['locations'] += c['locations']
            conf['length'] += c['length']
        if writer is not None:
            writer.close()
        with io.open(self.out.c, 'w', encoding='utf8') as f:
            json.dump(conf, f, indent=2, ensure_ascii=False)
        if show_progress:
            print()
        for i in problems:
            logging.error(i)
        logging.info('All done.')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output', type=str, default='output.mp4', help='output video file, default: output.mp4')
    parser.add_argument('-c', '--conf', type=str, default='output.json', help='output conf file, default: output.json')
    parser.add_argument('-i', type=str, help='sequence numbers of shards separated by comma, default: 0,0,...')
    parser.add_argument('--debug', action='store_true', help='show debug information')
    parser.add_argument('input', type=str, nargs='+', help='input files, must be MP4 format')
    args, _ = parser.parse_known_args()
    setup_log(logging.DEBUG if args.debug else logging.INFO)
    if 'i' not in args or args.i is None:
        args.i = ','.join(['0'] * len(args.input))
    Assembler(
        shards_in=[Shard(os.path.join(i, '{}.mp4'.format(int(j))), os.path.join(i, 'conf.json'), int(j)) for i, j in zip(args.input, args.i.split(','))],
        shard_out=Shard(args.output, args.conf)
    ).run()
