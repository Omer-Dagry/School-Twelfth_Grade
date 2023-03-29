# try to make a chat that when scrolling to the top it will load more messages
import time
from tkinter import *
from tkinter import scrolledtext


def load_more_messages(chat_text: scrolledtext.ScrolledText):
    chat_text.insert(1.0, "hello\n" * 120)
    chat_text.see(120.0)


def check_chat_position(root: Tk, chat_text: scrolledtext.ScrolledText):
    # print("hi", chat_text.yview())
    if chat_text.yview()[0] == 0:
        print("hi")
        load_more_messages(chat_text)
    root.after(500, lambda: check_chat_position(root, chat_text))


def main():
    root = Tk()
    chat_text = scrolledtext.ScrolledText(root)
    chat_text.insert(END, "hello world\n" * 120)
    chat_text.yview_pickplace(END)
    chat_text.pack()
    root.after(500, lambda: check_chat_position(root, chat_text))
    root.mainloop()


if __name__ == '__main__':
    main()
