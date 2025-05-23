from datetime import date


def get_user_info():
    info_dict = {
        'initials': ['RK','ES'],
        # 'pi_names': ['elissapi0', 'elissapi4'],
        # 'pi_names': ['elissapi1', 'shichenpi2', 'shichenpi3','elissapi0', 'elissapi4'],
        'pi_names': ['elissapi1','shichenpi2'  , 'shichenpi3'],
        'start_date': date(2024, 12, 1)  # For the current cohort, for the sake of simple_plots.py
    }
    return info_dict
