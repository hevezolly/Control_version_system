import unittest
import os
import shutil
from CVSysModules.dif_controller import Difference, MAIN_DIR_NAME
from CVSysModules.dir_change import ENCODING
import filecmp


class DiffControllerTest(unittest.TestCase):
    DIR1 = "dir_test1"
    DIR2 = "dir_test2"
    TEST_FILE = 'test.temp'

    def setUp(self) -> None:
        if os.path.isdir(self.DIR1):
            shutil.rmtree(self.DIR1)
        os.mkdir(self.DIR1)
        if os.path.isdir(self.DIR2):
            shutil.rmtree(self.DIR2)
        os.mkdir(self.DIR2)
        if not os.path.isfile(self.TEST_FILE):
            open(self.TEST_FILE, "w").close()
        if os.path.isfile(self.TEST_FILE):
            os.remove(self.TEST_FILE)

    def provide_space(self):
        return self.TEST_FILE

    def tearDown(self) -> None:
        if os.path.isdir(self.DIR1):
            shutil.rmtree(self.DIR1)
        if os.path.isdir(self.DIR2):
            shutil.rmtree(self.DIR2)

    def test_relative_path(self):
        d1 = (os.path.join(self.DIR1, 'dir1'))
        d2 = os.path.join(self.DIR1, 'dir1', 'dir2')
        os.mkdir(d1)
        os.mkdir(d2)
        path0 = Difference._get_relative_path(d2, 0)
        path1 = Difference._get_relative_path(d2, 1)
        path2 = Difference._get_relative_path(d2, 2)
        self.assertEqual('', path0)
        self.assertEqual(os.path.join('dir2', ''), path1)
        self.assertEqual(os.path.join('dir1', 'dir2', ''), path2)

    def test_get_renamed_files(self):
        open(os.path.join(self.DIR1, 'a'), 'w+').close()
        open(os.path.join(self.DIR1, 'b'), 'w+').close()
        open(os.path.join(self.DIR2, 'a'), 'w+').close()
        open(os.path.join(self.DIR2, 'c'), 'w+').close()
        open(os.path.join(self.DIR2, 'd'), 'w+').close()
        dif = Difference(self.DIR1, self.DIR2)
        left, right = dif._get_renamed_files()
        self.assertListEqual(['b'], left)
        self.assertListEqual(['c'], right)

    def test_are_dirs_same(self):
        os.mkdir(os.path.join(self.DIR1, 'a'))
        os.mkdir(os.path.join(self.DIR1, 'e'))
        open(os.path.join(self.DIR1, 'e', 'file.test'), 'w+').close()
        os.mkdir(os.path.join(self.DIR1, 'b'))
        os.mkdir(os.path.join(self.DIR1, 'd'))
        os.mkdir(os.path.join(self.DIR1, 'b', 'c'))
        os.mkdir(os.path.join(self.DIR2, 'a'))
        os.mkdir(os.path.join(self.DIR2, 'e'))
        with open(os.path.join(self.DIR2, 'e', 'file.test'), 'w+') as file:
            file.write("1")
        os.mkdir(os.path.join(self.DIR2, 'b'))
        os.mkdir(os.path.join(self.DIR2, 'd'))
        os.mkdir(os.path.join(self.DIR2, 'd', 'f'))
        os.mkdir(os.path.join(self.DIR2, 'b', 'c'))
        self.assertTrue(Difference.are_dirs_same(os.path.join(self.DIR1, 'a'),
                                                 os.path.join(self.DIR2, 'a')))
        self.assertTrue(Difference.are_dirs_same(os.path.join(self.DIR1, 'b'),
                                                 os.path.join(self.DIR2, 'b')))
        self.assertFalse(Difference.are_dirs_same(os.path.join(self.DIR1, 'd'),
                                                  os.path.join(self.DIR2,
                                                               'd')))
        self.assertFalse(Difference.are_dirs_same(os.path.join(self.DIR1, 'e'),
                                                  os.path.join(self.DIR2,
                                                               'e')))

    def test_get_renamed_subdirs1(self):
        os.mkdir(os.path.join(self.DIR1, 'a'))
        os.mkdir(os.path.join(self.DIR1, 'b'))
        os.mkdir(os.path.join(self.DIR1, 'b', 'e'))
        os.mkdir(os.path.join(self.DIR1, 'c'))
        os.mkdir(os.path.join(self.DIR1, 'c', 'fa'))
        os.mkdir(os.path.join(self.DIR1, 'd'))
        os.mkdir(os.path.join(self.DIR2, 'e'))
        os.mkdir(os.path.join(self.DIR2, 'f'))
        os.mkdir(os.path.join(self.DIR2, 'f', 'fa'))
        os.mkdir(os.path.join(self.DIR2, 'f', 'fa', 'ffa'))
        os.mkdir(os.path.join(self.DIR2, 'g'))
        os.mkdir(os.path.join(self.DIR2, 'g', 'e'))
        os.mkdir(os.path.join(self.DIR2, 'd'))
        dif = Difference(self.DIR1, self.DIR2)
        left, right = dif._get_renamed_subdirs()
        self.assertListEqual(['a', 'b'], left)
        self.assertListEqual(['e', 'g'], right)

    def test_get_delete_steps(self):
        os.mkdir(os.path.join(self.DIR1, 'a'))
        open(os.path.join(self.DIR1, 'file.test'), 'w+').close()
        open(os.path.join(self.DIR1, 'file.test2'), 'w+').close()
        open(os.path.join(self.DIR2, 'file.test2'), 'w+').close()
        dif = Difference(self.DIR1, self.DIR2)
        for step in dif.get_delete_steps():
            step.apply(self.DIR1)
        self.assertTrue(Difference.are_dirs_same(self.DIR1, self.DIR2))

    def test_get_rename_steps(self):
        os.mkdir(os.path.join(self.DIR1, 'a'))
        os.mkdir(os.path.join(self.DIR1, 'b'))
        os.mkdir(os.path.join(self.DIR1, 'b', 'e'))
        os.mkdir(os.path.join(self.DIR2, 'e'))
        os.mkdir(os.path.join(self.DIR2, 'g'))
        os.mkdir(os.path.join(self.DIR2, 'g', 'e'))
        dif = Difference(self.DIR1, self.DIR2)
        for step in dif.get_rename_steps():
            step.apply(self.DIR1)
        self.assertTrue(Difference.are_dirs_same(self.DIR1, self.DIR2))

    def test_get_file_changes(self):
        with open(os.path.join(self.DIR1, 'a'), 'wb+') as file1:
            file1.write(bytes([1, 2, 3]))
        with open(os.path.join(self.DIR2, 'a'), 'wb+') as file2:
            file2.write(bytes([2, 1, 12, 1, 5, 112]))
        changes = Difference._get_file_changes(self.provide_space,
                                               os.path.join(self.DIR1, 'a'),
                                               os.path.join(self.DIR2, 'a'))
        for change in changes:
            change.apply_to_file(os.path.join(self.DIR1, 'a'))
        self.assertTrue(filecmp.cmp(os.path.join(self.DIR1, 'a'),
                                    os.path.join(self.DIR2, 'a')))

    def test_get_lines_changes(self):
        with open(os.path.join(self.DIR1, 'a.txt'), 'wb+') as file1:
            file1.write("""привет привет
ой
пробел
строк
""".encode(ENCODING))
        with open(os.path.join(self.DIR2, 'a.txt'), 'wb+') as file2:
            file2.write("""привет привет пока
ой изменение
пробел
еще
несколько
строк""".encode(ENCODING))
        changes = Difference._get_file_changes(self.provide_space,
                                               os.path.join(self.DIR1,
                                                            'a.txt'),
                                               os.path.join(self.DIR2,
                                                            'a.txt'))
        for change in changes:
            change.apply_to_file(os.path.join(self.DIR1, 'a.txt'))
        self.assertTrue(filecmp.cmp(os.path.join(self.DIR1, 'a.txt'),
                                    os.path.join(self.DIR2, 'a.txt')))

    def test_get_change_steps(self):
        with open(os.path.join(self.DIR1, 'a'), 'wb+') as file1:
            file1.write(bytes([1, 2, 3]))
        with open(os.path.join(self.DIR1, 'b'), 'wb+') as file2:
            file2.write(bytes([1]))
        with open(os.path.join(self.DIR2, 'a'), 'wb+') as file3:
            file3.write(bytes([2, 1, 12, 1, 5, 112]))
        with open(os.path.join(self.DIR2, 'b'), 'wb+') as file4:
            file4.write(bytes([2, 1, 12, 1, 5, 112]))
        dif = Difference(self.DIR1, self.DIR2)
        for step in dif.get_change_steps(self.provide_space):
            step.apply(self.DIR1)
        self.assertTrue(Difference.are_dirs_same(self.DIR1, self.DIR2))

    def test_get_copy_steps(self):
        with open(os.path.join(self.DIR2, 'a'), 'wb+') as file:
            file.write(bytes(1024 * 1024 * 3))
        dif = Difference(self.DIR1, self.DIR2)
        dif.get_change(self.provide_space).apply_to(self.DIR1)
        self.assertTrue(Difference.are_dirs_same(self.DIR1, self.DIR2))

    def test_get_add_steps(self):
        os.mkdir(os.path.join(self.DIR2, 'a'))
        os.mkdir(os.path.join(self.DIR2, 'b'))
        open(os.path.join(self.DIR2, 'file.test'), 'w+').close()
        with open(os.path.join(self.DIR2, 'b', 'file.test'), 'wb+') as file:
            file.write(bytes([1, 23, 124, 33, 2, 12]))
        open(os.path.join(self.DIR2, 'file.test2'), 'w+').close()
        open(os.path.join(self.DIR1, 'file.test2'), 'w+').close()
        dif = Difference(self.DIR1, self.DIR2)
        for step in dif.get_add_steps(self.provide_space):
            step.apply(self.DIR1)
        self.assertTrue(Difference.are_dirs_same(self.DIR1, self.DIR2))

    def test_get_all_steps(self):
        os.mkdir(os.path.join(self.DIR1, 'a'))
        os.mkdir(os.path.join(self.DIR1, 'b'))
        os.mkdir(os.path.join(self.DIR1, 'b', 'd'))
        with open(os.path.join(self.DIR1, 'a', 'fil1.test'), 'wb+') as file1:
            file1.write(bytes([1, 2, 2, 1]))
        with open(os.path.join(self.DIR1, 'fil3.test'), 'wb+') as file3:
            file3.write(bytes([1, 2, 1]))
        os.mkdir(os.path.join(self.DIR2, 'a'))
        with open(os.path.join(self.DIR2, 'a', 'fil1.test'), 'wb+') as file1:
            file1.write(bytes([1, 2, 2, 1, 2, 3]))
        os.mkdir(os.path.join(self.DIR2, 'a', 'b'))
        os.mkdir(os.path.join(self.DIR2, 'b'))
        with open(os.path.join(self.DIR2, 'a', 'b', 'fil2.test'),
                  'wb+') as file2:
            file2.write(bytes([1, 2, 3, 3, 2, 1]))
        dif = Difference(self.DIR1, self.DIR2)
        for step in dif.get_all_steps(self.provide_space()):
            step.apply(self.DIR1)
        self.assertTrue(Difference.are_dirs_same(self.DIR1, self.DIR2))

    def test_CVS(self):
        os.mkdir(os.path.join(self.DIR1, MAIN_DIR_NAME))
        self.assertTrue(Difference.are_dirs_same(self.DIR1, self.DIR2))
