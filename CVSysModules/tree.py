import json
import os

ROOT_NAME = '$ROOT$'


class Tree:
    def __init__(self, json_path, create_new=False):
        self._data = {'index': -1, 'tree': [], 'names': {ROOT_NAME: -1},
                      'add': []}
        self.json_path = json_path

        self.index = self._data['index']
        self.tree = self._data['tree']
        self.names = self._data['names']
        self._add = self._data['add']

        if create_new:
            self.dump()
        else:
            self.load()

    @property
    def add(self):
        return self._add

    def add_path(self, path, origin):
        added = []
        path = os.path.abspath(path)
        origin = os.path.abspath(origin)
        # if not os.path.exists(path):
        #   raise FileNotFoundError(f'no such file or directory {path}')
        tail = path
        head = ''
        while tail != origin:
            if not tail:
                raise ValueError('incorrect path or origin')
            tail, new_head = os.path.split(tail)
            head = os.path.join(new_head, head)
            if tail != origin:
                new_added = self.add_path(os.path.normpath(tail), origin)
                added.extend(new_added)
        head = os.path.normpath(head)
        added.append(head)
        if head not in self._add:
            self._add.append(head)
        self.dump()
        return added

    def remove_path(self, path, origin):
        removed = []
        path = os.path.abspath(path)
        origin = os.path.abspath(origin)
        tail = path
        head = ''
        while tail != origin:
            if not tail:
                raise ValueError('incorrect path or origin')
            tail, new_head = os.path.split(tail)
            head = os.path.join(new_head, head)
        head = os.path.normpath(head)
        if head not in self._add:
            raise ValueError(f'{path} not in add list')
        self._add.remove(head)
        removed.append(head)
        for new_path in self._add:
            tail, _ = os.path.split(new_path)
            if tail == path:
                new_removed = self.remove_path(new_path, origin)
                removed.extend(new_removed)
        self.dump()
        return removed

    def clear_add(self):
        removed = self._add.copy()
        self._add = []
        self.dump()
        return removed

    def add_branch(self, name):
        if name in self.names:
            raise ValueError(f'name {name} is already exists')
        new_index = len(self.tree)
        self.names[name] = new_index
        path = [] if self.index == -1 else self.tree[self.index].copy()
        path.append(new_index)
        self.tree.append(path)
        self.dump()
        return new_index

    def get_index_path_by_index(self, index):
        if index < -1 or index >= len(self.tree):
            raise ValueError('index out of range')
        if index == -1:
            return
        for i in self.tree[index]:
            yield i

    def get_index_path_by_name(self, name):
        index = self.names[name]
        for path_element in self.get_index_path_by_index(index):
            yield path_element

    def get_name(self, index):
        if index < -1 or index >= len(self.tree):
            raise ValueError('index is out of range')
        for name, i in self.names.items():
            if i == index:
                return name

    def dump(self):
        self._data['index'] = self.index
        self._data['tree'] = self.tree
        self._data['names'] = self.names
        self._data['add'] = self._add
        with open(self.json_path, 'w+') as file:
            json.dump(self._data, file, indent=4)

    def load(self):
        with open(self.json_path, 'r') as file:
            self._data = json.load(file)
        self.index = self._data['index']
        self.tree = self._data['tree']
        self.names = self._data['names']
        self._add = self._data['add']
