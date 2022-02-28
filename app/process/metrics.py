import math
from functools import lru_cache, partial
from typing import List, Tuple, Optional, Mapping

import numpy as np
import pandas as pd

from .exp_center import exp_center_file_in_directory
from .input import find_input_file_in_directory, get_input_values, _OUTPUT_NAMES
from .log import log_process
from .outformation import find_outformation_in_directory, load_outformation
from .simudata import simudata_file_in_directory
from .trans import ff, l2_distance, epsg4326_to_3857


# K formation_num
# K initial_reduce
# K final_total_size
# K dispersion
# K density
# K center_gap
# K dangerous_frequency
# K crash_probability
# K polarization
#   execute_time
# K airway_bias
# K loc_bias
# X adjust_ratio
# K stable_time

def get_formation_num(outformation_data: List[Tuple[float, int, int]]) -> float:
    num = 0
    last_t_time = 0
    for data in outformation_data:
        t_time, out_form, total_size = data
        num += (total_size - out_form)
        last_t_time = t_time

    return num / (int(last_t_time) * 10 * 5)


def get_initial_reduce_and_final_total_size(outformation_data: List[Tuple[float, int, int]]) -> Tuple[float, float]:
    first = 0
    for line in outformation_data:
        time, _, total_size = line
        if total_size < 20:
            first = time
            break

    _, _, final_total_size = outformation_data[-1]
    return first, final_total_size


def get_dispersion(simudata: pd.DataFrame, exp_data: pd.DataFrame,
                   outformation_data: List[Tuple[float, int, int]]) -> float:
    aim_list = []
    j = 0
    for i in range(exp_data.shape[0]):
        current_time = exp_data['time'][i]
        while abs(outformation_data[j][0] - current_time) >= 1e-4 and \
                outformation_data[j][0] <= current_time:
            j += 1

        if abs(outformation_data[j][0] - current_time) >= 1e-4:
            continue

        _, outformation_num, cur_total_size = outformation_data[j]
        if (cur_total_size - outformation_num) >= 0.95 * cur_total_size:
            distance_list = []
            center = [exp_data['r_x'][i], exp_data['r_y'][i], exp_data['r_h'][i]]
            tt = ff(exp_data['time'][i])
            tmp_sim = simudata[(simudata['time'] < tt + 0.001) & (simudata['time'] > tt - 0.001)].reset_index(
                drop=True)
            if tmp_sim.shape[0] > 0:
                for j in range(tmp_sim.shape[0]):
                    distance_list.append(
                        l2_distance(center, [tmp_sim['x'][j], tmp_sim['y'][j], tmp_sim['height'][j]]))
                distance_list.sort()
                distance_list = distance_list[0:int(0.9 * len(distance_list))]
                aim_list.append(np.std(np.array(distance_list)) / np.mean(np.array(distance_list)))
        else:
            continue

    # noinspection PyTypeChecker
    return -1 if len(aim_list) == 0 else np.mean(np.array(aim_list))


def get_density(simudata: pd.DataFrame, exp_data: pd.DataFrame) -> float:
    density = 0
    for i in range(exp_data.shape[0]):
        center = [exp_data['r_x'][i], exp_data['r_y'][i], exp_data['r_h'][i]]
        tt = ff(exp_data['time'][i])
        tmp_sim = simudata[(simudata['time'] < tt + 0.001) & (simudata['time'] > tt - 0.001)].reset_index(drop=True)
        distances = []
        for j in range(tmp_sim.shape[0]):
            x = tmp_sim['x'][j]
            y = tmp_sim['y'][j]
            obj = [x, y, tmp_sim['height'][j]]
            distances.append(l2_distance(center, obj))
        distances.sort()
        bias = int(len(distances) * 0.9)

        r_value = distances[bias - 1]
        res = 3 * bias / (4 * math.pi * (r_value ** 3))
        density += res

    return density / (exp_data.shape[0]) * (100 ** 3)


def get_center_gap(simudata: pd.DataFrame, exp_data: pd.DataFrame) -> float:
    center_avg_gap = 0
    for i in range(exp_data.shape[0]):
        tt = ff(exp_data['time'][i])
        tmp_sim = simudata[(simudata['time'] < tt + 0.001) & (simudata['time'] > tt - 0.001)].reset_index(drop=True)
        dist = 0
        obj = [0, 0, 0]
        for j in range(tmp_sim.shape[0]):
            x = tmp_sim['x'][j]
            y = tmp_sim['y'][j]
            obj[0] += x
            obj[1] += y
            obj[2] += tmp_sim['height'][j]
        center = [obj[0] / tmp_sim.shape[0], obj[1] / tmp_sim.shape[0], obj[2] / tmp_sim.shape[0]]
        distances = []
        for j in range(tmp_sim.shape[0]):
            x = tmp_sim['x'][j]
            y = tmp_sim['y'][j]
            obj2 = [x, y, tmp_sim['height'][j]]
            distances.append(l2_distance(center, obj2))
        distances.sort()
        distances = distances[0:int(len(distances) * 0.9)]
        for d in distances:
            dist += d
        center_avg_gap += dist / len(distances)

    return center_avg_gap / exp_data.shape[0]


