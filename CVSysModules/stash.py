import json
import shutil
import os
from CVSysModules.file_change import BUFFER_SIZE

JSON_NAME = 'stash_info.json'
STASH_PATH = '.stash'


class Stash:
    def __init__(self, path, create_new=False):
        self._json_path = os.path.join(path, JSON_NAME)
        self._stash_path = os.path.join(path, STASH_PATH)

        if not os.path.exists(self._json_path):
            open(self._json_path, 'w').close()
            create_new = True

        if not os.path.exists(self._stash_path):
            os.mkdir(self._stash_path)
            create_new = True

        self.content = {}
        if create_new:
            self._clear_dir()
            self.dump()
        else:
            self.load()

    def _clear_dir(self):
        while 1:
            try:
                shutil.rmtree(self._stash_path)
                break
            except OSError:
                continue
        os.mkdir(self._stash_path)

    def dump(self):
        data = {'content': self.content}
        with open(self._json_path, 'w') as file:
            json.dump(data, file, indent=4)

    def load(self):
        with open(self._json_path, 'r') as file:
            data = json.load(file)
        self.content = data['content']

    def add_file(self, file_path, name_to_stash, commit_index, delete=False):
        if name_to_stash in self.content and not delete:
            raise ValueError("file is already in stash")
        stashed_path = os.path.join(self._stash_path, name_to_stash)
        self.content[name_to_stash] = {'path': stashed_path,
                                       'old_path': file_path,
                                       'index': commit_index}
        self.copy(file_path, stashed_path)
        self.dump()

    @staticmethod
    def copy(sourse, dest):
        with open(dest, 'wb') as d:
            with open(sourse, 'rb') as s:
                data = s.read(BUFFER_SIZE)
                while data:
                    d.write(data)
                    data = s.read(BUFFER_SIZE)

    def delete_file(self, stash_name):
        if stash_name not in self.content:
            raise ValueError(f"file {stash_name} was not found")
        os.remove(self.content[stash_name]['path'])
        self.content.pop(stash_name)
        self.dump()

    def restore(self, stash_name, path_to_restore, delete=False):
        if stash_name not in self.content:
            raise ValueError(f'no such name as {stash_name}')
        stashed_path = self.content[stash_name]['path']
        self.copy(stashed_path, path_to_restore)
        if delete:
            self.delete_file(stash_name)

    def clear(self):
        self.content = {}
        self._clear_dir()
        self.dump()
