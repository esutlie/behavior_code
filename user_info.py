from datetime import date


def get_user_info():
    info_dict = {
        'initials': 'ES',
        'pi_names': ['elissapi0', 'elissapi2', 'elissapi4'],
        # 'pi_names': ['elissapi1'],
        'start_date': date(2023, 10, 11)  # For the current cohort, for the sake of simple_plots.py
    }
    return info_dict