def get_danger_frequency(outformation_data: List[Tuple[float, int, int]]) -> float:
    init_num, crash_num = 20, 0
    for item in outformation_data:
        _, _, cur_total_size = item
        if cur_total_size < init_num:
            crash_num += (init_num - cur_total_size) * (init_num - cur_total_size - 1)
            init_num = cur_total_size

    return crash_num / 20


def get_crash_probability(outformation_data: List[Tuple[float, int, int]]) -> float:
    init_num, crash_num = 20, 0
    for item in outformation_data:
        _, _, cur_total_size = item
        if cur_total_size < init_num:
            crash_num += init_num - cur_total_size
            init_num = cur_total_size

    return crash_num / 20


def get_polarization(simudata: pd.DataFrame, exp_data: pd.DataFrame,
                     outformation_data: List[Tuple[float, int, int]]) -> float:
    aim_list = []
    j = 0
    for i in range(exp_data.shape[0]):
        if i == 0:
            continue

        current_time = exp_data['time'][i]
        while abs(outformation_data[j][0] - current_time) >= 1e-4 and \
                outformation_data[j][0] <= current_time:
            j += 1

        if abs(outformation_data[j][0] - current_time) >= 1e-4:
            continue

        _, outformation_num, cur_total_size = outformation_data[j]
        if (cur_total_size - outformation_num) >= 0.95 * cur_total_size:
            ans = [0, 0, 0]
            center = [exp_data['r_x'][i], exp_data['r_y'][i], exp_data['r_h'][i]]
            tt = ff(exp_data['time'][i])
            tmp_sim = simudata[(simudata['time'] < tt + 0.001) & (simudata['time'] > tt - 0.001)] \
                .reset_index(drop=True)

            pre_center = [exp_data['r_x'][i - 1], exp_data['r_y'][i - 1], exp_data['r_h'][i - 1]]
            pre_tt = ff(exp_data['time'][i - 1])
            pre_tmp_sim = simudata[
                (simudata['time'] < pre_tt + 0.001) & (simudata['time'] > pre_tt - 0.001)] \
                .reset_index(drop=True)

            center_dir = [center[0] - pre_center[0], center[1] - pre_center[1], center[2] - pre_center[2]]

            if tmp_sim.shape[0] > 0:
                for j in range(tmp_sim.shape[0]):
                    for k in range(pre_tmp_sim.shape[0]):
                        if pre_tmp_sim['id'][k] == tmp_sim['id'][j]:
                            item_dir = [tmp_sim['x'][j] - pre_tmp_sim['x'][k],
                                        tmp_sim['y'][j] - pre_tmp_sim['y'][k],
                                        tmp_sim['height'][j] - pre_tmp_sim['height'][k]]

                            ans[0] += item_dir[0] - center_dir[0]
                            ans[1] += item_dir[1] - center_dir[1]
                            ans[2] += item_dir[2] - center_dir[2]
                            break
                aim_list.append(math.sqrt(np.sum(np.array(ans) ** 2)))

    return -1 if len(aim_list) == 0 else np.mean(np.array(aim_list))


@lru_cache()
def _prepare_airway_bias():
    p1 = [13.147670731635747, 43.65982853870639, 2000.0]
    p2 = [13.186799589095362, 43.78649351263097, 2000.0]
    p1[0], p1[1] = epsg4326_to_3857(p1[1], p1[0])
    p2[0], p2[1] = epsg4326_to_3857(p2[1], p2[0])
    return p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2]


def get_airway_bias(simudata: pd.DataFrame, exp_data: pd.DataFrame) -> float:
    way_dir = _prepare_airway_bias()
    aim_list = []
    for i in range(exp_data.shape[0]):
        if i == 0:
            continue

        center = [exp_data['r_x'][i], exp_data['r_y'][i], exp_data['r_h'][i]]
        pre_center = [exp_data['r_x'][i - 1], exp_data['r_y'][i - 1], exp_data['r_h'][i - 1]]
        center_dir = [center[0] - pre_center[0], center[1] - pre_center[1], center[2] - pre_center[2]]

        ans = math.acos(
            (way_dir[0] * center_dir[0] + way_dir[1] * center_dir[1] + way_dir[2] * center_dir[2]) /
            (math.sqrt(np.sum(np.array(way_dir) ** 2)) * math.sqrt(np.sum(np.array(center_dir) ** 2)))
        )
        aim_list.append(ans)

    # noinspection PyTypeChecker
    return np.mean(np.array(aim_list))


