from CVSysModules.file_change import FileChange
from CVSysModules.dir_change import DirChange, ENCODING, DCT
import os
import struct


class ChangeStep:
    def __init__(self, target, change, is_binary):
        if not isinstance(change, FileChange) and not isinstance(change,
                                                                 DirChange):
            raise ValueError("incorrect change")
        self.target = target
        self.change = change
        self.is_binary = is_binary

    @property
    def can_be_reverted(self):
        return isinstance(self.change, DirChange)

    def revert(self, origin):
        if not self.can_be_reverted:
            raise TypeError("can't revert file change")
        target = os.path.join(origin, self.target)
        self.change.revert(target)

    @staticmethod
    def from_bytes(b, start_index=0):
        is_dir, = struct.unpack("?", b[start_index: start_index + 1])
        start_index += 1
        is_binary, = struct.unpack("?", b[start_index: start_index + 1])
        start_index += 1
        target_len, = struct.unpack("i", b[start_index: start_index + 4])
        start_index += 4
        target = b[start_index: start_index + target_len].decode(ENCODING)
        if is_dir:
            change = DirChange.from_bytes(b, start_index + target_len)
        else:
            change = FileChange.from_bytes(b, start_index + target_len)
        return ChangeStep(target, change, is_binary)

    def apply(self, origin):
        target = os.path.join(origin, self.target)
        if isinstance(self.change, FileChange):
            if not os.path.isfile(target):
                raise FileNotFoundError(f"no such file as {target}")
            self.change.apply_to_file(target)
        else:
            if not os.path.isdir(target):
                raise NotADirectoryError(f"no such dir as {target}")
            self.change.apply_to_dir(target)

    def encode(self):
        type_b = struct.pack("?", type(self.change) is DirChange)
        binary_b = struct.pack("?", self.is_binary)
        target_b = self.target.encode(ENCODING)
        target_len = struct.pack("i", len(target_b))
        change_b = self.change.encode()
        return type_b + binary_b + target_len + target_b + change_b

    def get_target(self, origin):
        target = os.path.join(origin, self.get_relative_target())
        return os.path.abspath(target)

    def get_relative_target(self):
        if isinstance(self.change, DirChange):
            return os.path.join(self.target, self.change.name)
        return self.target

    def set_relative_target(self, new_target):
        if isinstance(self.change, FileChange):
            self.target = new_target
        else:
            tail, head = os.path.split(new_target)
            self.target = tail
            self.change.name = head

    def get_rename_target(self):
        if isinstance(self.change, DirChange) \
                and self.change.type == DCT.RENAME:
            return os.path.join(self.target, self.change.new_name)
        raise TypeError('change type is not rename')

    def copy(self):
        new_change = self.change.copy()
        return ChangeStep(self.target, new_change, self.is_binary)
