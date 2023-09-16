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
PROGRESS_INTERVAL_MS = int(0.25 * 1_000)
END_TOLERANCE_MS = 300
CONFIG_FILENAME = "player.ini"
ABORT_EXIT_CODE=23

@dataclass(init=True)
class PlayerContext:
    root: tk.Tk = None
    player: vlc.MediaPlayer = None
    filename: str = None
    progress: ... = None
    last_time: ... = None
    job: ... = None

def start_playback(context: PlayerContext, volume: int):
    if volume is not None:
        context.player.audio_set_volume(max(0, min(volume, 100)))
    started = context.player.play()
    if started == -1:
        print(f"Error: Could not play file '{context.filename}'!")
        exit(4)
    print(f"Now playing '{context.filename}'...")
    context.job = context.root.after(PROGRESS_INTERVAL_MS, lambda: update_progress(context))

def update_progress(context: PlayerContext):
    new_time = context.player.get_time()
    if (new_time == context.last_time) and (context.player.get_length() - new_time < END_TOLERANCE_MS):
        stop(context)
    else:
        context.progress.set(context.player.get_position() * 100)
        context.last_time = new_time
        context.job = context.root.after(PROGRESS_INTERVAL_MS, lambda: update_progress(context))

def toggle_playback(player: vlc.MediaPlayer):
    player.set_pause(player.is_playing())

def forward(context: PlayerContext, seconds: int):
    new_time = min(context.player.get_length(), context.player.get_time() + seconds * 1_000)
    context.player.set_time(new_time)
    context.last_time = new_time

def rewind(context: PlayerContext, seconds: int):
    new_time = max(0, context.player.get_time() - seconds * 1_000)
    context.player.set_time(new_time)
    context.last_time = new_time

def stop(context: PlayerContext, abort: bool=False, delete: bool=False):
    if context.job is not None:
        context.root.after_cancel(context.job)
        context.job = None
    context.player.stop()
    context.player.release()
    if delete:
        delete_file(context.filename)
    context.root.destroy()
    if abort:
        print(f"Abort, saving resume file '{context.filename}'...")
        save_resume_filename(context.filename)
        exit(ABORT_EXIT_CODE)
    else:
        save_resume_filename(None)

def delete_file(filename: str):
    yes = askyesno(title="Confirmation", message=f"Really delete file '{filename}'?")
    if yes:
        print(f"Deleting file '{filename}'...")
        file = pathlib.Path(filename)
        file.unlink(missing_ok=True)

def save_resume_filename(resume_filename: str):
    if resume_filename is not None:
        config = configparser.ConfigParser()
        config['resume'] = { 'filename': resume_filename }
        with open(CONFIG_FILENAME, 'w') as configfile:
            config.write(configfile)
    else:
        pathlib.Path(CONFIG_FILENAME).unlink(missing_ok=True)

def load_resume_filename():
    config = configparser.ConfigParser()
    config.read(CONFIG_FILENAME)
    try:
        resume_filename = config['resume']['filename']
    except KeyError:
        resume_filename = None
    return resume_filename

def can_resume_or_continue(resume: bool, play_file: str):
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
    parser.add_argument('-r', '--resume', action='store_true')
    parser.add_argument('-fs', '--full-screen', action='store_true')
    parser.add_argument('-ff', '--fast-forward', type=int, default=FF_SECONDS)
    parser.add_argument('-fr', '--fast-rewind', type=int, default=FR_SECONDS)
    parser.add_argument('-av', '--audio-volume', type=int, default=None)

    args = parser.parse_args()
    return (args.filename, args.title,
        args.resume, args.full_screen,
        args.fast_forward, args.fast_rewind, args.audio_volume)

def main():
    # command line options
    filename, title, resume, fullscreen, ff, fr, av = get_commandline_arguments()

    # check file exists
    play_file = pathlib.Path(filename)
    if not play_file.is_file():
        print(f"Error: File '{filename}' does not exist!")
        exit(1)

    # check resume conditions
    if not can_resume_or_continue(resume, play_file):
        print(f"Not resume file '{filename}'...")
        exit(2)

    # init
    player = vlc.MediaPlayer(filename) # https://www.olivieraubert.net/vlc/python-ctypes/doc/vlc.MediaPlayer-class.html
    root = tk.Tk()
    context = PlayerContext(root=root, player=player, filename=filename, progress=tk.IntVar(), last_time=-1, job=None)

    # callbacks
    playback_callback = partial(toggle_playback, player=player)
    stop_callback = partial(stop, context=context)
    delete_callback = partial(stop_callback, delete=True)
    abort_callback = partial(stop_callback, abort=True)
    forward_callback = partial(forward, context=context, seconds=ff)
    rewind_callback = partial(rewind, context=context, seconds=fr)

    # controls
    root.title(f"{title} ({filename})")
    tk.Grid.rowconfigure(root, 0, weight=1)
    tk.Grid.rowconfigure(root, 1, weight=0)
    tk.Grid.columnconfigure(root, 0, weight=1)
    tk.Grid.columnconfigure(root, 1, weight=1)
    tk.Grid.columnconfigure(root, 2, weight=1)

    video = tk.Frame(root, bg='black')
    video.grid(row=0, column=0, columnspan=3, sticky="NSEW")
    player.set_xwindow(video.winfo_id())

    progressbar = ttk.Progressbar(variable=context.progress)
    progressbar.grid(row=1, column=0, columnspan=3, sticky="SEW")

    if fullscreen:
        root.attributes('-fullscreen', True)
        root.lift()
        root.focus_force()
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
    root.bind("<Escape>", lambda event: stop_callback())
    root.bind("<d>", lambda event: delete_callback())
    root.bind("<a>", lambda event: abort_callback())

    # start
    start_playback(context, av)
    root.mainloop()

if __name__ == '__main__':
    main()
