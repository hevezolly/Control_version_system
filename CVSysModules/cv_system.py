from CVSysModules.storage_controller import Storage
from CVSysModules.dif_controller import MAIN_DIR_NAME
from CVSysModules.visuaizer import TreeVisualizer
from CVSysModules.change_step import FileChange
import shutil
import os


class CVSystem:
    def __init__(self, path, init, clear):
        self.path = path
        self.controller_path = os.path.join(path, MAIN_DIR_NAME)
        self.storage = None
        if init:
            self.init(clear)
            return
        if not os.path.isdir(self.controller_path):
            raise ValueError(f'{path} is not CVS folder, init CVS first')
        self.load()

    def load(self):
        self.storage = Storage(self.path)

    def init(self, clear):
        if not os.path.exists(self.path) and not clear:
            raise FileNotFoundError(
                f'{self.path} doesn\'t exist. use -c flag to create')
        elif not os.path.exists(self.path):
            os.mkdir(self.path)
        if os.listdir(self.path) and not clear:
            raise FileExistsError(f'{self.path} is not empty. ' +
                                  f'use -c flag to clear' +
                                  f' it or choose empty directory')
        elif os.listdir(self.path) and clear:
            def del_file(file_path):
                os.remove(file_path)

            def del_dir(dir_path):
                while True:
                    try:
                        shutil.rmtree(dir_path)
                        break
                    except OSError:
                        continue

            for element in os.listdir(self.path):
                path = os.path.join(self.path, element)
                if os.path.isdir(path):
                    del_dir(path)
                else:
                    del_file(path)
        self.storage = Storage(self.path, create_new=True)

    @property
    def was_change(self):
        change = ChangeType(False, False)
        if self.update_conflicts():
            change.merge = True
        if not self.storage.was_change():
            return change
        for c in self.get_change_list():
            if c not in self.get_stashed_files():
                change.change = True
        return change

    def pull(self, index):
        self.was_change.raise_exception()
        self.storage.goto_index(index)
        self.storage.pull()

    def get_file_changes(self):
        changes = []
        for step in self.storage.diff.get_all_steps(
                self.storage.provide_fake_space):
            if type(step.change) == FileChange:
                target = os.path.join(self.storage.origin_path, step.target)
                if target not in changes:
                    changes.append(target)
        return changes

    def get_stashed_files(self):
        files = []
        for _, item in self.storage.stash.content:
            files.append(os.path.abspath(item['old_path']))
        return files

    def pull_name(self, name):
        if name not in self.storage.tree.names:
            raise ValueError(f'no such name as {name}')
        index = self.storage.tree.names[name]
        self.pull(index)

    def go_previous(self):
        if self.storage.index <= -1:
            return
        self.was_change.raise_exception()
        self.storage.goto_index(self.storage.index - 1)
        self.storage.pull()

    def go_back(self):
        if self.storage.index <= -1:
            return
        self.was_change.raise_exception()
        current_branch = self.storage.tree.tree[self.storage.index]
        if len(current_branch) < 1:
            return
        if len(current_branch) == 1:
            self.storage.goto_index(-1)
        elif len(current_branch) > 1:
            self.storage.goto_index(current_branch[-2])
        self.storage.pull()

    def get_tree_drawer(self):
        drawer = TreeVisualizer(self.storage.tree.tree,
                                self.storage.tree.names, self.storage.index)
        return drawer

    def add_name(self, name):
        self.storage.add(name)

    def show_add(self):
        adds = self.storage.get_all_adds()
        for i in range(len(adds)):
            yield {'i': i + 1, 'n': adds[i]}

    def add_index(self, index):
        changes = self.get_change_list()
        if index < 0 or index >= len(changes):
            raise ValueError(f'index is out of range')
        self.add_name(changes[index])

    def add_all(self):
        changes = self.get_change_list()
        if not changes:
            raise ValueError('no changes were found')
        for change in changes:
            self.add_name(change)

    def push(self, name):
        if not self.storage.was_change():
            raise ValueError('no changes were done')
        self.storage.push_change(name)

    def discard_by_name(self, file_name):
        success = self.storage.discard_change(file_name)
        return success
        #     print('change was successfully discarded')
        # else:
        #     print(f'no changes, connected to {file_name} were found')

    def discard_by_index(self, index):
        changes = self.get_change_list()
        if index < 0 or index >= len(changes):
            raise ValueError(f'index is out of range')
        self.discard_by_name(changes[index])

    def get_change_list(self):
        changes = []
        for step in self.storage.diff.get_all_steps(
                self.storage.provide_fake_space):
            if type(step.change) == FileChange:
                target = os.path.join(self.storage.origin_path, step.target)
                if target not in changes:
                    changes.append(target)
            else:
                target = os.path.join(self.storage.origin_path, step.target,
                                      step.change.name)
                if target not in changes:
                    changes.append(target)
        return changes

    def get_small_changes(self, add):
        changes = self.get_change_list()
        added = self.storage.get_all_adds()
        # print('changes were found in:')
        for i in range(len(changes)):
            yield {'i': i+1, 'n': changes[i]}
            # print(f'{i + 1}. {changes[i]}' + end)
        if not add:
            return
        for i in range(len(added)):
            yield {'i': None, 'n': added[i]}
            # print(f'{added[i]}' + end)

    def get_big_changes(self, add):
        used = []
        steps = list(
            self.storage.diff.get_all_steps(self.storage.provide_fake_space))
        if add:
            steps.extend(self.storage.add_steps)
        for step in steps:
            target = step.get_target(self.storage.origin_path)
            if target in used:
                continue
            if isinstance(step.change, FileChange):
                yield {'n': target, 't': None}
            else:
                yield {'n': target, 't': step.change.type}
            used.append(target)

    def stash(self, file, name, delete=False):
        if not os.path.isfile(file):
            raise FileNotFoundError(f'no such file as {file}')
        if file not in self.get_file_changes():
            raise ValueError(f'no changes were done in {file}')
        try:
            self.storage.stash.add_file(file, name, self.storage.index, delete)
            self.discard_by_name(file)
        except ValueError:
            raise ValueError(
                f'name {name} is already exists, use -d to rewrite')

    def stash_by_index(self, index, name, delete=False):
        changes = self.get_change_list()
        if index <= 0 or index > len(changes):
            raise ValueError('index is out of range')
        self.stash(changes[index], name, delete)

    def restore(self, new_file, delete, create_new, name):
        if new_file == '':
            new_file = self.storage.stash.content[name]['old_path']
        if not os.path.isfile(new_file) and not create_new:
            raise FileNotFoundError(f'no such file as {new_file}')
        elif not os.path.isfile(new_file):
            open(new_file, 'w').close()
        self.storage.stash.restore(name, new_file, delete)

    def remove_from_stash(self, name):
        self.storage.stash.delete_file(name)

    def clear_stash(self):
        self.storage.stash.clear()

    def show_stash(self):
        for key in self.storage.stash.content:
            old_path = self.storage.stash.content[key]['old_path']
            index = self.storage.stash.content[key]['index']
            name = self.storage.tree.get_name(index)
            yield {'p': old_path, 'k': key, 'n': name}
            print(f'{key}: {old_path} saved in the commit {name}')

    def merge(self, name, is_reversed):
        self.was_change.raise_exception()
        index = self.storage.tree.names[name]
        self.storage.merge(index, is_reversed)
        return self.storage.get_conflicts()

    def forget_conflicts(self):
        sucess = self.was_change.merge
        self.storage.set_conflicts([])
        return sucess

    def update_conflicts(self):
        conflicts = self.storage.get_conflicts()
        for conflict in conflicts:
            conflict.update(self.storage.origin_path)
        conflicts = list(filter(lambda c: c.__bool__(), conflicts))
        self.storage.set_conflicts(conflicts)
        return conflicts


class ChangeType:
    def __init__(self, merge, change):
        self.merge = merge
        self.change = change

    def __bool__(self):
        return self.merge or self.change

    def get_message(self):
        if self.merge:
            return 'merge conflicts were found. Solve them or use merge -f'
        if self.change:
            return 'change not saved, commit or discard all changes'

    def raise_exception(self):
        massage = self.get_message()
        if massage is None:
            return
        raise ValueError(massage)
