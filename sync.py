#! /usr/bin/python3

import argparse
import subprocess
from pathlib import Path
import logging
import time


logger = logging.getLogger(__name__)


class Chip(object):
    def __init__(self, path):
        self.path = Path(path)
        self.sync_done_flag = self.path / '.sync.done'

    def is_seq_finished(self):
        """determine whether sequence is finished or dead?"""
        flag1 = self.path / 'RTAComplete.txt'
        flag2 = self.path / 'RunCompletionStatus.xml'
        runinfo = self.path / 'RunInfo.xml'

        return flag1.exists() or flag2.exists() or (runinfo.exists() and time.time() - runinfo.stat().st_mtime > 24 * 3600 * 7)

    def is_chip_dir(self):
        """determine whether dir is a valid sequence run dir"""
        recipe_dir = self.path / 'Recipe'
        config_dir = self.path / 'Config'
        runinfo_xml = self.path / 'RunInfo.xml'
        return recipe_dir.exists() or config_dir.exists() or runinfo_xml.exists()

    def sync(self, remote, port=875, timeout=7200, final=False, extra_args=''):
        """do sync using rsync
            if sequence finished, create a flag file
        """

        if self.is_seq_finished() and final is not True:
            self.sync(remote, port=port, timeout=timeout, final=True, extra_args=extra_args)
            return
        logger.info(f'sync {self.path}...')
        cmd = f"rsync -av --partial --exclude 'Thumbnail_Images' --exclude '*.tmp.*' --timeout 30 --port {port} {extra_args} {self.path} {remote}"
        logger.debug(cmd)

        # run rsync
        proc = subprocess.Popen(cmd, shell=True, encoding='utf-8',
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        try:
            stdout, _ = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, _ = proc.communicate()

        if proc.returncode != 0:
            logger.warning(f"sync {self.path} has return code: {proc.returncode}")

        for line in stdout.split('\n'):
            logger.debug(line)

        if final and proc.returncode == 0:
            self.sync_done_flag.touch()
            logger.info(f'sync {self.path} finished')


def parse_args():
    parser = argparse.ArgumentParser(prog='sync')
    parser.add_argument('base_dir', help='Base dir of chip run data')
    parser.add_argument('remote_path', help='Remote path which should be a valid rsync dst expression string')
    parser.add_argument('--port', help='rsync port', type=int, default=875)
    parser.add_argument('--extra-args', help='extra rsync args to pass', default='')
    parser.add_argument('--timeout', help='rsync command timeout', type=int, default=7200)
    parser.add_argument('--make-cache', action='store_true', help='make cache for all exists chip data and exit')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='set log level to debug')
    args = parser.parse_args()

    logger_config = {'level': 'INFO',
                     'format': '{asctime} - {levelname} - {message}',
                     'style': '{'}
    if args.verbose:
        logger_config['level'] = 'DEBUG'

    logging.basicConfig(**logger_config)
    return args


def make_cache(base_dir):
    for chip_dir in Path(base_dir).glob('*'):
        if not chip_dir.is_dir():
            continue
        chip = Chip(chip_dir)
        if not chip.is_chip_dir():
            continue
        chip.sync_done_flag.touch()


def sync_all(base_dir, remote, **kwargs):
    for chip_dir in Path(base_dir).glob('*'):
        if not chip_dir.is_dir():
            continue
        chip = Chip(chip_dir)
        if not chip.is_chip_dir():
            continue
        if chip.sync_done_flag.exists():
            continue
        try:
            chip.sync(remote, **kwargs)
        except Exception as e:
            logger.error(e)
            continue


def main():
    args = parse_args()
    if args.make_cache:
        make_cache(args.base_dir)
        raise SystemExit
    sync_all(args.base_dir, args.remote_path,
             port=args.port, timeout=args.timeout, extra_args=args.extra_args.strip('"\''))


if __name__ == '__main__':
    main()
