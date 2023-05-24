"""
###############################################
Author: Omer Dagry
Mail: omerdagry@gmail.com
Date: 30/05/2023 (dd/mm/yyyy)
###############################################
"""

import os
import time
import shutil


def block(path: str) -> bool:
    """ :return: True to signal the "lock" is acquired """
    """
        create a folder "folder_name" to block another thread from touching a 
        specific resource file of the user/chat because we are reading the file 
        and then writing back and if someone does it at the same time with us 
        something will be lost, so blocking like this allows to block only for 
        this specific chat and not block all the clients threads, which is what we want
    """
    while True:
        try:
            os.makedirs(path, exist_ok=False)
            break
        except OSError:  # locked
            time.sleep(0.0005)
    return True


def unblock(path: str) -> bool:
    """ :return: False to signal the "lock" isn't acquired """
    if not os.path.isdir(path):
        raise ValueError(f"The 'lock' is already unlocked. (path - '{path}')")
    shutil.rmtree(path)
    return False
