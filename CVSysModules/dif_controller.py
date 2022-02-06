import filecmp
import difflib
import os
import itertools
from CVSysModules.dir_change import DirChange, DCT
from CVSysModules.file_change import FileChange, FCT, BUFFER_SIZE
from CVSysModules.change_step import ChangeStep
from CVSysModules.single_change import Change
from CVSysModules.binary_checker import is_binary_file

MAIN_DIR_NAME = '.CVS'
SIZE_TO_MAKE_COPY_MB = 1
TEXT_EXTENSIONS = ['.txt', '.doc', '.py']
SPACE_SEP = b'\r\n'


class Difference:
    def __init__(self, old_dir, new_dir, depth=0):
        self.left = old_dir
        self.right = new_dir
        self.diff = filecmp.dircmp(old_dir,
                                   new_dir,
                                   ignore=[MAIN_DIR_NAME,
                                           *filecmp.DEFAULT_IGNORES])
        self.depth = depth
        self._relative_path = Difference._get_relative_path(self.left,
                                                            self.depth)

    def get_all_steps(self, get_path, files=None):
        def check(step):
            return files is None or step.get_relative_target() in files

        for s in itertools.chain(self.get_add_steps(get_path),
                                 self.get_delete_steps(),
                                 self.get_change_steps(get_path),
                                 self.get_rename_steps()):
            if check(s):
                yield s

        for subdir in self.diff.common_dirs:
            left = os.path.join(self.left, subdir)
            right = os.path.join(self.right, subdir)
            new_diff = Difference(left, right, self.depth + 1)
            for s in new_diff.get_all_steps(get_path, files):
                yield s

    def get_change(self, get_path, files=None):
        change = Change()
        for s in self.get_all_steps(get_path, files):
            change.add_steps(s)
        return change

    def get_delete_steps(self):
        left_renamed_f, _ = self._get_renamed_files()
        left_renamed_d, _ = self._get_renamed_subdirs()
        for file_name in self.diff.left_only:
            if file_name in left_renamed_f or file_name in left_renamed_d:
                continue
            t = DCT.REMOVE_FILE
            if os.path.isdir(os.path.join(self.left, file_name)):
                t = DCT.REMOVE_DIR
            yield ChangeStep(self._relative_path, DirChange(file_name, t),
                             True)

    def get_add_steps(self, get_path):
        _, renamed_f = self._get_renamed_files()
        _, renamed_d = self._get_renamed_subdirs()
        renamed_f.extend(renamed_d)
        return Difference._get_add_steps(map(lambda a:
                                             os.path.join(self.right, a),
                                             self.diff.right_only),
                                         self.depth,
                                         get_path,
                                         renamed_f)

    def get_rename_steps(self):
        left_renamed_f, right_renamed_f = self._get_renamed_files()
        left_renamed_d, right_renamed_d = self._get_renamed_subdirs()
        for i in range(len(left_renamed_f)):
            change = DirChange(left_renamed_f[i],
                               DCT.RENAME,
                               right_renamed_f[i])
            yield ChangeStep(self._relative_path, change, True)
        for i in range(len(left_renamed_d)):
            change = DirChange(left_renamed_d[i],
                               DCT.RENAME,
                               right_renamed_d[i])
            yield ChangeStep(self._relative_path, change, True)

    @staticmethod
    def _get_relative_path(path_tail, depth):
        path = ""
        tail = path_tail
        for i in range(depth):
            tail, head = os.path.split(tail)
            path = os.path.join(head, path)
        return path

    def _get_renamed_subdirs(self):
        renamed_r = []
        renamed_l = []
        for dir_l in self.diff.left_only:
            left_name = os.path.join(self.left, dir_l)
            if os.path.isfile(left_name):
                continue
            for dir_r in self.diff.right_only:
                right_name = os.path.join(self.right, dir_r)
                if dir_r in renamed_r or os.path.isfile(right_name):
                    continue
                if Difference.are_dirs_same(left_name, right_name):
                    renamed_r.append(dir_r)
                    renamed_l.append(dir_l)
                    break
        return renamed_l, renamed_r

    @staticmethod
    def are_dirs_same(dir1, dir2, ignore_cvs=True):
        ignore = filecmp.DEFAULT_IGNORES
        if ignore_cvs:
            ignore.append(MAIN_DIR_NAME)
        diff = filecmp.dircmp(dir1, dir2, ignore=ignore)
        same = not (diff.left_only or diff.right_only or diff.diff_files)
        for subdir in diff.common_dirs:
            new1 = os.path.join(dir1, subdir)
            new2 = os.path.join(dir2, subdir)
            same = same and Difference.are_dirs_same(new1, new2)
        return same

    @staticmethod
    def _get_add_steps(files, depth, get_path, renames=()):
        for file in files:
            tail, name = os.path.split(file)
            if name in renames:
                continue
            path = Difference._get_relative_path(tail, depth)
            if os.path.isfile(file):
                change = DirChange(name, DCT.ADD_FILE)
                yield ChangeStep(path, change, is_binary_file(file))
                for change in Difference._get_file_changes(new_f=file,
                                                           get_path=get_path):
                    yield ChangeStep(os.path.join(path, name), change, True)
            elif os.path.isdir(file):
                change = DirChange(name, DCT.ADD_DIR)
                yield ChangeStep(path, change, True)
                files_to_check = map(lambda a: os.path.join(file, a),
                                     os.listdir(file))
                for s in Difference._get_add_steps(files_to_check,
                                                   depth + 1,
                                                   get_path):
                    yield s

    def get_change_steps(self, get_path):
        for file_name in self.diff.diff_files:
            left_name = os.path.join(self.left, file_name)
            right_name = os.path.join(self.right, file_name)
            relative_name = os.path.join(self._relative_path, file_name)
            for change in Difference._get_file_changes(get_path,
                                                       left_name,
                                                       right_name):
                yield ChangeStep(relative_name, change, True)

    @staticmethod
    def _get_file_changes(get_path, old_f=None, new_f=None):
        if old_f is None and new_f is None:
            raise ValueError('old_f or new_f should be not None')

        if get_path is not None:
            if new_f is not None:
                new_size = os.stat(new_f).st_size
                old_size = 0
                if old_f is not None:
                    old_size = os.stat(old_f).st_size
                if new_size - old_size >= SIZE_TO_MAKE_COPY_MB * 1024 * 1024 \
                        and is_binary_file(new_f):
                    return Difference._get_copy_change_from_file(new_f,
                                                                 get_path),

        b1 = b''
        if old_f is not None:
            with open(old_f, 'br') as f1:
                b1 = f1.read()
        b2 = b''
        if new_f is not None:
            with open(new_f, 'br') as f2:
                b2 = f2.read()
        if not (is_binary_file(old_f) or is_binary_file(new_f)):
            return Difference.get_file_changes_from_bytes_by_lines(b1, b2)
        return Difference.get_file_changes_from_bytes(b1, b2)

    @staticmethod
    def _get_copy_change_from_file(file_path, get_path):
        storage_path = get_path()
        with open(file_path, 'rb') as source:
            with open(storage_path, 'wb') as dest:
                data = source.read(BUFFER_SIZE)
                while data:
                    dest.write(data)
                    data = source.read(BUFFER_SIZE)
        return FileChange(0, storage_path, FCT.COPY)

    @staticmethod
    def get_file_changes_from_bytes(b1, b2, start_index=0):
        difference = difflib.SequenceMatcher(None, b1, b2)
        for tag, i1, i2, j1, j2 in reversed(difference.get_opcodes()):
            if tag == 'delete':
                yield FileChange(start_index + i1, i2 - i1, FCT.DELETE)
            elif tag == 'insert':
                yield FileChange(start_index + i1, b2[j1:j2], FCT.INSERT)
            elif tag == 'replace':
                yield FileChange(start_index + i1, i2 - i1, FCT.DELETE)
                yield FileChange(start_index + i1, b2[j1:j2], FCT.INSERT)

    @staticmethod
    def get_file_changes_from_bytes_by_lines(b1, b2):
        def add_space(b):
            return b + SPACE_SEP

        b1 = list(map(add_space, b1.split(SPACE_SEP)))
        b2 = list(map(add_space, b2.split(SPACE_SEP)))
        b1[-1] = b1[-1][:-len(SPACE_SEP)]
        b2[-1] = b2[-1][:-len(SPACE_SEP)]
        difference = difflib.SequenceMatcher(None, b1, b2)
        for tag, i1, i2, j1, j2 in reversed(difference.get_opcodes()):
            start = sum(map(lambda t: len(b1[t]), range(i1)))
            end = sum(map(lambda t: len(b1[t]), range(i2)))
            content = b''
            for i in range(j1, j2):
                content += b2[i]
            if tag == 'delete':
                yield FileChange(start, end - start, FCT.DELETE)
            elif tag == 'insert':
                yield FileChange(start, content, FCT.INSERT)
            elif tag == 'replace':
                yield FileChange(start, end - start, FCT.DELETE)
                yield FileChange(start, content, FCT.INSERT)

    def _get_renamed_files(self):
        renamed_r = []
        renamed_l = []
        for file_l in self.diff.left_only:
            left_name = os.path.join(self.left, file_l)
            if os.path.isdir(left_name):
                continue
            for file_r in self.diff.right_only:
                right_name = os.path.join(self.right, file_r)
                if file_r in renamed_r or os.path.isdir(right_name):
                    continue
                if filecmp.cmp(left_name, right_name):
                    renamed_r.append(file_r)
                    renamed_l.append(file_l)
                    break
        return renamed_l, renamed_r
