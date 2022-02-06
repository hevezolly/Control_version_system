from enum import Enum
import os
import shutil
import struct

ENCODING = "utf8"


class DCT(Enum):
    ADD_FILE = 0
    REMOVE_FILE = 1
    RENAME = 2
    ADD_DIR = 3
    REMOVE_DIR = 4


class DirChange:
    def __init__(self, file_name, change_type, new_name=None):
        if change_type == DCT.RENAME and new_name is None:
            raise ValueError(
                f"to rename file {file_name} new_name should be given")
        self.type = change_type
        self.name = file_name
        self.new_name = new_name

    @staticmethod
    def from_bytes(b, start_index=0):
        t = DCT(struct.unpack("b", b[start_index:start_index + 1])[0])
        start_index += 1
        name_len = struct.unpack("i", b[start_index: start_index + 4])[0]
        start_index += 4
        name = b[start_index: start_index + name_len].decode(ENCODING)
        start_index += name_len
        new_name_len = struct.unpack("i", b[start_index:start_index + 4])[0]
        start_index += 4
        if new_name_len == 0:
            return DirChange(name, t)
        new_name = b[start_index:start_index + new_name_len].decode(ENCODING)
        return DirChange(name, t, new_name)

    def apply_to_dir(self, directory):
        origin = os.path.join(directory, self.name)
        if self.type == DCT.ADD_FILE:
            open(origin, "w+").close()

        elif self.type == DCT.REMOVE_FILE:
            if not os.path.isfile(origin):
                raise FileNotFoundError("no such file")
            os.remove(origin)

        elif self.type == DCT.RENAME:
            new_origin = os.path.join(directory, self.new_name)
            if not os.path.isfile(origin) and not os.path.isdir(origin):
                raise FileNotFoundError("no such file or directory")
            if os.path.isfile(new_origin) or os.path.isdir(new_origin):
                raise FileExistsError(f'file {new_origin} is already exists')
            os.rename(origin, new_origin)

        elif self.type == DCT.ADD_DIR:
            os.mkdir(origin)

        elif self.type == DCT.REMOVE_DIR:
            if not os.path.isdir(origin):
                raise FileNotFoundError("no such directory")
            while 1:
                try:
                    shutil.rmtree(origin)
                    break
                except OSError:
                    continue

    def revert(self, directory):
        origin = os.path.join(directory, self.name)
        if self.type == DCT.ADD_FILE:
            if not os.path.isfile(origin):
                raise FileNotFoundError("no such file")
            os.remove(origin)

        elif self.type == DCT.REMOVE_FILE:
            open(origin, "w+").close()

        elif self.type == DCT.RENAME:
            new_origin = os.path.join(directory, self.new_name)
            if not os.path.isfile(new_origin) and not os.path.isdir(
                    new_origin):
                raise FileNotFoundError("no such file or directory")
            if os.path.isfile(origin) or os.path.isdir(origin):
                raise FileExistsError(f'file {origin} is already exists')
            os.rename(new_origin, origin)

        elif self.type == DCT.ADD_DIR:
            if not os.path.isdir(origin):
                raise FileNotFoundError("no such directory")
            while True:
                try:
                    shutil.rmtree(origin)
                    break
                except OSError:
                    continue

        elif self.type == DCT.REMOVE_DIR:
            os.mkdir(origin)

    def encode(self):
        type_b = struct.pack("b", self.type.value)
        name_b = self.name.encode(ENCODING)
        name_len = struct.pack("i", len(name_b))
        new_name_b = bytes()
        new_name_len = struct.pack("i", 0)
        if self.new_name is not None:
            new_name_b = self.new_name.encode(ENCODING)
            new_name_len = struct.pack("i", len(new_name_b))
        return type_b + name_len + name_b + new_name_len + new_name_b

    def copy(self):
        return DirChange(self.name, self.type, self.new_name)
