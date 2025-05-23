import os
import shutil
import time
from pathlib import Path

# Define local and OneDrive paths
behavior_data_dir = Path("C:/Users/Shichen/OneDrive - Johns Hopkins/ShulerLab/Rie_behavior/data")
# onedrive_dir = Path("C:/Users/Valued Customer/OneDrive - Johns Hopkins/behavior_data")
# onedrive_dir = Path("C:/Users/Rie/OneDrive - Johns Hopkins/behavior_data")


def upload_cloud_backup():
    while True:
        try:
            # Walk through the behavior_data directory and identify files and folders
            for root, dirs, files in os.walk(behavior_data_dir):
                # Calculate the relative path from the base behavior_data directory
                relative_path = Path(root).relative_to(behavior_data_dir)
                # Create the corresponding subdirectory path in the onedrive backup folder
                backup_subdir = onedrive_dir / relative_path
                backup_subdir.mkdir(parents=True, exist_ok=True)  # Create directories if needed

                # Copy each file if it's not already in the backup folder
                for file_name in files:
                    src_file = Path(root) / file_name
                    dest_file = backup_subdir / file_name

                    # Only copy if the file doesn't exist in the destination
                    if not dest_file.exists():
                        shutil.copy2(src_file, dest_file)
                        print(f"Copied {src_file} to {dest_file}")

        except Exception as e:
            print(f"Error during backup: {e}")

        # Wait 24 hours before the next check
        time.sleep(3600 * 24)

if __name__ == '__main__':
    upload_cloud_backup()
