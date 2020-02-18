from asyncio import Queue, sleep
from collections import namedtuple
from contextlib import ExitStack
from inspect import iscoroutinefunction
from logging import getLogger
from os import stat, SEEK_END
from pathlib import Path
from time import monotonic as monotime


logger = getLogger(__name__)


LogLine = namedtuple('LogLine', 'file line')


async def tail_files(get_paths, process_line, sleep_interval=1):
    assert callable(get_paths), 'get_paths must be function'
    assert iscoroutinefunction(process_line), 'process_line must be coroutine function'
    open_files = {} # path -> FileReader
    with ExitStack() as stack:
        paths = get_paths()
        logger.debug('Paths: %r', paths)
        for p in paths:
            logger.debug('Opening %s', p)
            try:
                open_files[p] = stack.enter_context(FileReader(p))
            except Exception as e:
                logger.warning('Failed to open file %s: %r', p, e)
        if not open_files:
            raise Exception('No file opened')
        while True:
            for p, fr in open_files.items():
                for line in fr.read_lines():
                    logger.debug('Line: %r', line)
                    await process_line(p, line)
            await sleep(sleep_interval)


def _close_file(f):
    '''
    Called from FileReader.__exit__()
    '''
    try:
        f.close()
    except Exception as e:
        logger.exception('Failed to close file %r: %r', f, e)


class FileReader:

    expire_interval_s = 60

    def __init__(self, path):
        self._path = Path(path)
        self._current_file = None
        self._current_dev_inode = None
        self._rotated_files = [] # [( file, expire_monotime )]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._current_file:
            _close_file(self._current_file)
        self._current_file = None
        for f, expire_mt in self._rotated_files:
            _close_file(f.close())
        self._rotated_files = None

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
        logger.debug(
            'Opened file %s fd %s dev %s inode %s position %s',
            self._path, f.fileno(), dev_inode[0], dev_inode[1], f.tell())
