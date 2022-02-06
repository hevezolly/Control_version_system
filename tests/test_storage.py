import unittest
import os
import shutil
from CVSysModules.storage_controller import Storage
from CVSysModules.dif_controller import Difference


class StorageTest(unittest.TestCase):
    DIR1_NAME = 'test_dir'
    DIR2_NAME = 'ad_dir'

    def setUp(self) -> None:
        if os.path.isdir(self.DIR1_NAME):
            shutil.rmtree(self.DIR1_NAME)
        os.mkdir(self.DIR1_NAME)
        if os.path.isdir(self.DIR2_NAME):
            shutil.rmtree(self.DIR2_NAME)
        os.mkdir(self.DIR2_NAME)

    def tearDown(self) -> None:
        if os.path.isdir(self.DIR1_NAME):
            shutil.rmtree(self.DIR1_NAME)
        if os.path.isdir(self.DIR2_NAME):
            shutil.rmtree(self.DIR2_NAME)

    def test_add_change(self):
        storage = Storage(self.DIR1_NAME, create_new=True)
        path = os.path.join(self.DIR1_NAME, 'asdf')
        os.mkdir(path)
        storage.add(path)
        storage.push_change('asdf')
        storage2 = Storage(self.DIR1_NAME)
        storage2.apply_changes(self.DIR2_NAME)
        self.assertTrue(
            Difference.are_dirs_same(self.DIR1_NAME, self.DIR2_NAME))

    def test_more_changes(self):
        storage = Storage(self.DIR1_NAME, create_new=True)
        os.mkdir(os.path.join(self.DIR1_NAME, 'asdf'))
        os.mkdir(os.path.join(self.DIR2_NAME, 'asdf'))
        storage.add(os.path.join(self.DIR1_NAME, 'asdf'))
        storage.push_change('asdf')
        open(os.path.join(self.DIR1_NAME, 'asdf', 'f'), 'w+').close()
        storage.add(os.path.join(self.DIR1_NAME, 'asdf', 'f'))
        storage.push_change('zxcv')
        storage2 = Storage(self.DIR1_NAME)
        storage2.goto_index(0)
        storage2.pull()
        self.assertTrue(
            Difference.are_dirs_same(self.DIR1_NAME, self.DIR2_NAME))

    def test_provide_space(self):
        storage = Storage(self.DIR1_NAME, create_new=True)
        new_path = storage.provide_space()
        other_path = storage.provide_space()
        self.assertNotEqual(new_path, other_path)

    def test_revert_change1(self):
        storage = Storage(self.DIR1_NAME, create_new=True)
        path = os.path.join(self.DIR1_NAME, 'asdf')
        os.mkdir(path)
        storage.discard_change(path)
        self.assertFalse(os.path.isdir(path))

    def test_revert_change2(self):
        storage = Storage(self.DIR1_NAME, create_new=True)
        path1 = os.path.join(self.DIR1_NAME, 'as')
        path2 = os.path.join(self.DIR1_NAME, 'a')
        os.mkdir(path1)
        os.mkdir(path2)
        storage.discard_change(path1)
        self.assertFalse(os.path.isdir(path1))
        self.assertTrue(os.path.isdir(path2))

    def test_revert_change3(self):
        storage = Storage(self.DIR1_NAME, create_new=True)
        path1 = os.path.join(self.DIR1_NAME, 'as')
        with open(path1, 'w') as file:
            file.write('zawneif keajinro')
        storage.add(path1)
        storage.push_change('asdf')
        with open(path1, 'w') as file:
            file.write('zawneif')
        with open(path1, 'r') as file:
            self.assertEqual('zawneif', file.read())
        storage.discard_change(path1)
        with open(path1, 'r') as file:
            self.assertEqual('zawneif keajinro', file.read())

    def test_revert_change4(self):
        storage = Storage(self.DIR1_NAME, create_new=True)
        path1 = os.path.join(self.DIR1_NAME, 'as')
        path2 = os.path.join(self.DIR1_NAME, 'a')
        os.mkdir(path1)
        storage.add(path1)
        storage.push_change('asdf')
        os.rename(path1, path2)
        storage.discard_change(path1)
        self.assertFalse(os.path.exists(path2))
        self.assertTrue(os.path.exists(path1))

    def test_merge(self):
        storage = Storage(self.DIR1_NAME, create_new=True)
        path1 = os.path.join(self.DIR1_NAME, 'a')
        path2 = os.path.join(self.DIR1_NAME, 'b')
        os.mkdir(path1)
        storage.add(path1)
        storage.push_change('asdf')
        index_to_merge = storage.index
        storage.goto_index(storage.index - 1)
        storage.pull()
        os.mkdir(path2)
        storage.add(path2)
        storage.push_change('aew')
        storage.merge(index_to_merge, False)
        self.assertTrue(os.path.exists(path1))
        self.assertTrue(os.path.exists(path2))
