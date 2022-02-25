import glob
import os

import pandas as pd

from app.proto import MpsReceiveMsg


def find_msgdata_in_directory(directory: str):
    matchings = glob.glob1(directory, 'msgData_*')
    if matchings:
        return os.path.join(directory, matchings[0])
    else:
        raise FileNotFoundError(f'No msgdata file found in {repr(directory)}.')


def msgdata_trans(src_file: str) -> pd.DataFrame:
    mpa = MpsReceiveMsg()
    data = {
        'time': [],
        'receive_id': [],
        'send_id': [],
        'type': [],
    }

    with open(src_file, 'rb') as f:
        con = f.read()
        index = 1
        while index < len(con):
            curindex = index
            lbytes = []
            while con[curindex] & 0x80:
                lbytes.append(con[curindex] & ~0x80)
                curindex += 1

            if len(lbytes) < 5:
                lbytes.append(con[curindex])

            final_length = 0x00
            for length in lbytes[::-1]:
                final_length = (final_length << 7) | length
            content = con[curindex + 1:curindex + 1 + final_length]
            mpa.ParseFromString(content)

            for msg in mpa.msginfo:
                data['time'].append(mpa.time)
                data['receive_id'].append(mpa.receiveID)
                data['send_id'].append(msg.sendID)
                data['type'].append(msg.msgtype)

            index = curindex + 1 + final_length + 1

        return pd.DataFrame(data)
