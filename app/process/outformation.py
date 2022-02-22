import codecs
import glob
import os
import re
from typing import List, Tuple

_OUTFORMATION_LINE_PATTERN = re.compile(r'^\s*time:([0-9\\.]+)\s+outFormation:([0-9]+)\s+totalsize:([0-9]+)\s*$')


def parse_outformation_line(line: str) -> Tuple[float, int, int]:
    match = _OUTFORMATION_LINE_PATTERN.fullmatch(line)
    return float(match[1]), int(match[2]), int(match[3])


def find_outformation_in_directory(directory: str):
    matchings = glob.glob1(directory, 'outformation_*')
    if matchings:
        return os.path.join(directory, matchings[0])
    else:
        raise FileNotFoundError(f'No outformation file found in {repr(directory)}.')


def load_outformation(outformation_file: str) -> List[Tuple[float, int, int]]:
    with codecs.open(outformation_file, 'r') as f:
        return [parse_outformation_line(line.strip()) for line in f.readlines()]


def load_outformation_in_directory(directory: str) -> List[Tuple[float, int, int]]:
    return load_outformation(find_outformation_in_directory(directory))
