import csv
import os
from typing import Mapping

_INPUT_NAMES_AND_TYPES = [
    ("initial_number", int),
    ("loc_offset", int),
    ("loc_err", float),
    ("angle_err", int),
    ("perception", float),
    ("lost_possibility", float),
    ("control_num", int),
    ("time", int),
    ("gap", int),
    ("type", int),
    ("R1", int),
    ("R2", int),
    ("R3", int),
    ("time.1", int),
    ("gap.1", int),
    ("type.1", int),
    ("R1.1", int),
    ("R2.1", int),
    ("R3.1", int),
]


def find_input_file_in_directory(directory: str):
    return os.path.join(directory, 'input.csv')


def get_input_values_from_directory(directory: str) -> Mapping[str, object]:
    return get_input_values(find_input_file_in_directory(directory))


def get_input_values(inp_file: str) -> Mapping[str, object]:
    with open(inp_file, 'r') as f:
        rd = csv.reader(f)
        values = next(rd)

        return {
            name: type_(val)
            for (name, type_), val in zip(_INPUT_NAMES_AND_TYPES, values)
        }


_OUTPUT_NAMES = [
    "loc_offset",
    "perception",
    "lost_possibility",
    "time",
    "gap",
    "type",
    "R1",
    "R2",
    "R3",
    "time.1",
    "gap.1",
    "type.1",
    "R1.1",
    "R2.1",
    "R3.1",
]
