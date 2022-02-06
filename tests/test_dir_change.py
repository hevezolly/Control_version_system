import unittest
import os
import shutil
from CVSysModules.dir_change import DirChange, DCT


class DirChangeTest(unittest.TestCase):
    DIR_NAME = "testDir1"

    def setUp(self) -> None:
        if not os.path.isdir(self.DIR_NAME):
            os.mkdir(self.DIR_NAME)

    def tearDown(self) -> None:
        if os.path.isdir(self.DIR_NAME):
            shutil.rmtree(self.DIR_NAME)

    def test_encode(self):
        change = DirChange("asdf", DCT.ADD_DIR, "eew")
        encoded = bytearray(change.encode())
        encoded.extend(bytearray(5))
        new = bytearray(5)
        new.extend(encoded)
        decoded = DirChange.from_bytes(new, 5)
        self.assertEqual(change.name, decoded.name)
        self.assertEqual(change.new_name, decoded.new_name)
        self.assertEqual(change.type, decoded.type)

    def test_add_file(self):
        change = DirChange("asdf", DCT.ADD_FILE)
        change.apply_to_dir(self.DIR_NAME)
        self.assertEqual(True,
                         os.path.isfile(os.path.join(self.DIR_NAME, "asdf")))

    def test_remove_file(self):
        change = DirChange("asdf", DCT.REMOVE_FILE)
        file_name = os.path.join(self.DIR_NAME, "asdf")
        open(file_name, "w+").close()
        change.apply_to_dir(self.DIR_NAME)
        self.assertEqual(False, os.path.isfile(file_name))

    def test_rename_file(self):
        change = DirChange("asdf", DCT.RENAME, "zxcv")
        file_name = os.path.join(self.DIR_NAME, "asdf")
        open(file_name, "w+").close()
        change.apply_to_dir(self.DIR_NAME)
        self.assertEqual(False,
                         os.path.isfile(os.path.join(self.DIR_NAME, "asdf")))
        self.assertEqual(True,
                         os.path.isfile(os.path.join(self.DIR_NAME, "zxcv")))

    def test_add_dir(self):
        change = DirChange("asdf", DCT.ADD_DIR)
        change.apply_to_dir(self.DIR_NAME)
        self.assertEqual(True,
                         os.path.isdir(os.path.join(self.DIR_NAME, "asdf")))

    def test_remove_dir(self):
        change = DirChange("asdf", DCT.REMOVE_DIR)
        dir_name = os.path.join(self.DIR_NAME, "asdf")
        os.mkdir(dir_name)
        change.apply_to_dir(self.DIR_NAME)
        self.assertEqual(False, os.path.isdir(dir_name))

    def test_rename_dir(self):
        change = DirChange("asdf", DCT.RENAME, "zxcv")
        dir_name = os.path.join(self.DIR_NAME, "asdf")
        os.mkdir(dir_name)
        change.apply_to_dir(self.DIR_NAME)
        self.assertEqual(False,
                         os.path.isdir(os.path.join(self.DIR_NAME, "asdf")))
        self.assertEqual(True,
                         os.path.isdir(os.path.join(self.DIR_NAME, "zxcv")))
