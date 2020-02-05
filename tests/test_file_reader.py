from nginx_log_monitor.file_reader import FileReader


def test_file_reader_empty_file(temp_dir):
    log_path = temp_dir / 'sample.log'
    log_path.write_text('')
    with FileReader(log_path) as fr:
        assert list(fr.read_lines()) == []


def test_file_reader_small_file(temp_dir):
    log_path = temp_dir / 'sample.log'
    log_path.write_text('before1\nbefore2\n')
    with FileReader(log_path) as fr:
        assert list(fr.read_lines()) == []
        with log_path.open(mode='a') as f:
            f.write('after1\nafter2\n')
        assert log_path.read_text() == 'before1\nbefore2\nafter1\nafter2\n'
        assert list(fr.read_lines()) == [b'after1\n', b'after2\n']


def test_file_reader_rotate_file(temp_dir):
    log_path = temp_dir / 'sample.log'
    log_path.write_text('before1\nbefore2\n')
    with FileReader(log_path) as fr:
        assert list(fr.read_lines()) == []
        with log_path.open(mode='a') as f:
            f.write('after1\nafter2\n')
        assert list(fr.read_lines()) == [b'after1\n', b'after2\n']
        log_path.unlink()
        log_path.write_text('rotated1\nrotated2\n')
        assert list(fr.read_lines()) == [b'rotated1\n', b'rotated2\n']

