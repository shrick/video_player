# AudioVideo

import pathlib

import vlc # https://www.olivieraubert.net/vlc/python-ctypes/doc/vlc.MediaPlayer-class.html

import ctypes
ctypes.CDLL('libX11.so.6').XInitThreads()

class PlaybackException(Exception):
    pass

class AudioVideo:
    def __init__(self) -> None:
        self._player = vlc.MediaPlayer()
        self._stopped = True

    def set_video_widget_id(self, widget_id: int):
        self._player.set_xwindow(widget_id)

    def play(self, videofile: pathlib.Path, volume: int) -> None:
        self.stop()
        if volume is not None:
            self._player.audio_set_volume(max(0, min(volume, 100)))
        self._player.set_media(self._player.get_instance().media_new_path(videofile))

        started = self._player.play()
        if started == -1:
            raise PlaybackException("Could not start file '{videofile}")
        self._stopped = False

        print(f"Now playing '{videofile}'...")

    def toggle(self) -> bool:
        if not self._stopped:
            self._player.set_pause(self._player.is_playing())
            return True

        return False

    def move(self, seconds: int) -> int:
        if not self._stopped:
            vtime = self._player.get_time()
            vlen = self._player.get_length()
            new_time = max(0, min(vlen, vtime + seconds * 1_000))
            return self._player.set_time(new_time)

        return 0

    def stop(self) -> None:
        if not self._stopped:
            self._player.stop()
            self._stopped = True

    def get_state(self):
        if not self._stopped:
            vtime = self._player.get_time()
            vlen = self._player.get_length()
            vpos = self._player.get_position()
            return vtime, vlen, vpos

        return None
