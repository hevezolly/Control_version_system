from enum import Enum
import struct
from CVSysModules.dir_change import ENCODING
import os


BUFFER_SIZE = 512


class FCT(Enum):
    INSERT = 0
    DELETE = 1
    COPY = 2


class FileChange:
    def __init__(self, index, data, change_type):
        self.type = change_type
        self.index = index
        self.data = data
        if type(data) is int and change_type == FCT.DELETE:
            self.data = struct.pack("i", data)
        if type(data) is str and change_type == FCT.COPY:
            self.data = data.encode(ENCODING)

    def get_index_length(self):
        length = 0
        index = self.index
        if self.type == FCT.INSERT:
            length = len(self.data)
        elif self.type == FCT.DELETE:
            length, = struct.unpack('i', self.data)
        elif self.type == FCT.COPY:
            index = 0
            length = os.path.getsize(self.data.decode(ENCODING))
        return index, length

    @staticmethod
    def from_bytes(b, start_index=0):
        t, = struct.unpack("b", b[start_index: start_index + 1])
        index, = struct.unpack("i", b[start_index + 1: start_index + 5])
        length, = struct.unpack("i", b[start_index + 5: start_index + 9])
        data = b[start_index + 9: start_index + 9 + length]
        real_type = FCT(t)
        return FileChange(index, data, real_type)

    def apply_to_file(self, file_name):
        if not os.path.isfile(file_name):
            raise FileNotFoundError(f'no such file, as {file_name}')
        if self.type == FCT.INSERT:
            self._apply_insert(file_name)
        elif self.type == FCT.DELETE:
            self._apply_delete(file_name)
        elif self.type == FCT.COPY:
            self._apply_copy(file_name)
        else:
            raise ValueError("wrong type")

    def _apply_insert(self, file_name):
        if self.type != FCT.INSERT:
            raise TypeError("can not apply change")
        with open(file_name, "rb+") as file:
            data = bytearray(self.data)
            file.seek(self.index)
            for c in data:
                new = file.read(1)
                if not new == b'':
                    data.extend(bytearray(new))
                    file.seek(-1, 1)
                file.write(c.to_bytes(1, "big"))
            file.truncate()

    def _apply_delete(self, file_name):
        if self.type != FCT.DELETE:
            raise TypeError("can not apply change")
        bytes_num, = struct.unpack("i", self.data)
        with open(file_name, "rb+") as file:
            i = 0
            while 1:
                file.seek(i + self.index + bytes_num)
                b = file.read(1)
                file.seek(self.index + i)
                if b == b'':
                    file.truncate()
                    return
                file.write(b)
                i += 1

    def _apply_copy(self, file_name):
        if self.type != FCT.COPY:
            raise TypeError("can not apply change")
        origin = self.data.decode(ENCODING)
        if not os.path.isfile(origin):
            raise FileNotFoundError(f"no such file as {origin}")
        with open(origin, 'rb') as source:
            with open(file_name, 'wb') as dest:
                data = source.read(BUFFER_SIZE)
                while data:
                    dest.write(data)
                    data = source.read(BUFFER_SIZE)

    def encode(self):
        b_type = struct.pack("b", self.type.value)
        b_index = struct.pack("i", self.index)
        b_length = struct.pack("i", len(self.data))
        return b_type + b_index + b_length + self.data

    def copy(self):
        return FileChange(self.index, self.data, self.type)
