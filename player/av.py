# AudioVideo

import pathlib

import vlc # https://www.olivieraubert.net/vlc/python-ctypes/doc/vlc.MediaPlayer-class.html

import ctypes
ctypes.CDLL('libX11.so.6').XInitThreads()

MARQUEE_OPTION_ENABLE = 1
MARQUEE_OPTION_DISABLE = 0
MARQUEE_OPTION_POSITION_BOTTOM = 8
MARQUEE_PIXEL_RATIO = 0.05

class PlaybackException(Exception):
    pass

class AudioVideo:
    def __init__(self, marquee_timeout: int | None) -> None:
        instance = vlc.Instance(["--sub-source=marq"])
        self._player = instance.media_player_new()
        self._stopped = True
        self._marquee_timeout = marquee_timeout

    def set_video_widget_id(self, widget_id: int):
        self._player.set_xwindow(widget_id)

    def play(self, videofile: pathlib.Path, volume: int, marquee_text: str | None) -> None:
        self.stop()
        media = self._player.get_instance().media_new_path(videofile)
        self._player.set_media(media)
        media.parse()
        if volume is not None:
            self._player.audio_set_volume(max(0, min(volume, 100)))

        # marquee
        if self._marquee_timeout is not None and marquee_text is not None:
            video_height = self._player.video_get_height()
            marquee_height = int(video_height * MARQUEE_PIXEL_RATIO)
            self._player.video_set_marquee_string(vlc.VideoMarqueeOption.Text, vlc.str_to_bytes(marquee_text))
            self._player.video_set_marquee_int(vlc.VideoMarqueeOption.Size, marquee_height) # pixels
            self._player.video_set_marquee_int(vlc.VideoMarqueeOption.Timeout, self._marquee_timeout * 1_000) # milliseconds
            self._player.video_set_marquee_int(vlc.VideoMarqueeOption.Position, MARQUEE_OPTION_POSITION_BOTTOM)
            self._player.video_set_marquee_int(vlc.VideoMarqueeOption.Enable, MARQUEE_OPTION_ENABLE)
        else:
            self._player.video_set_marquee_int(vlc.VideoMarqueeOption.Enable, MARQUEE_OPTION_DISABLE)

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
