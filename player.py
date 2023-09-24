# Video Player

import argparse
import pathlib
from functools import partial
from dataclasses import dataclass
import configparser
import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import askyesno
import vlc # https://www.olivieraubert.net/vlc/python-ctypes/doc/vlc.MediaPlayer-class.html

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
    video_frame: tk.Frame = None
    title: str = None
    wait: bool = False
    volume: int = None
    play_dir_list: list[pathlib.Path] = None
    play_file: str = None
    progress: ... = None
    last_time: int = -1
    job: ... = None

def start_playback(context: PlayerContext, play_file: pathlib.Path) -> None:
    if play_file is None or not play_file.is_file():
        print(f"Error: Could not open file '{play_file}'!")
        exit(2)

    context.play_file = play_file
    context.player = vlc.MediaPlayer(str(context.play_file))
    context.player.set_xwindow(context.video_frame.winfo_id())

    if context.volume is not None:
        context.player.audio_set_volume(max(0, min(context.volume, 100)))

    started = context.player.play()
    if started == -1:
        print(f"Error: Could not start file '{context.play_file}'!")
        exit(3)
    print(f"Now playing '{context.play_file}'...")

    context.root.title(f"{context.title} ({str(context.play_file)})")
    context.job = context.root.after(PROGRESS_INTERVAL_MS, lambda: update_progress(context))

def update_progress(context: PlayerContext) -> None:
    new_time = context.player.get_time()
    if (new_time == context.last_time) and (context.player.get_length() - new_time < END_TOLERANCE_MS):
        if not context.wait:
            next(context)
    else:
        context.progress.set(context.player.get_position() * 100)
        context.last_time = new_time
        context.job = context.root.after(PROGRESS_INTERVAL_MS, lambda: update_progress(context))

def toggle_playback(context: PlayerContext) -> None:
    if context.job is not None:
        context.player.set_pause(context.player.is_playing())

def forward(context: PlayerContext, seconds: int) -> None:
    if context.job is not None:
        new_time = min(context.player.get_length(), context.player.get_time() + seconds * 1_000)
        context.player.set_time(new_time)
        context.last_time = new_time

def rewind(context: PlayerContext, seconds: int) -> None:
    if context.job is not None:
        new_time = max(0, context.player.get_time() - seconds * 1_000)
        context.player.set_time(new_time)
        context.last_time = new_time

def cleanup_player(context: PlayerContext):
    if context.job is not None:
        context.root.after_cancel(context.job)
        context.job = None
        context.player.stop()
        context.player.release()
        context.player = None
        context.last_time = -1
        context.progress.set(0)

    if not context.play_file.exists():
        try:
            context.play_dir_list.remove(context.play_file)
        except ValueError:
            pass

def next(context: PlayerContext):
    # find next file
    try:
        index = context.play_dir_list.index(context.play_file) + 1
        if index == len(context.play_dir_list):
            index = 0
        next_play_file = context.play_dir_list[index]
    except IndexError:
        # no next file available
        return
    else:
        # restart playback
        cleanup_player(context)
        start_playback(context, next_play_file)

def prev(context: PlayerContext):
    # find prev file
    try:
        index = context.play_dir_list.index(context.play_file)
        prev_play_file = context.play_dir_list[index - 1]
    except IndexError:
        # no prev file available
        return
    else:
        # restart playback
        cleanup_player(context)
        start_playback(context, prev_play_file)

def delete(context: PlayerContext) -> None:
    cleanup_player(context)
    yes = askyesno(title="Confirmation", message=f"Really delete file '{context.play_file}'?")
    if yes:
        print(f"Deleting file '{context.play_file}'...")
        context.play_file.unlink(missing_ok=True)

def stop(context: PlayerContext, abort: bool=False, abort_exitcode=ABORT_EXIT_CODE) -> None:
    cleanup_player(context)
    context.root.destroy()
    if abort:
        print(f"Abort, saving resume file '{context.play_file}'...")
        save_resume_filename(context.play_file)
        exit(abort_exitcode)
    else:
        save_resume_filename(None)

