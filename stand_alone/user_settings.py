import os


def get_user_info():
    info_dict = {
        'initials': 'SZ',
        'mouse_buttons': [['SZ050', 'SZ051', 'SZ052'],
                          ['SZ053', 'SZ054', 'SZ055'],
                          ['SZ056', 'SZ057', 'SZ058'],
                          ['SZ059', 'cf_testmouse', 'sr_testmouse']],
        'button_colors': [[12, 12, 12],
                          [12, 12, 2],
                          [2, 2, 2],
                          [2, 3, 3]],
        'mouse_assignments': {
            'SZ050': 'cued_forgo',
            'SZ051': 'cued_forgo',
            'SZ052': 'cued_forgo',
            'SZ053': 'single_reward',
            'SZ054': 'single_reward',
            'SZ055': 'cued_forgo',
            'SZ056': 'cued_forgo',
            'SZ057': 'cued_forgo',
            'SZ058': 'single_reward',
            'SZ059': 'single_reward',
            'sr_testmouse': 'single_reward',
            'cf_testmouse': 'cued_forgo'
        },
        'mouse_colors': {
            'SZ050': 12,
            'SZ051': 12,
            'SZ052': 12,
            'SZ053': 12,
            'SZ054': 12,
            'SZ055': 2,
            'SZ056': 2,
            'SZ057': 2,
            'SZ058': 2,
            'SZ059': 2,
            'sr_testmouse': 3,
            'cf_testmouse': 3
        },
        'desktop_ip': '10.16.80.130',
        'desktop_user': 'Shichen',
        'desktop_password': 'shuler_914WBSB',
        'desktop_user_root': os.path.join('C:/', 'Users', 'Shichen'),
        'desktop_save_path': os.path.join('OneDrive - Johns Hopkins', 'ShulerLab', 'behavior_code', 'data'),
    }
    return info_dict