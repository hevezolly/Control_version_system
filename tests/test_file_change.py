import unittest
import os
from CVSysModules.file_change import FileChange, FCT


class SingleFileChangeTest(unittest.TestCase):
    FILE_NAME = "test.tst"
    ADDITIONAL_NAME = "test2.tst"

    def setUp(self) -> None:
        if not os.path.isfile(self.FILE_NAME):
            open(self.FILE_NAME, "w").close()
        if not os.path.isfile(self.ADDITIONAL_NAME):
            open(self.ADDITIONAL_NAME, "w").close()

    def tearDown(self) -> None:
        if os.path.isfile(self.FILE_NAME):
            os.remove(self.FILE_NAME)
        if os.path.isfile(self.ADDITIONAL_NAME):
            os.remove(self.ADDITIONAL_NAME)

    def test_apply_insert(self):
        change = FileChange(2, bytes([1, 2, 3]), FCT.INSERT)
        with open(self.FILE_NAME, "wb") as file:
            file.write(bytes([1, 2, 3]))
        change.apply_to_file(self.FILE_NAME)
        with open(self.FILE_NAME, "rb") as file:
            new_bytes = file.read()
        self.assertEqual(bytes([1, 2, 1, 2, 3, 3]), new_bytes)

    def test_apply_delete(self):
        change = FileChange(1, 2, FCT.DELETE)
        with open(self.FILE_NAME, "wb") as file:
            file.write(bytes([1, 2, 3, 4]))
        change.apply_to_file(self.FILE_NAME)
        with open(self.FILE_NAME, "rb") as file:
            new_bytes = file.read()
        self.assertEqual(bytes([1, 4]), new_bytes)

    def test_apply_copy(self):
        old_bytes = bytes(512) + bytes([1, 2, 3]) + bytes(512)
        with open(self.ADDITIONAL_NAME, 'wb') as source:
            source.write(old_bytes)
        change = FileChange(0, self.ADDITIONAL_NAME, FCT.COPY)
        change.apply_to_file(self.FILE_NAME)
        with open(self.FILE_NAME, 'rb') as file:
            self.assertEqual(old_bytes, file.read())

    def test_encode(self):
        change = FileChange(1, '.\\asdf', FCT.COPY)
        encoded = bytearray(change.encode())
        encoded.extend(bytearray([12, 3]))
        new = bytearray(2)
        new.extend(encoded)
        decoded = FileChange.from_bytes(new, 2)
        self.assertEqual(change.index, decoded.index)
        self.assertEqual(change.data, decoded.data)
        self.assertEqual(change.type, decoded.type)
