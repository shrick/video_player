# VideoControl

import pathlib

import vlc # https://www.olivieraubert.net/vlc/python-ctypes/doc/vlc.MediaPlayer-class.html

class AudioVideo:
    def __init__(self, videofile: pathlib.Path, widget_id: int, volume: int) -> None:
        self._videofile = videofile
        self._player = vlc.MediaPlayer(str(self._videofile))
        self._player.set_xwindow(widget_id)
        if volume is not None:
            self._player.audio_set_volume(max(0, min(volume, 100)))

    def play(self) -> None:
        started = self._player.play()
        if started == -1:
            print(f"Error: Could not start file '{self._videofile}'!")
            exit(3)
        print(f"Now playing '{self._videofile}'...")

    def toggle(self) -> None:
        self._player.set_pause(self._player.is_playing())

    def move(self, seconds: int) -> int:
        vtime = self._player.get_time()
        vlen = self._player.get_length()
        new_time = max(0, min(vlen, vtime + seconds * 1_000))
        return self._player.set_time(new_time)

    def stop(self) -> None:
        self._player.stop()
        self._player.release()
        self._player = None

    def get_state(self):
        vtime = self._player.get_time()
        vlen = self._player.get_length()
        vpos = self._player.get_position()
        return vtime, vlen, vpos
