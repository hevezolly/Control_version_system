from CVSysModules.dir_change import DirChange, DCT
from CVSysModules.dif_controller import Difference, SPACE_SEP
from CVSysModules.change_step import ChangeStep
from CVSysModules.file_change import FileChange, FCT, ENCODING
from CVSysModules.dif_controller import TEXT_EXTENSIONS
import re
import difflib
import shutil
import struct
import os

CONFLICT_START = b'>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>'
CONFLICT_MIDDLE = b'=============================='
CONFLICT_END = b'<<<<<<<<<<<<<<<<<<<<<<<<<<<<<'

pattern = CONFLICT_START + rb'.+?' + CONFLICT_MIDDLE + rb'.+?' + CONFLICT_END

MIN_BYTE_DISTANCE = 0
HASH_BASE = 3571


class MergeBase:
    def __init__(self, origin_steps):
        self.d0 = VirtDir(True, True, 0)
        self.d1 = VirtDir(True, True, 1)
        for step in origin_steps:
            self.d0.add_step(step, True)
            self.d1.add_step(step, True)
        self.result = None

    def add_step(self, step, branch):
        if branch == 0:
            self.d0.add_step(step, False)
        elif branch == 1:
            self.d1.add_step(step, False)
        else:
            raise ValueError('branch is out of range')

    def merge(self, simulation_space, ordered):
        if not ordered:
            self.result = VirtDir.merge(self.d0, self.d1, simulation_space)
        else:
            self.result = VirtDir.merge(self.d1, self.d0, simulation_space)

    def get_conflicts(self):
        if self.result is None:
            raise ValueError('merge was not done')
        return self.result.get_conflicts()

    def get_steps(self):
        if self.result is None:
            raise ValueError('merge was not done')
        return list(self.result.get_steps())


class VirtDir:
    def __init__(self, is_origin, is_dir, branch, is_binary=True, name=''):
        self.children = []
        self.is_binary = is_binary
        self.content = VirtFile(name, is_binary)
        self.create_step = None
        self.is_origin = is_origin
        self.is_dir = is_dir
        self.conflicts = ConflictInfo()
        self.name = name
        self.branch = branch
        self.parent = None

    def get_conflicts(self):
        result = []
        if not self.conflicts.solved:
            self.conflicts.name = self.name
            return [self.conflicts]
        for child in self.children:
            result.extend(child.get_conflicts())
        return result

    def add_step(self, step, is_origin=False):
        if isinstance(step.change, DirChange):
            self._add_dir_step(step, is_origin)
        elif isinstance(step.change, FileChange):
            self._add_file_step(step, is_origin)
        else:
            raise ValueError('incorrect change type')

    def _add_file_step(self, step, is_origin):
        name = step.get_relative_target()
        c = self.get_child_by_name(name)
        if name == c.name:
            if c.is_dir:
                raise TypeError('trying to add file step in dir')
            if is_origin:
                c.content.add_origin(step)
            else:
                c.content.add_step(step)
            return
        c._add_file_step(step, is_origin)

    def _add_dir_step(self, step, is_origin):
        name = step.get_relative_target()
        if step.change.type in (DCT.ADD_DIR, DCT.ADD_FILE):
            directory = VirtDir(is_origin,
                                step.change.type == DCT.ADD_DIR,
                                self.branch, step.is_binary,
                                name)
            directory.create_step = step
            self.add_child(directory)
        elif step.change.type in (DCT.REMOVE_DIR, DCT.REMOVE_FILE):
            self.remove_child(name)
        elif step.change.type == DCT.RENAME:
            old_name = step.get_relative_target()
            new_name = step.get_rename_target()
            self.rename(old_name, new_name)

    def copy(self):
        copy = VirtDir(self.is_origin,
                       self.is_dir,
                       self.branch,
                       self.is_binary,
                       self.name)
        copy.children = [c.copy() for c in self.children]
        copy.create_step = self.create_step.copy() \
            if self.create_step is not None else None
        copy.parent = self.parent
        copy.is_origin = False
        copy.content = self.content.copy()
        return copy

    def rename(self, old_name, new_name):
        c = self.get_child_by_name(old_name)
        if c.name == old_name:
            if c.is_origin:
                new_c = c.copy()
                c.parent.children.append(new_c)
                new_c.rename(old_name, new_name)
            else:
                c.name = new_name
                c.create_step.set_relative_target(new_name)
                if c.is_dir:
                    for child in c.children:
                        _, head = os.path.split(child.name)
                        new_child_name = os.path.join(new_name, head)
                        child.rename(child.name, new_child_name)
                else:
                    c.content.rename(new_name)
        else:
            c.rename(old_name, new_name)

    def get_child_by_name(self, name):
        tail = name
        if tail == self.name:
            return self
        if not self.is_dir:
            raise TypeError('trying to get children of file')
        while tail != self.name:
            for c in self.children:
                if c.name == tail:
                    return c
                if not c.is_dir:
                    continue
            tail, head = os.path.split(tail)
        raise ValueError('can\'t get child')

    def add_child(self, child):
        c = self.get_child_by_name(os.path.split(child.name)[0])
        if c is self:
            self.children.append(child)
            child.parent = self
            return
        c.add_child(child)

    def remove_child(self, name):
        tail, head = os.path.split(name)
        c = self.get_child_by_name(tail)
        if c is self:
            for d in self.children:
                if d.name == name:
                    self.children.remove(d)
                    break
            return
        c.remove_child(name)

    def get_steps(self):
        if self.create_step is not None:
            yield self.create_step
        if self.is_dir:
            for child in self.children:
                for s in child.get_steps():
                    yield s
        else:
            for step in self.content.get_steps():
                yield step

    def __contains__(self, item):
        if not self.is_dir:
            return False
        else:
            for child in self.children:
                if child.name == item:
                    return True
            return False

    def __getitem__(self, item):
        if not self.is_dir:
            raise TypeError('can\'t get child of file')

        for child in self.children:
            if child.name == item:
                return child
        raise ValueError('no such child in dir')

    @staticmethod
    def merge(one, other, simulation_space):
        if one.name != other.name:
            raise ValueError('can\'t merge different dirs')
        if one.is_dir != other.is_dir:
            raise ValueError('file and directory has same name')
        result = one.copy()
        if one.is_dir:
            new_children = []
            for child in one.children:
                if child.name in other:
                    c = VirtDir.merge(child,
                                      other[child.name],
                                      simulation_space)
                    c.parent = result
                    new_children.append(c)
                else:
                    child.parent = result
                    new_children.append(child)
            for child in other.children:
                if child.name not in one:
                    child.parent = result
                    new_children.append(child)
            result.children = list(new_children)
        else:
            r1, r2 = VirtFile.merge(one.content,
                                    other.content,
                                    simulation_space)
            result.content, result.conflicts = r1, r2
        return result


