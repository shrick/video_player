# video player
import argparse
from functools import partial
import tkinter as tk
import vlc

def playback(player):
    player.set_pause(player.is_playing())

def stop(player, root, delete=False):
    player.stop()
    player.release()
    if delete:
        print("TBD delete file")
    root.destroy()

def get_filename():
    parser = argparse.ArgumentParser()
    parser.add_argument('filename')
    parser.add_argument('-fs', '--full-screen', action='store_true')
    args = parser.parse_args()
    return args.filename, args.full_screen

if __name__ == '__main__':
    filename, fullscreen = get_filename()
    player = vlc.MediaPlayer(filename)

    root = tk.Tk()
    root.title("Shrick Video Player")
    if fullscreen:
        root.attributes('-fullscreen', True)
    else:
        root.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}+0+0")

    tk.Grid.rowconfigure(root, 0, weight=1)
    tk.Grid.rowconfigure(root, 1, weight=0)
    tk.Grid.columnconfigure(root, 0, weight=1)
    tk.Grid.columnconfigure(root, 1, weight=1)
    tk.Grid.columnconfigure(root, 2, weight=1)

    frame = tk.Frame(root, bg='black')
    frame.grid(row=0, column=0, columnspan=3, sticky="NSEW")

    playback_callback = partial(playback, player=player)
    stop_callback = partial(stop, player=player, root=root)
    delete_callback = partial(stop_callback, delete=True)

    if not fullscreen:
        tk.Button(root, text="Play/Pause", fg="green",
            command=playback_callback).grid(row=1, column=0, sticky="SEW")
        tk.Button(root, text="Stop/Quit", fg="blue",
            command=stop_callback).grid(row=1, column=1, sticky="SEW")
        tk.Button(root, text="Delete", fg="red",
            command=delete_callback).grid(row=1, column=2, sticky="SEW")

    root.bind("<Escape>", lambda event: stop_callback())
    root.bind("<space>", lambda event: playback_callback())

    player.set_xwindow(frame.winfo_id())
    player.play()

    root.focus_set()
    root.mainloop()
