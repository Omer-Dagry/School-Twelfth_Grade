import os
import wave
import time
import pyaudio
import logging
import playsound

from tkinter import *
from typing import Callable
from multiprocessing import Process


# Constants
# logging
LOG_DIR = 'log'
LOG_LEVEL = logging.DEBUG
LOG_FILE = LOG_DIR + "/ChatEase-Client.log"
LOG_FORMAT = "%(levelname)s | %(asctime)s | %(processName)s | %(threadName)s | %(message)s"

# Globals
stop_rec: bool

# Create All Needed Directories & Files & Initialize logging
os.makedirs(LOG_DIR, exist_ok=True)
if not os.path.isfile(LOG_FILE):
    with open(LOG_FILE, "w"):
        pass
logging.basicConfig(format=LOG_FORMAT, filename=LOG_FILE, level=LOG_LEVEL)


def playsound_wrapper(email: str, sound: str, block: bool = True):
    try:
        playsound.playsound(sound, block)
    except playsound.PlaysoundException as e:
        logging.warning(f"[RecordingGUI]: exception when playing audio file, ex: {e} ({email})")


class RecordingGUI:
    def __init__(self, email: str, record_button: Button, winfo_screenwidth: int, winfo_screenheight: int,
                 upload_file: Callable, chat_id: str, record_audio_func: Callable):
        #
        logging.info(f"[RecordingGUI]: initializing ({email})")
        self.__email = email
        self.__upload_file = upload_file
        self.__record_button = record_button
        self.__chat_id = chat_id
        self.__winfo_screenwidth = winfo_screenwidth
        self.__winfo_screenheight = winfo_screenheight
        self.__record_audio_func = record_audio_func
        #
        self.__tmp_file = rf"{self.__email}\temp.wav"
        #
        self.__playing_button: Button | None = None
        self.__playing_process: Process | None = None
        self.__recording_button: Button | None = None
        self.__playing_file_path: str = self.__tmp_file
        #
        os.makedirs(self.__email, exist_ok=True)
        logging.info(f"[RecordingGUI]: finished initializing ({email})")

    def record_audio(self):
        """
        Call This Function To Record Audio.
        Create A Thread For This Call.
        """
        global stop_rec
        stop_rec = False
        self.__record_button.configure(command=self.__stop_recording, text="Stop Recording")
        self.__record_audio()

    @staticmethod
    def __stop_recording():
        """ Changes the variable stop_rec to False """
        global stop_rec
        stop_rec = True

    def __record_audio(self):
        """
        Records Audio
        Saves it to a file named temp.wav in the user folder
        """
        logging.info(f"[RecordingGUI]: starting to record ({self.__email})")
        global stop_rec
        skip = False
        try:
            audio = pyaudio.PyAudio()
            stream = audio.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
            frames = []
            while not stop_rec:
                data = stream.read(1024)
                frames.append(data)
            stream.stop_stream()
            stream.close()
            audio.terminate()
            with open(self.__tmp_file, "wb") as f:
                sound_file = wave.open(f, "wb")
                sound_file.setnchannels(1)
                sound_file.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
                sound_file.setframerate(44100)
                sound_file.writeframes(b''.join(frames))
                sound_file.close()
        except Exception as e:  # in case there is no microphone
            skip = True
            logging.debug(f"[RecordingGUI]: exception recording, ex: {str(e)} ({self.__email})")
        finally:
            # disable recording button
            self.__record_button.configure(command=self.__record_audio_func, text="Record", state=DISABLED)
            stop_rec = True
        if not skip:
            logging.info(f"[RecordingGUI]: finished recording ({self.__email})")
            self.__recording_options()

    def __recording_options(self):
        """
        after recording this function will be called to open a window with 3 options
        1) play - plays the voice recording
        2) delete - deletes the voice recording (doesn't send it)
        3) send - send the voice recording
        """
        logging.info(f"[RecordingGUI]: initializing recording options GUI ({self.__email})")
        color = "#ffffd0"
        size = 120
        window_x = self.__winfo_screenwidth / 2
        window_y = self.__winfo_screenheight / 2
        # create options window & configure it
        self.__options_window = Tk()
        self.__options_window.protocol("WM_DELETE_WINDOW", lambda: None)
        self.__options_window.title("Options")
        self.__options_window.geometry("250x%d+%d+%d" % (size, window_x, window_y))
        self.__options_window.minsize(250, size)
        self.__options_window.maxsize(250, size)
        self.__playing_file_path = self.__tmp_file
        self.__playing_button = Button(self.__options_window, text="Play", bg=color, width=21)
        self.__playing_button.configure(command=self.__play_audio_thread)
        self.__playing_button.grid(row=0, column=0, sticky="news")
        delete = Button(self.__options_window, text="Delete", bg=color, command=self.__delete_file_close_window)
        delete.grid(row=1, column=0, sticky="news")
        send = Button(
            self.__options_window, text="Send", bg=color,
            command=lambda: self.__upload_file(
                self.__chat_id, self.__tmp_file, self.__options_window, True
            )
        )
        send.grid(row=2, column=0, sticky="news")
        logging.info(f"[RecordingGUI]: finished initializing recording options GUI ({self.__email})")
        logging.info(f"[RecordingGUI]: mainloop ({self.__email})")
        self.__options_window.mainloop()
        # if user didn't press anything and closed the window the recording file still exist so this deletes it
        if os.path.isfile(self.__tmp_file):
            count = 0
            while count < 5:
                try:
                    os.remove(self.__tmp_file)
                    logging.info(f"[RecordingGUI]: removed audio file ({self.__email})")
                    break
                except Exception as e:
                    logging.debug(
                        f"[RecordingGUI]: exception while removing the audio file, ex: {str(e)} ({self.__email})")
                    time.sleep(0.5)
                    count += 1
        self.__record_button.configure(command=self.__record_audio_func, text="Record", state=NORMAL)

    def __play_audio_thread(self):
        """ Creates a thread that plays the audio file and changes the button text """
        if self.__playing_process is not None:  # if there is something playing right now it will terminate it
            self.__terminate_and_restore_button()
        logging.info(f"[RecordingGUI]: playing audio file ({self.__email})")
        play_ = Process(target=playsound_wrapper, args=(self.__email, self.__playing_file_path,), daemon=True,
                        name="RecordingGUI - Play")
        play_.start()
        self.__playing_process = play_
        self.__playing_button.configure(text="Stop")
        self.__playing_button.configure(command=self.__terminate_and_restore_button)

        # Checks if the audio file is still being played, if not shuts the process
        while True:
            # update the gui window because we are in a while loop that
            # doesn't allow the gui to update unless we call update()
            self.__options_window.update()
            if isinstance(self.__playing_process, Process) and not self.__playing_process.is_alive():
                self.__terminate_and_restore_button()
                break
            time.sleep(0.05)

    def __terminate_and_restore_button(self):
        """ Terminates the process of the audio file, Restores button """
        if isinstance(self.__playing_process, Process):
            self.__playing_process.terminate()
        logging.info(f"[RecordingGUI]: stopped playing audio file ({self.__email})")
        self.__playing_process = None
        self.__playing_button.configure(text="Play")
        self.__playing_button.configure(command=self.__play_audio_thread)

    def __delete_file_close_window(self):
        """ Deletes the voice recording and closes the voice recording options window """
        if os.path.isfile(self.__playing_file_path):
            count = 0
            while count < 5:
                try:
                    os.remove(self.__playing_file_path)
                    logging.info(f"[RecordingGUI]: removed audio file ({self.__email})")
                    break
                except PermissionError:
                    time.sleep(0.5)
                    count += 1
        self.__options_window.quit()
