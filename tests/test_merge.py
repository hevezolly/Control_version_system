import unittest
from CVSysModules.merge import VirtDir
from CVSysModules.dir_change import DCT, DirChange
from CVSysModules.change_step import ChangeStep
import os
import shutil


class VirtDirTest(unittest.TestCase):
    SIM_SPACE = '.sim_space'

    def setUp(self) -> None:
        if os.path.exists(self.SIM_SPACE):
            while True:
                try:
                    shutil.rmtree(self.SIM_SPACE)
                    break
                except OSError:
                    continue
        if not os.path.exists(self.SIM_SPACE):
            os.mkdir(self.SIM_SPACE)

    def tearDown(self) -> None:
        if os.path.exists(self.SIM_SPACE):
            while True:
                try:
                    shutil.rmtree(self.SIM_SPACE)
                    break
                except OSError:
                    continue

    @staticmethod
    def add_dir(origin, name):
        change = DirChange(name, DCT.ADD_DIR)
        return ChangeStep(origin, change, True)

    @staticmethod
    def add_file(origin, name):
        change = DirChange(name, DCT.ADD_FILE)
        return ChangeStep(origin, change, False)

    def test_add(self):
        directory = VirtDir(True, True, 0)
        directory.add_step(self.add_dir('', 'asdf'), False)
        self.assertTrue('asdf' in directory)
        directory.add_step(self.add_file('asdf', 'asdf'), False)
        directory.add_step(self.add_dir('asdf', 'z'), False)
        self.assertFalse(os.path.join('asdf', 'asdf') in directory)
        self.assertTrue(os.path.join('asdf', 'asdf') in directory['asdf'])
        self.assertTrue(os.path.join('asdf', 'z') in directory['asdf'])

    def test_get_child(self):
        directory = VirtDir(True, True, 0)
        directory.add_step(self.add_dir('', 'asdf'), False)
        directory.add_step(self.add_dir('asdf', 'asdf'), False)
        directory.add_step(self.add_dir('asdf', 'a'), False)
        directory.add_step(self.add_file(os.path.join('asdf', 'asdf'), 'a'),
                           False)
        child = directory['asdf'].get_child_by_name(
            os.path.join('asdf', 'asdf', 'a'))
        self.assertTrue(
            child is directory['asdf'][os.path.join('asdf', 'asdf')])

    def test_del(self):
        directory = VirtDir(True, True, 0)
        directory.add_step(self.add_dir('', 'asdf'), False)
        directory.add_step(self.add_dir('asdf', 'asdf'), False)
        directory.add_step(self.add_file(os.path.join('asdf', 'asdf'), 'a'),
                           False)
        self.assertTrue(os.path.join('asdf', 'asdf', 'a') in directory['asdf'][
            os.path.join('asdf', 'asdf')])
        directory.remove_child(os.path.join('asdf', 'asdf', 'a'))
        self.assertFalse(
            os.path.join('asdf', 'asdf', 'a') in directory['asdf'][
                os.path.join('asdf', 'asdf')])

    def test_rename1(self):
        directory = VirtDir(True, True, 0)
        directory.add_step(self.add_dir('', 'asdf'), False)
        directory.add_step(self.add_dir('asdf', 'asdf'), False)
        directory.rename(os.path.join('asdf', 'asdf'),
                         os.path.join('asdf', 'as'))
        self.assertTrue(os.path.join('asdf', 'as') in directory['asdf'])
        self.assertFalse(os.path.join('asdf', 'asdf') in directory['asdf'])

    def test_rename2(self):
        directory = VirtDir(True, True, 0)
        directory.add_step(self.add_dir('', 'asdf'), True)
        directory.add_step(self.add_dir('asdf', 'asdf'), True)
        directory.rename(os.path.join('asdf', 'asdf'),
                         os.path.join('asdf', 'as'))
        self.assertTrue(os.path.join('asdf', 'as') in directory['asdf'])
        self.assertTrue(os.path.join('asdf', 'asdf') in directory['asdf'])

    def test_get_steps(self):
        s1 = self.add_dir('', 'asdf')
        s2 = self.add_dir('asdf', 'asdf')
        s3 = self.add_file(os.path.join('asdf', 'asdf'), 'a')
        directory = VirtDir(True, True, 0)
        directory.add_step(s1, True)
        directory.add_step(s2, True)
        directory.add_step(s3, True)
        steps = list(directory.get_steps())
        self.assertListEqual([s1, s2, s3], steps)

    def test_merge(self):
        dir0 = VirtDir(True, True, 0)
        dir1 = VirtDir(True, True, 1)
        dir0.add_step(self.add_dir('', 'asdf'))
        dir0.add_step(self.add_dir('asdf', 'asdf'))
        dir1.add_step(self.add_dir('', 'asdf'))
        dir1.add_step(self.add_dir('', 'asdf1'))
        result = VirtDir.merge(dir0, dir1, self.SIM_SPACE)
        self.assertTrue('asdf' in result)
        self.assertTrue('asdf1' in result)
        self.assertTrue(os.path.join('asdf', 'asdf') in result['asdf'])
