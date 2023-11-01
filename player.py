# Video Player

from player.playlist import Playlist
from player.control import Controller
from player.ui import UserInterface

import argparse

TITLE = "Shrick Video Player"
FF_SECONDS = 10
FR_SECONDS = 5

def get_commandline_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('dirname')
    parser.add_argument('-t', '--title', default=TITLE)
    parser.add_argument('-r', '--resume', action='store_true')
    parser.add_argument('-w', '--wait', action='store_true')
    parser.add_argument('-fs', '--full-screen', action='store_true')
    parser.add_argument('-ff', '--fast-forward', type=int, default=FF_SECONDS)
    parser.add_argument('-fr', '--fast-rewind', type=int, default=FR_SECONDS)
    parser.add_argument('-av', '--audio-volume', type=int, default=None)

    args = parser.parse_args()
    return (args.dirname, args.title,
        args.resume, args.wait, args.full_screen,
        args.fast_forward, args.fast_rewind, args.audio_volume)

def main():
    # evaluate command line options
    dirname, title, resume, wait, fullscreen, ff, fr, volume = get_commandline_arguments()

    # setup
    playlist = Playlist(dirname, resume)
    controller = Controller(playlist, volume, ff, fr, wait)
    ui = UserInterface(title, fullscreen, controller)

    # start
    print(f"Resuming file {playlist.get_current_file()} ...")
    ui.start()

if __name__ == '__main__':
    main()
