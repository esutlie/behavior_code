"""
This script is designed to convert my (Elissa Sutlief's) behavior files into the new standard format the shuler lab
will use to make their behavior files easy to convert to the nwb format. Others should modify this script to convert
their own data files into the standard lab format, then use the nwb conversion script designed by catalyst neuro to
make their files compatible with dandy.

The standard format consists of a csv file with the first line containing column headers and every other line containing
event data. This is paired with meta data json file.

The folder structure of the original data :
data\
  ES031\
    data_YYYY-MM-DD_HH-mm-ss.txt
    data_YYYY-MM-DD_HH-mm-ss.txt
    data_YYYY-MM-DD_HH-mm-ss.txt
  ES032\
    data_YYYY-MM-DD_HH-mm-ss.txt
    data_YYYY-MM-DD_HH-mm-ss.txt
    data_YYYY-MM-DD_HH-mm-ss.txt

The folder structure of the converted data:
data_conversion\
  conversion.py                  --> This script. Edit and run to convert data to standard format
  paths.py                       --> A script with the data paths that should be inside the same folder as this one
data_standard\
  mouse_data.json                --> meta data for each mouse, to be added to each data file
  task_data.json                 --> meta data for each task, to be added to each data file
  ES031\
    ES031_YYYY-MM-DD_HH-mm-ss\
      data.csv
      meta_data.json
    ES031_YYYY-MM-DD_HH-mm-ss\
      data.csv
      meta_data.json
    ES031_YYYY-MM-DD_HH-mm-ss\
      data.csv
      meta_data.json
  ES032\
    ES032_YYYY-MM-DD_HH-mm-ss\
      data.csv
      meta_data.json
    ES032_YYYY-MM-DD_HH-mm-ss\
      data.csv
      meta_data.json
    ES032_YYYY-MM-DD_HH-mm-ss\
      data.csv
      meta_data.json

"""

from paths import get_paths
import os
from os import walk
import pandas as pd
import numpy as np
from csv import reader
import json


def save_json(path, var):
    json_object = json.dumps(var, indent=4)
    with open(path, "w") as outfile:
        outfile.write(json_object)


def load_json(path):
    with open(path, 'r') as openfile:
        var = json.load(openfile)
    return var


def convert_data(regen=False):
    paths = get_paths()
    mouse_data = load_json(os.path.join(paths['converted_data'], 'mouse_data.json'))
    task_data = load_json(os.path.join(paths['converted_data'], 'task_data.json'))
    for root, dirs, filenames in walk(paths['original_data']):
        if len(dirs) == 0 and os.path.basename(root)[:2] == 'ES':
            mouse = os.path.basename(root)
            for f in filenames:
                if f == 'desktop.ini':
                    continue
                dest = os.path.join(paths['converted_data'], mouse, f'{mouse}_{f[5:24]}')
                if not regen and os.path.exists(dest):
                    continue
                path = os.path.join(root, f)
                data = pd.read_csv(path, na_values=['None'], skiprows=3)

                with open(path, 'r') as file:
                    r = reader(file)
                    info_keys = next(r)
                    info_values = next(r)
                starts = np.where([True if s[0] == '{' else False for s in info_values])[0][::-1]
                ends = np.where([True if s[-1] == '}' else False for s in info_values])[0][::-1]
                for i in range(len(starts)):
                    info_values = info_values[:starts[i]] + [
                        ",".join(info_values[starts[i]:ends[i] + 1])] + info_values[
                                                                        ends[i] + 1:]
                info = dict(zip(info_keys, info_values))
                if 'port2duration' in info.keys():
                    info['port2_duration'] = info['port2duration']

                mouse_info = mouse_data[mouse]
                task_info = task_data[info['task']]
                session_meta_data = {
                    'session': {
                        'date': info['date'],
                        'time': info['time'],
                        'experimenter': 'Elissa Sutlief',
                        'box': 0 if 'box' not in info.keys() else info['box']
                    },
                    'mouse': mouse_info,
                    'task': task_info
                }
                for p in [1, 2]:
                    if f'port{p}_info' in info.keys():
                        port_dict = eval(info[f'port{p}_info'].replace('<', '\'').replace('>', '\''))
                        if port_dict['distribution'][:8] == 'function':
                            port_dict['distribution'] = 'exp_decreasing'
                        session_meta_data['task'][f'port{p}'] = port_dict
                    else:
                        session_meta_data['task'][f'port{p}'] = {
                            'distribution': info[f'port{p}_distribution'],
                            'cumulative': info[f'port{p}_cumulative'],
                            'peak': info[f'port{p}_peak'],
                            'duration': info[f'port{p}_duration'],
                            'port_num': p,
                        }

                if not os.path.exists(dest):
                    os.makedirs(dest)
                save_json(os.path.join(dest, 'meta_data.json'), session_meta_data)
                data.to_csv(os.path.join(dest, 'data.csv'))


if __name__ == '__main__':
    convert_data()
