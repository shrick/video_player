# Controller

from player.playlist import Playlist
from player.av import AudioVideo

from typing import Callable

PROGRESS_INTERVAL_MS = int(0.25 * 1_000)
END_TOLERANCE_MS = 300

class Controller:
    def __init__(self, playlist: Playlist, volume: int, ff: int, fr: int, wait: bool) -> None:
        self._playlist: Playlist = playlist
        self._volume = volume
        self._ff = ff
        self._fr = fr
        self._wait = wait
        self._av: AudioVideo = None
        self._ui = None

    def register_ui(self, ui) -> Callable:
        self._ui = ui
        return self.start_playback

    def start_playback(self) -> None:
        play_file = self._playlist.get_current_file()
        if play_file is None or not play_file.is_file():
            print(f"Error: Could not open file '{play_file}'!")
            self.stop()
        else:
            self._av = AudioVideo(play_file, self._ui.get_video_widget_id(), self._volume, autoplay=True)
            self._ui.set_caption(play_file)
            self._update_progress(restart=True)

    def _update_progress(self, restart: bool=False) -> None:
        if restart:
            self._last_time = -1

        if self._av is not None:
            new_time, vlen, vpos = self._av.get_state()

            self._ui.set_progress(vpos * 100)
            if not self._wait and (new_time == self._last_time) and (vlen - new_time < END_TOLERANCE_MS):
                self.next_video()
            self._last_time = new_time
            self._cancel_action = self._ui.schedule_action(PROGRESS_INTERVAL_MS, self._update_progress)

    def toggle_playback(self) -> None:
        if self._av is not None:
            self._av.toggle()
        else:
            self.start_playback()

    def fast_forward(self) -> None:
        if self._av is not None:
            self._last_time = self._av.move(self._ff)

    def fast_rewind(self) -> None:
        if self._av is not None:
            self._last_time = self._av.move(-self._fr)

    def _skip_video(self, next: bool, delete_current: bool=False, continue_playback: bool=True) -> None:
        playlist_skip = self._playlist.next if next else self._playlist.prev
        if playlist_skip(delete_current=delete_current):
            self._stop_playback()
            if continue_playback:
                self.start_playback()

    def next_video(self, delete_current: bool=False, continue_playback: bool=True) -> None:
        self._skip_video(next=True, delete_current=delete_current, continue_playback=continue_playback)

    def prev_video(self) -> None:
        self._skip_video(next=False)

    def delete(self) -> None:
        self._stop_playback()
        play_file = self._playlist.get_current_file()
        if self._ui.question_dialog(title="Confirmation", message=f"Really delete file '{play_file}'?"):
            print(f"Deleting file '{play_file}'...")
            self.next_video(delete_current=True, continue_playback=not self._wait)
        elif not self._wait:
            self.start_playback()

    def abort(self) -> None:
        self.stop()
        print(f"Abort, saving resume file '{self._playlist.get_current_file()}'...")
        self._playlist.save_resume_file()

    def stop(self) -> None:
        self._stop_playback()
        self._ui.quit()

    def _stop_playback(self) -> None:
        if self._av is not None:
            self._cancel_action()
            self._av.stop()
            self._av = None
