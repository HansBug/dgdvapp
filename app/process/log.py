import os
from operator import itemgetter
from typing import Tuple, Iterator

import numpy as np
import pandas as pd

from .exp_center import find_expdata_in_directory, exp_center_file_in_directory, exp_center_trans
from .simudata import find_simudata_in_directory, simudata_file_in_directory, simudata_trans


def is_log_directory(directory: str) -> bool:
    try:
        find_simudata_in_directory(directory)
        find_expdata_in_directory(directory)
    except FileNotFoundError:
        return False
    else:
        return True


def walk_log_directories(root: str) -> Iterator[str]:
    for directory, _, _ in os.walk(root, followlinks=True):
        if is_log_directory(directory):
            yield directory


def log_trans(directory: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    simudata_df = simudata_trans(find_simudata_in_directory(directory))
    exp_center_df = exp_center_trans(find_expdata_in_directory(directory))

    records = {}
    for lineno, row in simudata_df.iterrows():
        time_ = row['time']
        x, y = row['x'], row['y']
        height = row['height']
        if time_ not in records:
            records[time_] = []
        records[time_].append((x, y, height))

    means = {}
    for time_, items in records.items():
        x_array = np.asarray(list(map(itemgetter(0), items)))
        y_array = np.asarray(list(map(itemgetter(1), items)))
        h_array = np.asarray(list(map(itemgetter(2), items)))
        means[time_] = (np.mean(x_array), np.mean(y_array), np.mean(h_array))

    xs, ys, hs = [], [], []
    for lineno, row in exp_center_df.iterrows():
        time_ = row['time']
        rx, ry, rh = means.get(time_, (-1, -1, -1))
        xs.append(rx)
        ys.append(ry)
        hs.append(rh)

    exp_center_df['r_x'] = xs
    exp_center_df['r_y'] = ys
    exp_center_df['r_h'] = hs

    return simudata_df, exp_center_df


def log_process(directory: str, force: bool = False):
    simudata_file = simudata_file_in_directory(directory)
    exp_center_file = exp_center_file_in_directory(directory)
    if not force and os.path.exists(simudata_file) and os.path.exists(exp_center_file):
        return

    simudata_pd, exp_center_pd = log_trans(directory)
    simudata_pd.to_csv(simudata_file)
    exp_center_pd.to_csv(exp_center_file)
