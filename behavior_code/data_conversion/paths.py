import os


def get_paths():
    return {
        'original_data': os.path.join(os.path.dirname(os.getcwd()), 'data'),
        'converted_data': os.path.join(os.path.dirname(os.getcwd()), 'data_standard')
    }
