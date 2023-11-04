# Video Player

Simple VLC and Tkinter based video player

# SYNOPSIS

```
player.py [-h] [-t TITLE] [-r] [-w] [-fs] [-ff FAST_FORWARD] [-fr FAST_REWIND] [-av AUDIO_VOLUME] dirname
```

# Description

Video player to prepare and perform video playback of all video files below a given directory. Can be started in fullscreen mode (`-fs`) displaying only a caption and a progress bar around the video or in window mode with additional control buttons.

With `-w` option next video will not automatically played, instead it waits/pauses at the end of each video so you can screen and sort out video files without hurry.

With `-r` option playback is resumed with the video file the last session was aborted. The resume configuration is saved directly below the passed video directory in a `player.ini` file and only written on abort, i.e. quitting the application normally will neither change nor delete the resume configuration.

# Key bindings

The following key bindings allow control via keyboard and wireless presenter devices:

| Key(s)            | Action |
| ----------------- | ------ |
| Cursor left, b    | Fast rewind |
| Cursor right      | Fast forward |
| Space, Escape, F5 | Toggle play/pause |
| Page up           | Previous video |
| Page down         | Next video |
| d                 | Delete current video file |
| q                 | Quit |
| a                 | Abort (quit with saving resume configuration) |

# Dependencies

* Python 3 (v3.10.12 used for development)
* [python-vlc](https://pypi.org/project/python-vlc/) (Python VLC bindings)
* VLC (at least the basic binaries w/o GUI support)
