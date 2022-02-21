import os
from operator import itemgetter

import numpy as np
import pandas as pd

from .exp_center import exp_center_process, find_expdata_in_directory
from .simudata import simudata_process, find_simudata_in_directory


def log_process(directory: str, force: bool = False):
    simudata_file = os.path.join(directory, 'simudata.csv')
    exp_center_file = os.path.join(directory, 'exp_center.csv')
    if not force and os.path.exists(simudata_file) and os.path.exists(exp_center_file):
        return

    simudata_process(
        os.path.join(directory, find_simudata_in_directory(directory)),
        simudata_file, force=force,
    )
    exp_center_process(
        os.path.join(directory, find_expdata_in_directory(directory)),
        exp_center_file, force=force,
    )

    simudata_pd = pd.read_csv(simudata_file)
    exp_center_pd = pd.read_csv(exp_center_file)

    records = {}
    for lineno, row in simudata_pd.iterrows():
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
    for lineno, row in exp_center_pd.iterrows():
        time_ = row['time']
        rx, ry, rh = means.get(time_, (-1, -1, -1))
        xs.append(rx)
        ys.append(ry)
        hs.append(rh)

    exp_center_pd['r_x'] = xs
    exp_center_pd['r_y'] = ys
    exp_center_pd['r_h'] = hs
    exp_center_pd.to_csv(exp_center_file)
