import os
import shutil
import itertools
from CVSysModules.tree import Tree
from CVSysModules.single_change import Change
from CVSysModules.change_step import DirChange
from CVSysModules.dir_change import DCT
from CVSysModules.dif_controller import Difference, MAIN_DIR_NAME, BUFFER_SIZE
from CVSysModules.stash import Stash
from CVSysModules.merge import MergeBase, ConflictInfo

TREE_DIR_NAME = '.tree'
JSON_NAME = 'tree.json'
SIMULATION_DIR_NAME = '.simulation'
CHANGE_NAME = 'change.cng'
BASE_SPACE_EXTENSION = '.cnt'
FAKE_STORAGE = 'fake_place'
ADD_STORAGE = 'add.ast'
CONFLICTS = 'conflicts.mrg'
MERGE_DIR_NAME = 'merge'


class Storage:
    def __init__(self, directory, create_new=False):
        self.tree = None
        self.origin_path = directory
        self._path = os.path.join(directory, MAIN_DIR_NAME)
        self._tree_path = os.path.join(self._path, TREE_DIR_NAME)
        self._merge_path = os.path.join(self._path, MERGE_DIR_NAME)
        self._simulation_path = os.path.join(self._path, SIMULATION_DIR_NAME)
        self._fake_place = os.path.join(self._path,
                                        FAKE_STORAGE + BASE_SPACE_EXTENSION)
        self._conflict_place = os.path.join(self._path, CONFLICTS)
        self._add_storage = os.path.join(self._path, ADD_STORAGE)
        if create_new:
            self._recreate()
        else:
            self.tree = Tree(os.path.join(self._path, JSON_NAME))
            self.add_steps = self.get_add()
        self.stash = Stash(self._path, create_new)
        self.diff = Difference(self._simulation_path, self.origin_path)

    def set_add(self):
        new_change = Change(*self.add_steps)
        with open(self._add_storage, 'wb') as file:
            file.write(new_change.encode())

    def get_add(self):
        with open(self._add_storage, 'rb') as file:
            return Change.from_bytes(file.read()).steps

    @property
    def index(self):
        return self.tree.index

    def provide_space(self):
        path = self._tree_path
        for i in self.tree.get_index_path_by_index(self.index):
            path = os.path.join(path, str(i))
        unique_path = os.path.join(path, self.get_unique_file_name(path))
        open(unique_path, 'w+').close()
        return unique_path

    @staticmethod
    def get_unique_file_name(path):
        for i in itertools.count():
            name = str(i) + BASE_SPACE_EXTENSION
            if not os.path.isfile(os.path.join(path, name)):
                break
        return name

    def _recreate(self):
        if os.path.isdir(self._path):
            shutil.rmtree(self._path)
        self.add_steps = []
        os.mkdir(self._path)
        os.mkdir(self._tree_path)
        os.mkdir(self._simulation_path)
        os.mkdir(self._merge_path)
        with open(self._add_storage, 'wb') as file:
            c = Change()
            file.write(c.encode())
        self.tree = Tree(os.path.join(self._path, JSON_NAME), create_new=True)

    def simulate(self, index=None):
        if os.path.isdir(self._simulation_path):
            shutil.rmtree(self._simulation_path)
        while 1:
            try:
                os.mkdir(self._simulation_path)
                break
            except PermissionError:
                continue
        self.apply_changes(self._simulation_path, index)

    def pull(self):
        for name in os.listdir(self.origin_path):
            if name == MAIN_DIR_NAME:
                continue
            file = os.path.join(self.origin_path, name)
            while True:
                try:
                    if os.path.isfile(file):
                        os.remove(file)
                    else:
                        shutil.rmtree(file)
                except OSError:
                    continue
                else:
                    break
        self.apply_changes(self.origin_path)
        self.simulate()

    def get_all_adds(self):
        def join(step):
            return step.get_target(self.origin_path)

        return list(set(map(join, self.add_steps)))

    def was_change(self):
        return not Difference.are_dirs_same(self._simulation_path,
                                            self.origin_path) or self.tree.add

    def add(self, path):
        added = self.tree.add_path(path, self.origin_path)
        diff = Difference(self._simulation_path, self.origin_path)
        change = diff.get_change(self.provide_space, added)
        change.apply_to(self._simulation_path)
        self.add_steps.extend(change.steps)
        self.set_add()

    def push_change(self, name):
        if not self.was_change():
            return
        if not self.tree.add:
            raise ValueError('add is empty')

        new_index = self.tree.add_branch(name)
        path = self._tree_path
        for i in self.tree.get_index_path_by_index(new_index):
            path = os.path.join(path, str(i))
        os.mkdir(path)
        self.goto_index(new_index)
        path = os.path.join(path, CHANGE_NAME)
        change = Change(*self.get_add())
        self.tree.clear_add()
        self.add_steps = []
        self.set_add()
        with open(path, 'wb') as file:
            file.write(change.encode())

    def goto_index(self, index):
        if index < -1 or index >= len(self.tree.tree):
            raise ValueError('index out of range')
        self.tree.index = index
        self.tree.dump()

    def apply_changes(self, path, index=None):
        if index is None:
            index = self.index
        for index in self.tree.get_index_path_by_index(index):
            change = self.get_change(index)
            change.apply_to(path)

    def get_change(self, index=None):
        if index is None:
            index = self.tree.index
        path = self._tree_path
        for i in self.tree.get_index_path_by_index(index):
            path = os.path.join(path, str(i))
        path = os.path.join(path, CHANGE_NAME)
        with open(path, 'rb') as file:
            return Change.from_bytes(file.read())

    def provide_fake_space(self):
        if not os.path.isfile(self._fake_place):
            open(self._fake_place, 'w').close()
        return self._fake_place

    @staticmethod
    def _discard_step(step, origin, simulation):
        def revert_file(change, copy):
            with open(copy, 'rb') as source:
                with open(change, 'wb') as dest:
                    data = source.read(BUFFER_SIZE)
                    while data:
                        dest.write(data)
                        data = source.read(BUFFER_SIZE)

        target = step.get_target(origin)
        if type(step.change) == DirChange:
            step.revert(origin)
            if step.change.type == DCT.REMOVE_FILE:
                file_to_change = target
                file_to_copy = step.get_target(simulation)
                revert_file(file_to_change, file_to_copy)
        else:
            file_to_change = target
            file_to_copy = step.get_target(simulation)
            if os.path.exists(file_to_copy):
                revert_file(file_to_change, file_to_copy)

    def discard_change(self, file):
        was_change = False
        file = os.path.abspath(file)
        diff = Difference(self._simulation_path, self.origin_path)
        steps = [s for s in diff.get_all_steps(self.provide_fake_space)]
        for step in reversed(steps):
            target = step.get_target(self.origin_path)
            if file == target:
                was_change = True
                Storage._discard_step(step, self.origin_path,
                                      self._simulation_path)
        return was_change

    def set_conflicts(self, conflicts):
        if not any(conflicts):
            if os.path.exists(self._conflict_place):
                os.remove(self._conflict_place)
        else:
            with open(self._conflict_place, 'wb') as file:
                file.write(ConflictInfo.encode(conflicts))

    def get_conflicts(self):
        if not os.path.exists(self._conflict_place):
            return []
        with open(self._conflict_place, 'rb') as file:
            conflicts = ConflictInfo.decode(file.read())
            return [c for c in conflicts if
                    os.path.isfile(os.path.join(self.origin_path, c.name))]

    def merge(self, other_index, reverse):
        left = []
        right = []
        for current_i in self.tree.get_index_path_by_index(self.index):
            if other_index == current_i:
                raise ValueError("changes are on one branch")
            right.append(current_i)
        for other_i in self.tree.get_index_path_by_index(other_index):
            if self.index == other_i:
                raise ValueError("changes are on one branch")
            left.append(other_i)

        i = 0
        common_steps = []
        for i in range(min(len(left), len(right))):
            if left[i] != right[i]:
                break
            common_steps.extend(self.get_change(left[i]).steps)
        left = left[i:]
        right = right[i:]
        base = MergeBase(common_steps)
        for index in left:
            change = self.get_change(index)
            for step in change.steps:
                base.add_step(step, 0)
        for index in right:
            change = self.get_change(index)
            for step in change.steps:
                base.add_step(step, 1)

        base.merge(self._merge_path, not reverse)
        new_steps = base.get_steps()
        fina_change = Change(*new_steps)

        self.simulate(-1)
        fina_change.apply_to(self._simulation_path)

        dif = Difference(self.origin_path, self._simulation_path)
        change = dif.get_change(self.provide_space)
        change.apply_to(self.origin_path)

        self.simulate(self.index)
        self.set_conflicts(base.get_conflicts())
