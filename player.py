# video player
import argparse
import pathlib
from functools import partial
from dataclasses import dataclass
import configparser
import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import askyesno
import vlc

TITLE = "Shrick Video Player"
FF_SECONDS = 10
FR_SECONDS = 5
PROGRESS_INTERVAL = int(0.25 * 1_000)
CONFIG_FILENAME = "player.ini"

@dataclass(init=True)
class PlayerContext:
    root: ... = None
    player: ... = None
    filename: str = None
    progress: ... = None
    job: ... = None

def update_progress(context):
    percentage = context.player.get_position() * 100
    if context.player.get_time() < context.player.get_length() - 100:
        context.progress.set(percentage)
        context.job = context.root.after(PROGRESS_INTERVAL, lambda: update_progress(context))
    else:
        stop(context)

def toggle_playback(player):
    player.set_pause(player.is_playing())

def forward(player, seconds):
    new_time = min(player.get_length(), player.get_time() + seconds * 1_000)
    player.set_time(new_time)

def rewind(player, seconds):
    new_time = max(0, player.get_time() - seconds * 1_000)
    player.set_time(new_time)

def stop(context, delete=False):
    if context.job is not None:
        context.root.after_cancel(context.job)
        context.job = None
    context.player.stop()
    context.player.release()
    if delete:
        delete_file(context.filename)
    context.root.destroy()
    save_resume_filename(context.filename)

def delete_file(filename):
    yes = askyesno(title="Confirmation", message=f"Really delete file '{filename}'?")
    if yes:
        print(f"Deleting file '{filename}'...")
        file = pathlib.Path(filename)
        file.unlink(missing_ok=True)

def save_resume_filename(resume_filename):
    config = configparser.ConfigParser()
    config['resume'] = { 'filename': resume_filename }
    with open(CONFIG_FILENAME, 'w') as configfile:
        config.write(configfile)

def load_resume_filename():
    config = configparser.ConfigParser()
    config.read(CONFIG_FILENAME)
    try:
        resume_filename = config['resume']['filename']
    except KeyError:
        resume_filename = None
    return resume_filename

def can_resume_or_continue(resume, play_file):
    if resume:
        try:
            resume_file = pathlib.Path(load_resume_filename())
        except TypeError:
            pass
        else:
            if resume_file.is_file() and not resume_file.samefile(play_file):
                return False

    return True

def get_commandline_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('filename')
    parser.add_argument('-t', '--title', default=TITLE)
    parser.add_argument('-fs', '--full-screen', action='store_true')
    parser.add_argument('-ff', '--fast-forward', type=int, default=FF_SECONDS)
    parser.add_argument('-fr', '--fast-rewind', type=int, default=FR_SECONDS)
    parser.add_argument('-r', '--resume', action='store_true')
    args = parser.parse_args()
    return args.filename, args.title, args.full_screen, args.fast_forward, args.fast_rewind, args.resume

def main():
    # command line options
    filename, title, fullscreen, ff, fr, resume = get_commandline_arguments()

    # check file exists
    play_file = pathlib.Path(filename)
    if not play_file.is_file():
        print(f"Error: File '{filename}' does not exist!")
        exit(1)

    # check resume conditions
    if not can_resume_or_continue(resume, play_file):
        print(f"Not resume file '{filename}'...")
        exit(0)

    # init
    player = vlc.MediaPlayer(filename) # https://www.olivieraubert.net/vlc/python-ctypes/doc/vlc.MediaPlayer-class.html
    root = tk.Tk()
    context = PlayerContext(root=root, player=player, filename=filename, progress=tk.IntVar(), job=None)

    # callbacks
    playback_callback = partial(toggle_playback, player=player)
    stop_callback = partial(stop, context=context)
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

    progressbar = ttk.Progressbar(variable=context.progress)
    progressbar.grid(row=1, column=0, columnspan=3, sticky="SEW")

    if fullscreen:
        root.attributes('-fullscreen', True)
    else:
        root.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}+0+0")

        tk.Button(root, text="Play/Pause", fg="green",
            command=playback_callback).grid(row=2, column=0, sticky="SEW")
        tk.Button(root, text="Stop/Quit", fg="blue",
            command=stop_callback).grid(row=2, column=1, sticky="SEW")
        tk.Button(root, text="Delete", fg="red",
            command=delete_callback).grid(row=2, column=2, sticky="SEW")

    # key bindings
    root.bind('<Right>', lambda event: forward_callback())
    root.bind('<Left>', lambda event: rewind_callback())
    root.bind("<space>", lambda event: playback_callback())
    root.bind("<q>", lambda event: stop_callback())
    root.bind("<Escape>", lambda event: stop_callback())

    # start
    print(f"Now playing '{filename}'...")
    started = player.play()
    if started == -1:
        print(f"Error: Could not play file '{filename}'!")
        exit(1)

    context.job = root.after(PROGRESS_INTERVAL, lambda: update_progress(context))
    root.focus_set()
    root.mainloop()

if __name__ == '__main__':
    main()
