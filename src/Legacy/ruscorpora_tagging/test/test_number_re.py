import sys

sys.path.append('..')

from lemmer import NUMBER_RE

def test_number_re():
    for number_positive in [
        '1',
        '100000000000.9',
        '999999999999999999',
        '4.568293864',
        '0.1',
        '0.0000000000000051',
        '-3,14159',
        '1,5'
    ]:
        assert NUMBER_RE.match(number_positive) is not None

    for number_negative in [
        '.',
        '..',
        '1..15',
        '.19',
        ',',
        '1,,10923'
        '-',
        '-11-1--1.13981'
        '1abc2'
        '.-987',
        '0-2+4g7',
        '+'
    ]:
        assert NUMBER_RE.match(number_negative) is None