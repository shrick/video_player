# UserInterface

from typing import Callable

import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import askyesno

from player.control import Controller

class UserInterface:
    def __init__(self, title: str, fullscreen: bool, controller: Controller) -> None:
        self._started = False
        self._setup(title, fullscreen, controller)
        self._start_playback = controller.register_ui(self)

    def _setup(self, title: str, fullscreen: bool, controller: Controller) -> None:
        # window
        self._root = tk.Tk()
        self._root.title(title)

        # widgets
        tk.Grid.rowconfigure(self._root, 0, weight=0)
        tk.Grid.rowconfigure(self._root, 1, weight=1)
        tk.Grid.rowconfigure(self._root, 2, weight=0)
        tk.Grid.rowconfigure(self._root, 3, weight=0)
        tk.Grid.columnconfigure(self._root, 0, weight=1)
        tk.Grid.columnconfigure(self._root, 1, weight=1)
        tk.Grid.columnconfigure(self._root, 2, weight=1)

        self._caption = tk.Label(self._root)
        self._caption.grid(row=0, column=0, columnspan=3, sticky="NEW")

        self._video = tk.Frame(self._root, bg='black')
        self._video.grid(row=1, column=0, columnspan=3, sticky="NSEW")

        self._progress = tk.IntVar()
        ttk.Progressbar(variable=self._progress).grid(row=2, column=0, columnspan=3, sticky="SEW")

        # Wireless presenter compatible key bindings:
        # - Next        = Page Down
        # - Previous    = Page Up
        # - Start/Stop  = Alternating between F5 and Esc
        # - Hide        = b
        self._root.bind('b', lambda presenter_event: controller.fast_rewind())              # presenter
        self._root.bind('<Left>', lambda e: controller.fast_rewind())
        self._root.bind('<Right>', lambda e: controller.fast_forward())
        self._root.bind("<space>", lambda e: controller.toggle_playback())
        self._root.bind("<F5>", lambda presenter_event: controller.toggle_playback())       # presenter
        self._root.bind("<Escape>", lambda presenter_event: controller.toggle_playback())   # presenter
        self._root.bind("<Prior>", lambda presenter_event: controller.prev_video())         # presenter
        self._root.bind("<Next>", lambda presenter_event: controller.next_video())          # presenter
        self._root.bind("<d>", lambda e: controller.delete())
        self._root.bind("<q>", lambda e: controller.stop())
        self._root.bind("<a>", lambda e: controller.abort())

        if fullscreen:
            self._root.attributes('-fullscreen', True)
            self._root.lift()
            self._root.focus_force()
        else:
            self._root.geometry(f"{self._root.winfo_screenwidth()}x{self._root.winfo_screenheight()}+0+0")
            tk.Button(self._root, text="Play/Pause", fg="green",
                command=controller.toggle_playback).grid(row=3, column=0, sticky="SEW")
            tk.Button(self._root, text="Stop/Quit", fg="blue",
                command=controller.stop).grid(row=3, column=1, sticky="SEW")
            tk.Button(self._root, text="Delete", fg="red",
                command=controller.delete).grid(row=3, column=2, sticky="SEW")

    def start(self) -> None:
        if not self._started:
            self._start_playback()
            self._root.mainloop()
            self._started = True

    def quit(self) -> None:
        self._root.destroy()

    def set_caption(self, caption) -> None:
        self._caption.configure(text=caption)

    def set_progress(self, progress: float) -> None:
        self._progress.set(int(progress))

    def schedule_action(self, interval, action) -> Callable:
        job = self._root.after(interval, action)

        def cancel_action():
            self._root.after_cancel(job)

        return cancel_action

    def question_dialog(self, title, message):
        return askyesno(title=title, message=message)

    def get_video_widget_id(self) -> int:
        return self._video.winfo_id()
