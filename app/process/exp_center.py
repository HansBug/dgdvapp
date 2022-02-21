import glob
import os

import pandas as pd

from app.proto import MpsProtoData


def find_expdata_in_directory(directory: str):
    matchings = glob.glob1(directory, 'expdata_*')
    if matchings:
        return matchings[0]
    else:
        raise FileNotFoundError(f'No expdata file found in {repr(directory)}.')


def exp_center_process_in_directory(directory: str, force: bool = False):
    return exp_center_process(
        os.path.join(directory, find_expdata_in_directory(directory)),
        os.path.join(directory, 'exp_center.csv'),
        force=force,
    )


def exp_center_process(src_file: str, dst_file: str, force: bool = False):
    mpd = MpsProtoData()
    if not force and os.path.exists(dst_file):
        return

    with open(src_file, 'rb') as f:
        con = f.read()
        index = 0
        data = {
            'id': [],
            'type': [],
            'time': [],
            'lng': [],
            'lat': [],
            'height': []
        }
        while index < len(con):
            type_ = con[index]
            cur = index + 1
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
            if type_ == 1:
                index = cur + 1 + final_length
                continue
            else:
                mpd.ParseFromString(content)
                if mpd.id == 20000:
                    data['id'].append(mpd.id)
                    data['type'].append(mpd.type)
                    data['time'].append(mpd.time)
                    data['lng'].append(mpd.lng)
                    data['lat'].append(mpd.lat)
                    data['height'].append(mpd.h)
            index = cur + 1 + final_length
        df = pd.DataFrame(data)
        df.to_csv(dst_file)
