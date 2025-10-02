import json
import os.path
import csv
from paths import get_paths

def save_json(path, var):
    json_object = json.dumps(var, indent=4)
    with open(path, "w") as outfile:
        outfile.write(json_object)


def load_json(path):
    with open(path, 'r') as openfile:
        var = json.load(openfile)
    return var


def save_paths():
    paths = {}


def edit_mouse_data():
    path = os.path.join(os.getcwd(), '../data_standard/mouse_data.json')
    mouse_data = load_json(path)
    for key in mouse_data.keys():
        mouse_data[key]['species'] = 'mouse'
    save_json(path, mouse_data)


def save_task_data():
    task_data = {
        'multi_reward': {
            'name': 'multi_reward',
            'description': 'a give up task with multiple rewards given in the exponential port.',
            'keys': {
                'head': 'IR sensor detecting when the mouse pokes its head into the port',
                'lick': 'IR sensor detecting when the mouse licks the lick spout',
            },
        },
    }
    path = os.path.join(os.getcwd(), '../data_standard/task_data.json')
    save_json(path, task_data)


if __name__ == '__main__':
    # save_paths()
    # save_mouse_data()
    # save_task_data()
    edit_mouse_data()
