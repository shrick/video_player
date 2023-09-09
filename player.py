# video player
import argparse
from functools import partial
import tkinter as tk
import vlc

TITLE = "Shrick Video Player"
FF_SECONDS = 10
FR_SECONDS = 5

def playback(player):
    player.set_pause(player.is_playing())

def forward(player, seconds):
    player.set_time(player.get_time() + seconds * 1_000)

def rewind(player, seconds):
    player.set_time(player.get_time() - seconds * 1_000)

def stop(player, root, filename, delete=False):
    player.stop()
    player.release()
    if delete:
        print(f"TBD delete file '{filename}'")
    root.destroy()

def get_commandline_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('filename')
    parser.add_argument('-t', '--title', default=TITLE)
    parser.add_argument('-fs', '--full-screen', action='store_true')
    parser.add_argument('-ff', '--fast-forward', type=int, default=FF_SECONDS)
    parser.add_argument('-fr', '--fast-rewind', type=int, default=FR_SECONDS)
    args = parser.parse_args()
    return args.filename, args.title, args.full_screen, args.fast_forward, args.fast_rewind

if __name__ == '__main__':
    # init
    filename, title, fullscreen, ff, fr = get_commandline_arguments()
    player = vlc.MediaPlayer(filename)
    root = tk.Tk()

    # callbacks
    playback_callback = partial(playback, player=player)
    stop_callback = partial(stop, player=player, root=root, filename=filename)
    delete_callback = partial(stop_callback, delete=True)
    forward_callback = partial(forward, player=player, seconds=ff)
    rewind_callback = partial(rewind, player=player, seconds=fr)

    # controls
    root.title(f"{title} ({filename})")
    tk.Grid.rowconfigure(root, 0, weight=1)
    tk.Grid.rowconfigure(root, 1, weight=0)
    tk.Grid.columnconfigure(root, 0, weight=1)
    tk.Grid.columnconfigure(root, 1, weight=1)
    tk.Grid.columnconfigure(root, 2, weight=1)

    frame = tk.Frame(root, bg='black')
    frame.grid(row=0, column=0, columnspan=3, sticky="NSEW")
    player.set_xwindow(frame.winfo_id())

    if fullscreen:
        root.attributes('-fullscreen', True)
    else:
        root.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}+0+0")

        tk.Button(root, text="Play/Pause", fg="green",
            command=playback_callback).grid(row=1, column=0, sticky="SEW")
        tk.Button(root, text="Stop/Quit", fg="blue",
            command=stop_callback).grid(row=1, column=1, sticky="SEW")
        tk.Button(root, text="Delete", fg="red",
            command=delete_callback).grid(row=1, column=2, sticky="SEW")

    # key bindings
    root.bind('<Right>', lambda event: forward_callback())
    root.bind('<Left>', lambda event: rewind_callback())
    root.bind("<space>", lambda event: playback_callback())
    root.bind("<q>", lambda event: stop_callback())
    root.bind("<Escape>", lambda event: stop_callback())

    # start
    player.play()
    root.focus_set()
    root.mainloop()
