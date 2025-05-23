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
        'mouse_assignments': {
            'MOUSE_NAME': 'TASK_NAME',
            'testmouse': 'TASK_NAME',
        },
        'mouse_swap_assignments': {
            'MOUSE_NAME': False,
            'testmouse': False,
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
