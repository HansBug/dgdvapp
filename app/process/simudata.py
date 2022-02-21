import glob
import os

import pandas as pd

from app.proto import MpsProtoAircraft


def find_simudata_in_directory(directory: str):
    matchings = glob.glob1(directory, 'simudata_*')
    if matchings:
        return matchings[0]
    else:
        raise FileNotFoundError(f'No simudata file found in {repr(directory)}.')


def simudata_process_in_directory(directory: str, force: bool = False):
    return simudata_process(
        os.path.join(directory, find_simudata_in_directory(directory)),
        os.path.join(directory, 'simudata.csv'),
        force=force,
    )


def simudata_process(src_file: str, dst_file: str, force: bool = False):
    mpa = MpsProtoAircraft()
    if not force and os.path.exists(dst_file):
        return

    with open(src_file, 'rb') as f:
        con = f.read()
        index = 1
        data = {
            'id': [],
            'type': [],
            'time': [],
            'lng': [],
            'lat': [],
            'height': [],
            'roll': [],
            'pitch': [],
            'yaw': [],
            'speed': []
        }
        while index < len(con):
            cur = index
            lengths = []
            while con[cur] >= 128:
                lengths.append(con[cur] - 128)
                cur += 1
            if len(lengths) < 5:
                lengths.append(con[cur])
            lengths.reverse()

            final_length = 0
            for length in lengths:
                final_length = final_length * 128 + length
            content = con[cur + 1:cur + 1 + final_length]
            mpa.ParseFromString(content)

            if mpa.head.type != 7030102:
                data['id'].append(mpa.head.id)
                data['type'].append(mpa.head.type)
                data['time'].append(mpa.head.time)
                data['lng'].append(mpa.head.lng)
                data['lat'].append(mpa.head.lat)
                data['height'].append(mpa.head.h)
                data['roll'].append(mpa.roll)
                data['pitch'].append(mpa.pitch)
                data['yaw'].append(mpa.yaw)
                data['speed'].append(mpa.speed)
            index = cur + 1 + final_length + 1

        df = pd.DataFrame(data)
        df.to_csv(dst_file)
