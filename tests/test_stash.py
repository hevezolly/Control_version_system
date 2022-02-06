import unittest
import os
import shutil
from CVSysModules.stash import Stash


class StashTest(unittest.TestCase):
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

    def test_add(self):
        file = os.path.join(self.DIR1_NAME, 'asdf')
        data = 'weqpwef;aosia;wetqw;ebrk;qjwbdsoifapdr'
        with open(file, 'w') as f:
            f.write(data)
        stash = Stash(self.DIR2_NAME, True)
        stash.add_file(file, 'asdf', 0)
        self.assertEqual(1, len(stash.content))
        self.assertEqual('asdf', next(iter(stash.content.keys())))
        self.assertTrue(os.path.isfile(stash.content['asdf']['path']))

    def test_restore(self):
        file = os.path.join(self.DIR1_NAME, 'asdf')
        file2 = os.path.join(self.DIR1_NAME, 'asdf2')
        open(file2, 'w').close()
        data = 'weqpwef;aosia;wetqw;ebrk;qjwbdsoifapdr'
        with open(file, 'w') as f:
            f.write(data)
        stash = Stash(self.DIR2_NAME, True)
        stash.add_file(file, 'asdf', 0)
        stash2 = Stash(self.DIR2_NAME)
        stash2.restore('asdf', file2)
        with open(file2, 'r') as f:
            new_data = f.read()
        self.assertEqual(data, new_data)