class VirtFile:
    LEFT = 'left.sim'
    RIGHT = 'right.sim'
    ORIGIN = 'origin.sim'

    def __init__(self, name, is_binary):
        self.origin = []
        self.changes = []
        self.name = name
        self.is_binary = is_binary

    def add_origin(self, step):
        new_step = step.copy()
        new_step.set_relative_target('')
        self.origin.append(new_step)

    def add_step(self, step):
        new_step = step.copy()
        new_step.set_relative_target('')
        self.changes.append(new_step)

    def rename(self, new_name):
        self.name = new_name

    @staticmethod
    def clear_simulation(simulation_space):
        if not os.path.isdir(simulation_space):
            os.mkdir(simulation_space)
            return
        while True:
            try:
                shutil.rmtree(simulation_space)
                break
            except OSError:
                continue
        os.mkdir(simulation_space)

    def simulate_origin(self, path):
        open(path, 'w+').close()
        for step in self.origin:
            step.change.apply_to_file(path)

    def simulate_file(self, path):
        self.simulate_origin(path)
        for step in self.changes:
            step.change.apply_to_file(path)

    def get_steps(self):
        for step in self.origin:
            step.set_relative_target(self.name)
            yield step
        for step in self.changes:
            step.set_relative_target(self.name)
            yield step

    def copy(self):
        new = VirtFile(self.name, self.is_binary)
        new.origin = [s.copy() for s in self.origin]
        new.changes = [s.copy() for s in self.changes]
        return new

    @staticmethod
    def numerate(o_lines, l_lines, r_lines):
        for i in range(len(o_lines)):
            o_lines[i] = (o_lines[i], i)
        for i in range(len(l_lines)):
            l_lines[i] = (l_lines[i], i)
        for i in range(len(r_lines)):
            r_lines[i] = (r_lines[i], i)

    @staticmethod
    def denumerate(result):
        for i in range(len(result)):
            if not isinstance(result[i], tuple):
                continue
            result[i] = result[i][0]

    @staticmethod
    def _merge_bytes(o_lines, l_lines, r_lines):
        conflict = ConflictInfo()
        for i in range(len(o_lines)):
            if o_lines.count(o_lines) > 1:
                pass
        lines = []
        length = 0
        difference = difflib.SequenceMatcher(None, l_lines, r_lines)
        for tag, i1, i2, j1, j2 in difference.get_opcodes():
            left = l_lines[i1:i2]
            right = r_lines[j1:j2]
            if tag == 'delete':
                for i in range(i1, i2):
                    if i >= len(o_lines) or l_lines[i] != o_lines[i]:
                        lines.append(l_lines[i])
                        length += 1
            if tag == 'insert':
                for i in range(j1, j2):
                    if i >= len(o_lines) or r_lines[i] != o_lines[i]:
                        lines.append(r_lines[i])
                        length += 1
            if tag == 'replace':
                from_left = []
                from_right = []
                i = 0
                while i < max(len(left), len(right)):
                    add = True
                    if i == len(left):
                        lines.extend(right[i:])
                        length += len(right[i:])
                        break
                    if i == len(right):
                        lines.extend(left[i:])
                        length += len(left[i:])
                        break

                    if left[i] in o_lines:
                        lines.append(right[i])
                        length += 1
                    elif right[i] in o_lines:
                        lines.append(left[i])
                        length += 1
                    elif left[i] == right[i]:
                        lines.append(left[i])
                        length += 1
                    else:
                        j = i
                        for j in range(i, min(len(left), len(right))):
                            if left[j] in o_lines or right[j] in o_lines:
                                break
                            from_left.append(left[j])
                            from_right.append(right[j])
                            add = False
                        else:
                            add = True
                        length += len(from_left)
                        i = j
                        conflict.add(len(lines))
                        lines.append(CONFLICT_START)
                        lines.extend(from_left)
                        lines.append(CONFLICT_MIDDLE)
                        lines.extend(from_right)
                        lines.append(CONFLICT_END)
                        from_right = []
                        from_left = []
                    if add:
                        i += 1
            if tag == 'equal':
                lines.extend(l_lines[i1:i2])
                length += len(l_lines[i1:i2])
        return lines, conflict, length

    @staticmethod
    def merge(one, other, simulation_space):
        if one.name != other.name:
            raise ValueError('can\'t merge two different files')

        if one.is_binary != other.is_binary:
            raise ValueError('can\'t merge binary file with non binary')

        if one.is_binary:
            return one, ConflictInfo()
        VirtFile.clear_simulation(simulation_space)
        origin = os.path.join(simulation_space, VirtFile.ORIGIN)
        left = os.path.join(simulation_space, VirtFile.LEFT)
        right = os.path.join(simulation_space, VirtFile.RIGHT)
        one.simulate_origin(origin)
        one.simulate_file(left)
        other.simulate_file(right)
        with open(origin, 'br') as o_f:
            o_lines = o_f.read().split(SPACE_SEP)
        with open(left, 'br') as l_f:
            l_lines = l_f.read().split(SPACE_SEP)
        with open(right, 'br') as r_f:
            r_lines = r_f.read().split(SPACE_SEP)

        resulted_lines, conflict, length = VirtFile._merge_bytes(
            o_lines, l_lines, r_lines)
        if not min(len(l_lines), len(r_lines)) <= length <= max(len(l_lines),
                                                                len(r_lines)):
            VirtFile.numerate(o_lines, l_lines, r_lines)
        resulted_lines, conflict, length = VirtFile._merge_bytes(
            o_lines, l_lines, r_lines)
        VirtFile.denumerate(resulted_lines)
        resulted_bytes = b''
        for i in range(len(resulted_lines)):
            resulted_bytes += resulted_lines[i]
            if i < len(resulted_lines) - 1:
                resulted_bytes += SPACE_SEP

        step = ChangeStep('', FileChange(0, resulted_bytes, FCT.INSERT), False)
        new_virt_file = VirtFile(one.name, one.is_binary)
        new_virt_file.add_origin(step)
        return new_virt_file, conflict


