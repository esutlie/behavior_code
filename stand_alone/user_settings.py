import os

"""
Copy this file to a new one with the name 'user_settings.py' in the same folder location as this one. Replace all BOLD_CASE
variables with your own. GOOD LUCK!
"""


def get_user_info():
    info_dict = {
        'initials': 'RK',
        # 'mouse_buttons': [['RK001', 'RK002', 'RK003'],
        #                   ['RK004', 'RK005', 'RK006'],
        #                   ['testmouse1', 'testmouse2', 'testmouse3'],
        #                   ],
        'mouse_buttons': [['RK007', 'RK008', 'RK009'],
                          ['RK010', 'testmouse', 'testmouse'],
                          ['testmouse1', 'testmouse2', 'testmouse3'],
                          ],
        'button_colors': [[12, 12, 12],
                          [12, 12, 12],
                          [2, 2, 2],
                          [2, 3, 3]
                          ],
        'mouse_assignments': {
            # 'RK001': 'multi_reward',
            # 'RK002': 'multi_reward',
            # 'RK003': 'multi_reward',
            # 'RK004': 'multi_reward',
            # 'RK005': 'multi_reward',
            # 'RK006': 'multi_reward',
            'RK007': 'multi_reward',
            'RK008': 'multi_reward',
            'RK009': 'multi_reward',
            'RK010': 'multi_reward',
            'testmouse1': 'multi_reward'
        },
        'port_swap_assignments': {
            'RK007': True,
            'RK008': False,
            'RK009': True,
            'RK010': False,
            'testmouse1': False
        },
        'block_swap_assignments': { #0.4 if swap_block is false, 0.8 if true.
            'RK007': 'trial',
            'RK008': 'trial',
            'RK009': 'trial',
            'RK010': 'trial',
            'testmouse1': 'trial'
        },
        'mouse_colors': {
            # 'RK001': 1,
            # 'RK002': 1,
            # 'RK003': 1,
            # 'RK004': 2,
            # 'RK005': 2,
            # 'RK006': 2,
            # 'testmouse1': 3,
            # 'testmouse2': 3,
            # 'testmouse3': 3,
            'RK007': 1,
            'RK008': 1,
            'RK009': 1,
            'RK010': 1,
        },
        # 'desktop_ip': '192.168.0.150',
        # 'desktop_user': 'rie',
        # 'desktop_password': 'shuler',
        # 'desktop_user_root': os.path.join('C:/', 'Users', 'Rie'),
        # 'desktop_save_path': os.path.join('behavior_data'),
        'desktop_ip': '10.203.164.9',
        'desktop_user': 'Shichen',
        'desktop_password': 'shuler_914WBSB',
        'desktop_user_root': os.path.join('C:/', 'Users', 'Shichen'),
        'desktop_save_path': os.path.join('OneDrive - Johns Hopkins', 'ShulerLab', 'Rie_behavior', 'data'),
    }
    return info_dict
