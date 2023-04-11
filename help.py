import os
import tkinter.filedialog

filename = tkinter.filedialog.askopenfilename()
if filename == "" or not os.path.isfile(filename):
    print("return")
