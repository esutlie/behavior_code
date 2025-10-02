import os
import paramiko
from datetime import datetime
from user_info import get_user_info


def upload_to_pi(pi_host_name, durations=False):
    local_path = os.path.join(os.getcwd(), "stand_alone")
    pi_user_name = 'pi'
    remote_path = '/home/pi/behavior'
    password = 'shuler'
    # command = f'scp -r {os.path.join(local_path, "stand_alone")} {pi_user_name}@{pi_host_name}:{remote_path}'
    ssh = paramiko.SSHClient()
    ssh.load_host_keys(os.path.expanduser(os.path.join("~", ".ssh", "known_hosts")))
    ssh.connect(pi_host_name, username=pi_user_name, password=password)
    sftp = ssh.open_sftp()
    try:
        sftp.chdir(remote_path)  # Test if remote_path exists
    except IOError:
        sftp.mkdir(remote_path)  # Create remote_path
        sftp.chdir(remote_path)

    [_, _, files] = list(os.walk(local_path))[0]
    for f in files:
        if f != 'desktop.ini' and (f != 'durations.pkl' or durations):
            print(pi_host_name + ' ' + '/'.join([remote_path, f]))
            sftp.put(os.path.join(local_path, f), '/'.join([remote_path, f]))
    sftp.close()
    ssh.close()


def reset_time(pi_host_name):
    now = datetime.now()
    t = now.strftime('%Y-%m-%d %H:%M:%S')
    pi_user_name = 'pi'
    password = 'shuler'
    ssh = paramiko.SSHClient()
    ssh.load_host_keys(os.path.expanduser(os.path.join("~", ".ssh", "known_hosts")))
    ssh.connect(pi_host_name, username=pi_user_name, password=password)
    stdin, stdout, stderr = ssh.exec_command(f"sudo date -s '{t}'")
    cmd_output = stdout.read()
    print(f'set {pi_host_name} time to {cmd_output}')
    ssh.close()


def ping_host(pi_host_name):
    pi_user_name = 'pi'
    password = 'shuler'
    ssh = paramiko.SSHClient()
    ssh.load_host_keys(os.path.expanduser(os.path.join("~", ".ssh", "known_hosts")))
    try:
        ssh.connect(pi_host_name, username=pi_user_name, password=password, timeout=1)
        ssh.close()
        return True
    except Exception as e:
        ssh.close()
        print(f'{pi_host_name} ping failed', end=': ')
        print(e)
        return False


if __name__ == '__main__':
    info_dict = get_user_info()
    for name in info_dict['pi_names']:
        upload_to_pi(name, durations=False)
        reset_time(name)