class ConflictInfo:
    def __init__(self, *poses):
        self.poses = []
        self.name = ''
        self.add(*poses)

    @property
    def solved(self):
        return len(self.poses) == 0

    def update(self, path_to_origin):
        path = os.path.join(path_to_origin, self.name)
        if not os.path.isfile(path):
            raise ValueError(f"{path} is not file")
        if self.solved:
            return
        new_poses = []
        with open(path, 'rb') as file:
            data = file.read()
            result = re.findall(pattern, data, re.DOTALL)
            start_index = 0
            for r in result:
                byte_pos = data.find(r, start_index)
                line_count = data.count(SPACE_SEP, 0, byte_pos)
                new_poses.append(line_count)
                start_index += byte_pos + len(r)
        self.poses = new_poses

    @staticmethod
    def encode(conflicts):
        data = b''
        for conflict in conflicts:
            local_data = b''
            encoded = conflict.name.encode(ENCODING)
            local_data += struct.pack('h', len(encoded))
            local_data += encoded
            local_data += struct.pack('h', len(conflict.poses))
            for pos in conflict.poses:
                local_data += struct.pack('i', pos)
            data += local_data
        return data

    @staticmethod
    def decode(data):
        index = 0
        while index < len(data) - 1:
            name_len, = struct.unpack('h', data[index: index + 2])
            index += 2
            name = data[index: index + name_len].decode(ENCODING)
            index += name_len
            number, = struct.unpack('h', data[index:index + 2])
            index += 2
            poses = struct.unpack('i' * number, data[index:index + 4 * number])
            conflict = ConflictInfo(*poses)
            conflict.name = name
            yield conflict
            index += 4 * number

    def get_str(self, path):
        for pos in self.poses:
            yield f'conflict in file {os.path.join(path, self.name)} ' \
                  f'at line {pos + 1}'

    def __bool__(self):
        return not self.solved

    def add(self, *poses):
        for pos in poses:
            self.poses.append(pos)
        self.poses.sort()