def get_loc_bias(simudata: pd.DataFrame, exp_data: pd.DataFrame) -> float:
    p2 = [13.186799589095362, 43.78649351263097, 2000.0]
    p2[0], p2[1] = epsg4326_to_3857(p2[1], p2[0])
    aim = float('inf')
    for i in range(exp_data.shape[0]):
        center = [exp_data['r_x'][i], exp_data['r_y'][i], exp_data['r_h'][i]]
        cur_ans = math.sqrt((center[0] - p2[0]) ** 2 + (center[1] - p2[1]) ** 2 + (center[2] - p2[2]) ** 2)
        if cur_ans < aim:
            aim = cur_ans

    return aim


def get_execute_time(inputs: Mapping[str, object], outformation_data: List[Tuple[float, int, int]]):
    control_time = (inputs['time'], inputs['time.1'])
    execute_time = 0
    c_index = 0
    cur_time = control_time[c_index]

    for time_, out_form, total_size in outformation_data:
        if abs(time_ - outformation_data[-1][0]) < 1e-6:
            execute_time += time_ - cur_time
            break
        if c_index + 1 < len(control_time):
            if time_ > control_time[c_index + 1]:
                execute_time += time_ - cur_time
                cur_time = control_time[c_index + 1]
                c_index += 1

        if (total_size - out_form) >= int(total_size * 0.95):
            if time_ > cur_time:
                execute_time += time_ - cur_time
                if c_index + 1 == len(control_time):
                    break
                else:
                    cur_time = control_time[c_index + 1]
                    c_index += 1

    return execute_time


def get_stable_time(outformation_data: List[Tuple[float, int, int]]) -> float:
    num = 0
    for data in outformation_data:
        _, out_form, total_size = data
        if (total_size - out_form) >= int(total_size * 0.95):
            num += 1
    return ff(num / len(outformation_data) * 100)


_ALL_NAME_LIST = [
    # inputs
    *_OUTPUT_NAMES,

    # metrics
    'formation_num',
    'initial_reduce',
    'final_total_size',
    'dispersion',
    'density',
    'center_gap',
    'dangerous_frequency',
    'crash_probability',
    'polarization',
    'execute_time',
    'airway_bias',
    'loc_bias',
    # 'adjust_ratio',
    'stable_time',
]


def get_all_metrics(directory: str, force: bool = False,
                    shown_names: Optional[List[str]] = None):
    shown_names = shown_names or _ALL_NAME_LIST

    input_file = find_input_file_in_directory(directory)
    simudata_file = simudata_file_in_directory(directory)
    exp_center_file = exp_center_file_in_directory(directory)
    outformation_file = find_outformation_in_directory(directory)
    log_process(directory, force)

    input_values = get_input_values(input_file)
    simudata = pd.read_csv(simudata_file)
    exp_data = pd.read_csv(exp_center_file)
    outformation_data = load_outformation(outformation_file)

    irft = None

    def _get_irft() -> Tuple[float, float]:
        nonlocal irft
        if irft is None:
            irft = get_initial_reduce_and_final_total_size(outformation_data)

        return irft

    data_map = {
        'formation_num': lambda: get_formation_num(outformation_data),
        'initial_reduce': lambda: _get_irft()[0],
        'final_total_size': lambda: _get_irft()[1],
        'dispersion': lambda: get_dispersion(simudata, exp_data, outformation_data),
        'density': lambda: get_density(simudata, exp_data),
        'center_gap': lambda: get_center_gap(simudata, exp_data),
        'dangerous_frequency': lambda: get_danger_frequency(outformation_data),
        'crash_probability': lambda: get_crash_probability(outformation_data),
        'polarization': lambda: get_polarization(simudata, exp_data, outformation_data),
        'execute_time': lambda: get_execute_time(input_values, outformation_data),
        'airway_bias': lambda: get_airway_bias(simudata, exp_data),
        'loc_bias': lambda: get_loc_bias(simudata, exp_data),
        # 'adjust_ratio': lambda: -1,
        'stable_time': lambda: get_stable_time(outformation_data),
        **{name: partial(input_values.__getitem__, name) for name in _OUTPUT_NAMES},
    }
    return {name: data_map[name]() for name in shown_names}
