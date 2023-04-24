import logging
import os
import shutil
import signal
import sys
import time
from itertools import zip_longest

logger = logging.getLogger(__name__)


class Synchronizer:
    """The Synchronizer class allows to synchronize the source folder with the replica folder

    Attributes
    ----------
    source_folder_state : dict
        the current state of the source folder.
    replica_folder_state : dict
        the current state of the replica folder.
    source_directory_path : str
        path to source folder.
    replica_directory_path : str
        path to replica folder.
    interval : int
        time in seconds to set the frequency of script execution.
    log_file_path : str
        path to the logging file.

    Methods
    -------
    get_absolute_path(directory_path, object_name)
        Creates an absolute path.
    make_copy(directory_path, object_name, object_type)
        Copies a file or folder to the replica folder.
    delete_files(directory_object, object_type)
        Deletes a folder or file.
    check_folder_state(self, directory, folder_state, state_only=False)
        Checks differences in source and replica folders.
    create_log_file()
        Creates a log file in the specified directory.
    check_arguments()
        Checks arguments for count, data type, and typos.
    set_arguments()
        Sets arguments from the command line to class attributes.
    stop_synchronizer(self, signal, frame)
        Terminates the script.
    run_synchronizer()
        Starts a loop for a script.
    """

    def __init__(self):
        self.source_folder_state: dict = {}
        self.replica_folder_state: dict = {}
        self.source_directory_path: str = ''
        self.replica_directory_path: str = ''
        self.interval: int = 0
        self.log_file_path: str = ''

        self.set_arguments()
        self.create_log_file()
        self.run_synchronizer()

    def get_absolute_path(self, directory_path: str, object_name: str) -> str:
        """Creates an absolute path for file or folder in replica folder by replacing from replica to source paths.
        That's required for compare source folder state with replica folder state.

        :param directory_path:
            path to the file or folder.
        :param object_name:
            folder or file name.
        :return:
            string with absolute path for files or folders in replica folder.
        """

        return os.path.join(directory_path, object_name).replace(self.replica_directory_path,
                                                                 self.source_directory_path)

    def make_copy(self, directory_path: str, object_name: str, object_type: str) -> None:
        """Copies a file or folder to the replica folder if path of file or folder not exists in replica folder
        and adds file or folder path to replica and source state.

        :param directory_path:
            path to the folder.
        :param object_name:
            folder or file name.
        :param object_type:
            type of object to define key for record in folder state.
        """

        path_abs = os.path.join(directory_path, object_name)
        replica_absolute_path = path_abs.replace(self.source_directory_path,
                                                 self.replica_directory_path)

        if not os.path.exists(replica_absolute_path):
            self.replica_folder_state[object_type].add(path_abs)
            match object_type:
                case 'folders':
                    shutil.copytree(path_abs, replica_absolute_path)
                    logger.info(
                        f'New folder "{object_name}" was detected in source and copied to the replica folder. '
                        f'Path: "{replica_absolute_path}"')

                case 'files':
                    shutil.copy(path_abs, replica_absolute_path)
                    logger.info(
                        f'New file "{object_name}" was detected in source and copied to the replica folder. '
                        f'Path: "{replica_absolute_path}"')

        self.source_folder_state[object_type].add(path_abs)

    def delete_files(self, directory_object: str, object_type: str) -> None:
        """Deletes a folder or file.

        :param directory_object:
            path where locates folder or file.
        :param object_type:
            type of object to choosing function for deletion.
        """

        replica_absolute_path = directory_object.replace(self.source_directory_path,
                                                         self.replica_directory_path)
        if os.path.exists(replica_absolute_path):

            match object_type:
                case 'folders':
                    shutil.rmtree(replica_absolute_path)
                    logger.info(
                        f'Folder "{directory_object.split("/")[-1]}" was deleted from source. '
                        f'Path: "{replica_absolute_path}"')
                case 'files':
                    os.remove(replica_absolute_path)
                    logger.info(
                        f'File "{directory_object.split("/")[-1]}" was deleted from source. '
                        f'Path: "{replica_absolute_path}"')

    def check_folder_state(self, directory: str, folder_state: dict, state_only: bool = False) -> None:
        """Checks differences in states of source and replica folders and makes copy or deletions in replica folder.
        If parameter state_only is True collect state from path in parameter directory to folder state which specified
        in parameter folder_state.

        :param directory:
            path to the source directory.
        :param folder_state:
            state for specified directory.
        :param state_only:
            flag: if True - function only collect state, default False.
        """

        for current_directory in os.walk(directory):
            directory_path, folders_in_directory, files_in_directory = current_directory

            for folder, file in zip_longest(folders_in_directory, files_in_directory):
                if state_only:
                    if folder:
                        folder_state['folders'].add(self.get_absolute_path(directory_path, folder))
                    if file:
                        folder_state['files'].add(self.get_absolute_path(directory_path, file))
                    continue

                if folder:
                    self.make_copy(directory_path, folder, 'folders')
                if file:
                    self.make_copy(directory_path, file, 'files')

        deleted_folders = (self.replica_folder_state['folders']) - (self.source_folder_state['folders'])
        deleted_files = (self.replica_folder_state['files']) - (self.source_folder_state['files'])

        for folder, file in zip_longest(deleted_folders, deleted_files):
            if folder:
                self.delete_files(folder, 'folders')
            if file:
                self.delete_files(file, 'files')

        self.replica_folder_state = self.source_folder_state

        self.source_folder_state = {
            'folders': set(),
            'files': set(),
        }

    def create_log_file(self) -> None:
        """Creates a log file in the specified directory."""

        log_file_name = 'folder_synchronizer.log'
        logging.basicConfig(filename=f'{os.path.join(self.log_file_path, log_file_name)}', level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        logger.addHandler(logging.StreamHandler())

    def check_arguments(self) -> list:
        """Checks arguments for count, data type, and typos.

        :return:
            list of checked arguments.
        """

        arguments = sys.argv[1:]

        if len(arguments) != 4:
            logger.error('\nTo run this script, you should pass 4 arguments:\n'
                         '-source folder path\n'
                         '-replica folder path\n'
                         '-interval in seconds\n'
                         '-logging file path\n\n'
                         'For example: '
                         'python synchronizer.py /path/to/source_folder /path/to/replica_folder 5 /path/to/log_file')
            sys.exit()

        for position, argument in enumerate(arguments):
            if position == 2:
                try:
                    arguments[2] = float(eval(argument))
                except (ValueError, TypeError, NameError):
                    logger.error('\nInterval should be an integer.')
                    sys.exit()
                continue

            if not os.path.exists(argument):
                logger.error(f'\nThis directory does not exist or contains a typo: "{argument}"\n')
                sys.exit()

            if os.path.abspath(argument) == os.getcwd() and position != 3:
                logger.error(f'\nThis directory cannot be used because '
                             f'it is the same as the home directory of the current script: "{argument}"\n')
                sys.exit()

        return arguments

    def set_arguments(self) -> None:
        """Sets folders state and arguments from the command line to class attributes."""

        self.source_directory_path, self.replica_directory_path, self.interval, self.log_file_path = self.check_arguments()

        self.replica_folder_state = self.source_folder_state = {
            'folders': set(),
            'files': set(),
        }

    def stop_synchronizer(self, signal, frame) -> None:
        """Terminates the script.

        :param signal:
            signal number
        :param frame:
            the interrupted stack frame
        """

        logger.info('Script is stopped')
        sys.exit()

    def run_synchronizer(self) -> None:
        """Starts a loop for a script at intervals."""

        logger.info('Script is running')
        signal.signal(signal.SIGINT, self.stop_synchronizer)
        self.check_folder_state(self.replica_directory_path, self.replica_folder_state, state_only=True)
        while True:
            self.check_folder_state(self.source_directory_path, self.source_folder_state)
            time.sleep(self.interval)


if __name__ == '__main__':
    Synchronizer()
