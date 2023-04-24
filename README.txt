This script allows to backup directories at a specified interval.
The script tracks changes in the structure of the source directory.
If changes are detected, the script performs copying (if the file is added in the source folder)
or deletion (if the file is removed from the source folder) to the replica folder.

To run the script, open a terminal, navigate to the folder where the script file is located,
and run the following command:
python synchronizer.py /path/to/source_folder /path/to/replica_folder 5 /path/to/log_file

Where:
/path/to/source_folder - source folder path
/path/to/replica_folder - replica folder path
5 - interval in seconds
/path/to/log_file - logging file path


In order to stop the script, just press the key combination: Ctrl + C.

Requirements:
Python version 3.10.
