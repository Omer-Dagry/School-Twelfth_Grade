from tkinter import *
from tkinter.scrolledtext import ScrolledText


class Check(Tk):
    def __init__(self, seen_by: list[str]):
        super().__init__()
        self.__seen_by = seen_by
        self.__setup_seen_by()

    def __setup(self):
        #
        for widget in self.winfo_children():
            widget.destroy()
        #

    def __setup_seen_by(self):
        #
        width = 250
        height = 250
        location_x = self.winfo_pointerx() - 250 // 2
        location_y = self.winfo_pointery() - 120 // 2
        self.maxsize(width, height)
        self.minsize(width, height)
        self.geometry(f"{width}x{height}+{location_x}+{location_y}")
        #
        for widget in self.winfo_children():
            widget.destroy()
        #
        back = Button(self, text="Back", command=self.__setup)
        back.place(x=0, y=0)
        #
        seen_by_label = Label(self, text="Seen By", anchor=CENTER, height=2)
        seen_by_label.pack(fill=X)
        #
        seen_by_list = ScrolledText(self, font=('helvetica', '16'))
        for i in range(len(self.__seen_by)):
            user_label = Label(self, text=self.__seen_by[i], bg="#d0ffff")
            seen_by_list.window_create(END, window=user_label)
            if i < len(self.__seen_by) - 1:
                seen_by_list.insert(END, "\r\n")
        seen_by_list.pack()
        #
        seen_by_label.lift()
        back.lift()
        #


def main():
    seen_by = ["omer", "noa", "adi", "eytan", "talya"] * 5
    check = Check(seen_by)
    check.mainloop()


if __name__ == '__main__':
    main()