def save_resume_filename(resume_file: pathlib.Path) -> None:
    if resume_file is not None:
        config = configparser.ConfigParser()
        config['resume'] = { 'filename': str(resume_file) }
        with open(CONFIG_FILENAME, 'w') as configfile:
            config.write(configfile)
    else:
        pathlib.Path(CONFIG_FILENAME).unlink(missing_ok=True)

def load_resume_filename() -> str:
    config = configparser.ConfigParser()
    config.read(CONFIG_FILENAME)
    try:
        resume_filename = config['resume']['filename']
    except KeyError:
        resume_filename = None
    return resume_filename

def get_resume_file(resume: bool, play_dir_list: list) -> bool:
    if resume:
        try:
            resume_file = pathlib.Path(load_resume_filename())
        except TypeError:
            pass
        else:
            if resume_file.is_file() and resume_file in play_dir_list:
                return resume_file

    return None

def build_play_dir_list(play_dir: pathlib.Path):
    result = []

    for p in play_dir.iterdir():
        if p.is_dir():
            result.extend(build_play_dir_list(p))
        elif p.is_file():
            result.append(p)

    return sorted(result)

def get_commandline_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('dirname')
    parser.add_argument('-t', '--title', default=TITLE)
    parser.add_argument('-r', '--resume', action='store_true')
    parser.add_argument('-w', '--wait', action='store_true')
    parser.add_argument('-a', '--abort-exitcode', type=int, default=ABORT_EXIT_CODE)
    parser.add_argument('-fs', '--full-screen', action='store_true')
    parser.add_argument('-ff', '--fast-forward', type=int, default=FF_SECONDS)
    parser.add_argument('-fr', '--fast-rewind', type=int, default=FR_SECONDS)
    parser.add_argument('-av', '--audio-volume', type=int, default=None)

    args = parser.parse_args()
    return (args.dirname, args.title,
        args.resume, args.wait, args.abort_exitcode, args.full_screen,
        args.fast_forward, args.fast_rewind, args.audio_volume)

def main():
    # command line options
    dirname, title, resume, wait, abort_exitcode, fullscreen, ff, fr, av = get_commandline_arguments()

    # check directory exists
    play_dir = pathlib.Path(dirname)
    if not play_dir.is_dir():
        print(f"Error: Directory '{dirname}' does not exist!")
        exit(1)

    # collect all files from directory
    play_dir_list = build_play_dir_list(play_dir)

    # resume or start
    play_file = get_resume_file(resume, play_dir_list)
    if play_file is None and len(play_dir_list):
        play_file = play_dir_list[0]
    else:
        print(f"Resuming file {play_file} ...")

    # init
    root = tk.Tk()
    context = PlayerContext(root=root, title=title, wait=wait, volume=av, play_dir_list=play_dir_list, progress=tk.IntVar())

    # controls
    tk.Grid.rowconfigure(root, 0, weight=1)
    tk.Grid.rowconfigure(root, 1, weight=0)
    tk.Grid.columnconfigure(root, 0, weight=1)
    tk.Grid.columnconfigure(root, 1, weight=1)
    tk.Grid.columnconfigure(root, 2, weight=1)

    video = tk.Frame(root, bg='black')
    video.grid(row=0, column=0, columnspan=3, sticky="NSEW")
    context.video_frame = video

    progressbar = ttk.Progressbar(variable=context.progress)
    progressbar.grid(row=1, column=0, columnspan=3, sticky="SEW")

    # widget callbacks
    playback_callback = partial(toggle_playback, context=context)
    stop_callback = partial(stop, context=context, abort_exitcode=max(ABORT_EXIT_CODE, abort_exitcode))
    next_callback = partial(next, context=context)
    prev_callback = partial(prev, context=context)
    delete_callback = partial(delete, context=context)
    abort_callback = partial(stop_callback, abort=True)
    forward_callback = partial(forward, context=context, seconds=ff)
    rewind_callback = partial(rewind, context=context, seconds=fr)

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
    root.bind("<Prior>", lambda event: prev_callback())
    root.bind("<Next>", lambda event: next_callback())
    root.bind("<Escape>", lambda event: next_callback())
    root.bind("<q>", lambda event: stop_callback())
    root.bind("<d>", lambda event: delete_callback())
    root.bind("<a>", lambda event: abort_callback())

    # start
    start_playback(context, play_file)
    root.mainloop()

if __name__ == '__main__':
    main()
