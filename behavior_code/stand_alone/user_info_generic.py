import os

"""
Copy this file to a new one with the name 'user_settings.py' in the same folder location as this one. Replace all BOLD_CASE
variables with your own. GOOD LUCK!
"""


def get_user_info():
    info_dict = {
        'initials': 'USER_INITIALS',
        'mouse_buttons': [['MOUSE_NAME', 'MOUSE_NAME', 'MOUSE_NAME'],
                          ['MOUSE_NAME', 'MOUSE_NAME', 'MOUSE_NAME'],
                          ['MOUSE_NAME', 'MOUSE_NAME', 'MOUSE_NAME']],
        'button_colors': [[1,1,1],
                          [2,2,2],
                          [3,3,3]],
        'mouse_assignments': {
            'MOUSE_NAME': 'TASK_NAME',
            'testmouse': 'TASK_NAME',
        },
        'mouse_colors': {
            'MOUSE_NAME': 1,
            'testmouse': 1,
        },

        'desktop_ip': 'PUT_IP_ADDRESS_HERE',
        'desktop_user': 'PUT_USERNAME_HERE',
        'desktop_password': 'PUT_PASSWORD_HERE',
        'desktop_user_root': os.path.join('C:/', 'PATH', 'TO', 'ROOT'),
        'desktop_save_path': os.path.join('PATH', 'TO', 'DATA', 'FOLDER'),
    }
    return info_dict

import os


def get_user_info():
    info_dict = {
        'initials': 'ES',
        'mouse_buttons': [['ES041', 'ES042', 'ES037'],
                          ['ES043', 'ES044', 'ES039'],
                          ['ES045', 'ES046', 'ES047']],
        'mouse_assignments': {
            'ES036': 'single_reward',
            'ES037': 'single_reward',
            'ES039': 'cued_forgo',
            'ES040': 'cued_forgo',
            'ES041': 'single_reward',
            'ES042': 'single_reward',
            'ES043': 'single_reward',
            'ES044': 'single_reward',
            'ES045': 'cued_forgo',
            'ES046': 'cued_forgo',
            'ES047': 'cued_forgo',
            'testmouse': 'cued_forgo',
        },
        'mouse_colors': {
            'ES036': 1,
            'ES037': 1,
            'ES039': 2,
            'ES040': 2,
            'ES041': 3,
            'ES042': 3,
            'ES043': 3,
            'ES044': 3,
            'ES045': 4,
            'ES046': 4,
            'ES047': 4,
            'testmouse': 1,
        },
        'desktop_ip': '10.16.79.143',
        'desktop_user': 'Elissa',
        'desktop_password': 'shuler',
        'desktop_user_root': os.path.join('C:/', 'Users', 'Elissa'),
        'desktop_save_path': os.path.join('GoogleDrive', 'Code', 'Python', 'behavior_code', 'data'),
    }
    return info_dict
