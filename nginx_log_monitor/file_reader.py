from asyncio import Queue, get_running_loop, sleep
from collections import namedtuple
from inspect import iscoroutinefunction
from logging import getLogger
from os import stat, SEEK_END
from pathlib import Path
from time import monotonic as monotime


logger = getLogger(__name__)


LogLine = namedtuple('LogLine', 'file line')


async def tail_files(queue, get_paths, sleep_interval=1):
    assert isinstance(queue, Queue)
    assert iscoroutinefunction(get_paths)
    open_files = {} # path -> FileReader
    paths = await get_paths()
    for p in paths:
        open_files[p] = FileReader(p)
    while True:
        for p, fr in open_files.items():
            for line in fr.read_lines():
                await queue.put(LogLine(file=p, line=line))
        await sleep(sleep_interval)


class FileReader:

    expire_interval_s = 60

    def __init__(self, path):
        self._path = Path(path)
        self._current_file = None
        self._current_dev_inode = None
        self._rotated_files = [] # [( file, expire_monotime )]

    def read_lines(self):
        # check if current file is rotated
        if self._current_file is not None and self._looks_rotated():
            self._open()
            assert self._current_file

        # read from rotated files, if there is anything new
        new_rotated_files = []
        for f, expire_mt in self._rotated_files:
            while True:
                line = f.readline()
                logger.debug('Read from rotated file %s: %r', f.fileno(), line)
                if not line:
                    break
                yield line
                expire_mt = monotime() + self.expire_interval_s
            if expire_mt > monotime():
                new_rotated_files.append((f, expire_mt))
            else:
                logger.debug('Closing file %s', f.fileno())
                f.close()
            del f
        self._rotated_files = new_rotated_files

        # read from current file
        if self._current_file is None:
            self._open(seek_end=True)
        f = self._current_file
        while True:
            line = f.readline()
            logger.debug('Read from current file %s: %r', f.fileno(), line)
            if not line:
                break
            yield line

    def _looks_rotated(self):
        st = self._path.stat()
        return (st.st_dev, st.st_ino) != self._current_dev_inode

    def _open(self, seek_end=False):
        f = self._path.open(mode='rb')
        st = stat(f.fileno())
        dev_inode = (st.st_dev, st.st_ino)
        if dev_inode == self._current_dev_inode:
            # this would we weird, but could maybe happen;
            # we do not want to have the file opened twice
            f.close()
            return
        if seek_end:
            f.seek(0, SEEK_END)
        if self._current_file is not None:
            self._rotated_files.append((self._current_file, monotime() + self.expire_interval_s))
        self._current_file = f
        self._current_dev_inode = dev_inode
        logger.debug('Opened file %s fd %s dev_inode %s', self._path, f.fileno(), dev_inode)