import os
import sys
import time
import shutil
import pickle
import random
import datetime
import win32api
import importlib
import win32event
import win32process

from typing import *


class Process:
    def __init__(self, target: Callable, args: Union[tuple, Any] = None, kwargs: Union[dict[str, Any], None] = None,
                 name: Union[str, None] = None, process_security_attributes=None, thread_security_attributes=None,
                 inherit_handles: int = 0, flags: Union[int, None] = None, environment: Union[Dict, None] = None,
                 current_directory: Union[str, None] = None):
        kwargs = {} if kwargs is None else kwargs
        args = () if args is None else args
        assert isinstance(kwargs, dict)
        assert isinstance(args, tuple)
        self.__target = target
        self.__args = args
        self.__kwargs = kwargs
        self.__name = name
        python = sys.executable
        script_name = ".".join(__file__.split('\\')[-1].split('.')[:-1])
        #
        target_file_path = target.__code__.co_filename
        target_name = "'" + target.__qualname__ + "'"
        dir_name = os.path.dirname(__file__)
        file_name = "process_temp_file.py"
        while os.path.isfile(f'{dir_name}\\{file_name}'):
            file_name = ".".join(file_name.split(".")[:-1]) + "_." + file_name.split(".")[-1]
        shutil.copy2(src=target_file_path, dst=f'{dir_name}\\{file_name}')
        self.__file_name = file_name
        file_name = "'" + file_name.split(".")[0] + "'"
        if self.__args != () or self.__kwargs != {}:
            pickle_file_name = f"pickle_process_args_kwargs{random.randrange(-100000, len(args))}_" \
                               f"{str(datetime.datetime.now().strftime('%Y_%m_%d %H.%M.%S.%f'))}"
            while os.path.isfile(pickle_file_name):
                time.sleep(0.001)
                pickle_file_name = f"pickle_process_args_kwargs{random.randrange(-100000, len(args))}_" \
                                   f"{str(datetime.datetime.now().strftime('%Y_%m_%d %H.%M.%S.%f'))}"
            try:
                with open(pickle_file_name, "wb") as f:
                    f.write(pickle.dumps((args, kwargs)))
            except (pickle.PickleError, pickle.PicklingError) as pickle_error:
                os.remove(pickle_file_name)
                raise pickle_error
            pickle_file_name = "'" + pickle_file_name + "'"
            #
            self.__command_line = \
                f'"{python}" -c "import {script_name}; {script_name}.Process.run(' \
                f'{pickle_file_name}, {file_name}, {target_name})"'
        else:
            self.__command_line = \
                f'"{python}" -c "import {script_name}; {script_name}.Process.run(' \
                f'None, {file_name}, {target_name})"'
        self.__process_security_attributes = process_security_attributes
        self.__thread_security_attributes = thread_security_attributes
        self.__inherit_handles = inherit_handles
        flags = win32process.CREATE_SUSPENDED if flags is None else flags | win32process.CREATE_SUSPENDED
        self.__flags = flags
        self.__environment = environment
        self.__current_directory = os.path.dirname(__file__) if current_directory is None else current_directory
        self.__startup_info = win32process.STARTUPINFO()
        self.__startup_info.hStdInput = win32api.GetStdHandle(win32api.STD_INPUT_HANDLE)
        self.__startup_info.hStdOutput = win32api.GetStdHandle(win32api.STD_OUTPUT_HANDLE)
        self.__startup_info.hStdError = win32api.GetStdHandle(win32api.STD_ERROR_HANDLE)
        self.__started = False
        self.__suspended = True
        self.__killed = False
        self.__process, self.__main_thread, self.__process_id, self.__main_thread_id = win32process.CreateProcess(
            self.__name, self.__command_line, self.__process_security_attributes, self.__thread_security_attributes,
            self.__inherit_handles, self.__flags, self.__environment, self.__current_directory, self.__startup_info
        )

    @staticmethod
    def run(pickled_data_file_name: str, file_name: str, target_name: str):
        """ This func unpickles the args & kwargs and then calls the target func """
        try:
            module = importlib.import_module(file_name)
            if "." in target_name:
                target_name_list = target_name.split(".")
                for target_name in target_name_list:
                    target = getattr(module, target_name)
                    module = target
            else:
                target = getattr(module, target_name)
        except AttributeError as error:
            os.remove(file_name + ".py")
            if pickled_data_file_name is not None:
                os.remove(pickled_data_file_name)
            raise error
        except BaseException as err:
            os.remove(file_name + ".py")
            if pickled_data_file_name is not None:
                os.remove(pickled_data_file_name)
            raise err
        os.remove(file_name + ".py")
        if pickled_data_file_name is not None:
            try:
                with open(pickled_data_file_name, "rb") as f:
                    pickle_data = pickle.load(f)
            except (pickle.PickleError, pickle.PicklingError, pickle.UnpicklingError) as pickle_error:
                os.remove(pickled_data_file_name)
                raise pickle_error
            except BaseException as error:
                os.remove(pickled_data_file_name)
                raise error
            os.remove(pickled_data_file_name)
            args = pickle_data[0]
            kwargs = pickle_data[1]
        if pickled_data_file_name is not None:
            target(*args, **kwargs)
        else:
            target()

    def start(self):
        """ Start The Process Main Thread"""
        if self.__started:
            raise RuntimeError("process can only be started once")
        suspend_count = self.resume_main_thread()
        # wait for the main thread to import the target
        # function and only then returns from this function call
        while self.__file_name in os.listdir():
            time.sleep(0.1)
        self.__started = True
        return suspend_count

    def resume_main_thread(self):
        """ Resume Main Thread """
        if self.__suspended:
            self.__suspended = False
            return win32process.ResumeThread(self.__main_thread)
        raise RuntimeError("Can't resume a thread that isn't suspend.")

    def suspend_main_thread(self):
        """ Suspend Main Thread """
        if not self.__suspended:
            self.__suspended = True
            return win32process.SuspendThread(self.__main_thread)
        raise RuntimeError("Can't suspend a thread that isn't running.")

    def join(self, timeout=win32event.INFINITE) -> int:
        """
            Join This Process And All It's Threads
            (waits until the process exits by itself or until timing out)
            :param timeout: time-out interval in milliseconds
        """
        if self.__main_thread is not None and self.__started:
            return win32event.WaitForSingleObject(self.__process, timeout)
        raise RuntimeError("Can't join a process that hasn't started yet.'")

    def terminate(self):
        """ Terminates The Process ( same as .kill() )"""
        if self.__started and self.__process is not None:
            win32process.TerminateProcess(self.__process, -1)
            return
        raise RuntimeError("Can't terminate a process that hasn't started yet.")

    def kill(self):
        """ Kills The Process ( same as .terminate() )"""
        if self.__started and self.__process is not None:
            if self.is_alive():
                self.__killed = True
                win32process.TerminateProcess(self.__process, -1)
            return
        raise RuntimeError("Can't kill a process that hasn't started yet.")

    @staticmethod
    def exit_process(exit_code: int):
        """
            Closes The Current Process,
            Not Necessarily The Process Of A Specific Instance Of This Class.
            This Will Close The Process That The Call To This Function Was Made From.
        """
        win32process.ExitProcess(exit_code)

    def is_alive(self):
        """ Check If The Process Is Still Alive """
        if self.__process is not None and self.__started:
            return win32process.GetExitCodeProcess(self.__process) == 259
        raise RuntimeError("Can't check if process is alive, the process hasn't started yet.'")

    def get_exit_code(self):
        """ Get The Process Exit Code """
        if self.__process is not None and self.__started:
            if self.__killed:
                return None  # if the process was killed/terminated there is no exit code
            if self.is_alive():
                return None  # if process is still running there is no exit code yet
            return win32process.GetExitCodeProcess(self.__process)
        raise Exception("Can't check the process's exit code, the process hasn't started yet.'")

    def get_process_id(self):
        """ returns: the process id """
        return self.__process_id

    def get_main_thread_id(self):
        """ returns: the main thread id """
        return self.__main_thread_id

    def get_name(self):
        """ returns: the process name """
        return self.__name
