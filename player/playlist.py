# Playlist

import pathlib
import configparser

CONFIG_FILENAME = "player.ini"

class Playlist:
    def __init__(self, root: str, resume: bool) -> None:
        self._root = pathlib.Path(root)
        if not self._root.is_dir():
            raise NotADirectoryError(f"Directory '{root}' does not exist!")
        self._files = self._collect_files(self._root)

        # setup next file to play
        resume_file = self._load_resume_file() if resume else None
        if resume_file and resume_file in self._files:
            self._current = resume_file
        elif len(self._files):
            self._current = self._files[0]
        else:
            self._current = None

    def _collect_files(self, vdir: pathlib.Path) -> list[pathlib.Path]:
        result = []

        for p in vdir.iterdir():
            if p.is_dir():
                result.extend(self._collect_files(p))
            elif p.is_file():
                if p.name != CONFIG_FILENAME:
                    result.append(p)

        return sorted(result)

    def _load_resume_file(self):
        config = configparser.ConfigParser()
        config.read(self._root / CONFIG_FILENAME)

        try:
            resume_file = pathlib.Path(config['resume']['filename'])
        except KeyError:
            pass
        else:
            if resume_file.is_file():
                return resume_file

        return None

    def save_resume_file(self) -> None:
        if self._current is not None:
            config = configparser.ConfigParser()
            config['resume'] = { 'filename': str(self._current) }
            with open(self._root / CONFIG_FILENAME, 'w') as configfile:
                config.write(configfile)

    def get_current_file(self) -> pathlib.Path:
        return self._current

    def _skip(self, offset, delete_current=False) -> bool:
        if offset == 0:
            return False

        files_count = len(self._files)
        if files_count < 2:
            return False

        try:
            old_index = self._files.index(self._current)
            old_file = self._current
        except IndexError:
            return False

        new_index = old_index + offset
        if new_index == files_count:
            # next rollover (offset > 0)
            new_index = offset - 1
        elif new_index < 0:
            # prev rollover (offset < 0)
            new_index = files_count + offset
        self._current = self._files[new_index]

        if delete_current or not old_file.exists():
            try:
                old_file.unlink(missing_ok=True)
                self._files.remove(old_file)
            except ValueError:
                pass

        return True

    def next(self, skip=1, delete_current=False) -> bool:
        return self._skip(skip, delete_current)

    def prev(self, skip=1, delete_current=False) -> bool:
        return self._skip(-skip, delete_current)
