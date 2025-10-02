from support_classes import scp, ssh
import os
from user_settings import get_user_info

info_dict = get_user_info()


def get_filepaths():
    file_paths = []
    local_dir = os.path.join(os.getcwd(), 'data')
    for root, dirs, filenames in os.walk(local_dir):
        if len(dirs) == 0 and os.path.basename(root)[:2] == info_dict['initials']:
            mouse = os.path.basename(root)
            for f in filenames:
                file_paths.append(os.path.join(local_dir, mouse, f))
    return file_paths


def scp_rescue(gen_cmd=False):
    file_paths = get_filepaths()
    dest_path = os.path.join(info_dict['desktop_user_root'], info_dict['desktop_save_path'])

    for file in file_paths:
        path_parts = file.split(os.sep)
        file_mouse_path = os.path.join(*path_parts[-2:])
        full_dest_path = os.path.join(dest_path, path_parts[-2])
        file_name = os.path.join(*path_parts[-1:])
        os.chdir(os.path.join(*path_parts[-3:-1]))
        ssh_path = os.path.join(dest_path, path_parts[-2])
        os.system('sudo chmod o-w ' + file_name)
        mkdir_command = 'if not exist "%s" mkdir "%s"' % (
            ssh_path.replace('/', '\\'), ssh_path.replace('/', '\\'))

        ssh(info_dict['desktop_ip'], mkdir_command, info_dict['desktop_user'],
            info_dict['desktop_password'])

        res = scp(info_dict['desktop_ip'], file_name, full_dest_path, info_dict['desktop_user'],
                  info_dict['desktop_password'], cmd=gen_cmd)

        os.chdir(os.path.join(os.getcwd(), '..', '..'))
        if gen_cmd:
            print(res)
        else:
            if res == 0:
                print('\nSuccessful file transfer to "%s"\nDeleting local file from pi.'
                      % os.path.join(dest_path, file_mouse_path))
                os.remove(file)
            else:
                print('\nFile transfer failed with exit code "%s"\n' % str(res))


if __name__ == '__main__':
    scp_rescue()
