from CVSysModules.cv_system import CVSystem
from CVSysModules.dir_change import DCT
import sys
import os
import argparse


def get_parser():
    main_parser = argparse.ArgumentParser()

    main_parser.add_argument('DIRECTORY', help='path to working directory')

    main_parser.add_argument('-s', '--silent',
                             action='store_true',
                             default=False,
                             help='activates silent mode')

    subparsers = main_parser.add_subparsers(help='list of commands',
                                            dest='command')

    init_parser = subparsers.add_parser('init',
                                        help='init control version system',
                                        description='init control ' +
                                                    'version system')
    init_parser.add_argument('-c', '--clear', action='store_true',
                             default=False,
                             help='if used, init clears given DIRECTORY' +
                                  'or creates it if DIRECTORY doesn\'t exist')

    pull_parser = subparsers.add_parser('pull', help='pulls commit',
                                        description='pulls commit')
    pull_parser.add_argument('-i', '--index', nargs=1, metavar='INDEX',
                             help='pulls commit by INDEX')
    pull_parser.add_argument('-n', '--name', nargs=1, metavar='NAME',
                             help='pulls commit by NAME')
    pull_parser.add_argument('-b', '--back', action='store_true',
                             default=False,
                             help='pulls previous element in tree')
    pull_parser.add_argument('-B', '--backTime', action='store_true',
                             default=False,
                             help='pulls previous commit, made by user')

    commit_parser = subparsers.add_parser('commit',
                                          help='commits all changes from add',
                                          description='commits all ' +
                                                      'changes from add')
    commit_parser.add_argument('-n', '--name', nargs=1, metavar='NAME',
                               help='set commit name as NAME')

    state_parser = subparsers.add_parser('state',
                                         help='displays cvs information',
                                         description='displays short' +
                                                     ' change information')
    state_parser.add_argument('-a', '--with_add', action='store_true',
                              default=False,
                              help='displays adds with changes')
    state_parser.add_argument('-f', '--full', action='store_true',
                              default=False,
                              help='displays full change information')
    state_parser.add_argument('-t', '--tree', action='store_true',
                              default=False,
                              help='shows commit tree')

    dis_parser = subparsers.add_parser('discard',
                                       help='discards change',
                                       description='''discards change by index.
                                           you can chack index by using
                                           CVS.py DIRECTORY state''')
    dis_parser.add_argument('pointer',
                            help='index of change or name of' +
                                 ' file (if used with -n)')
    dis_parser.add_argument('-n', '--name', action='store_true',
                            default=False,
                            help='makes pointer use names insted of indexes')

    add_parser = subparsers.add_parser('add',
                                       help='adds change',
                                       description='shows add list')
    add_parser.add_argument('-i', '--index', nargs=1, metavar='INDEX',
                            help='adds change by its index' +
                                 ' in CVS.py DIRECTORY state')
    add_parser.add_argument('-n', '--name', nargs=1, metavar='NAME',
                            help='adds change by file name')
    add_parser.add_argument('-a', '--all', action='store_true', default=False,
                            help='adds all changes')

    stash_parser = subparsers.add_parser('stash',
                                         help='controls stash',
                                         description='shows stashed files')
    stash_parser.add_argument('-a', '--add', nargs=1, metavar='PATH',
                              help='stash file by PATH')
    stash_parser.add_argument('-d', '--delete', action='store_true',
                              default=False,
                              help='removes file from stash, if used with' +
                                   ' --restore, deletes file after saving')
    stash_parser.add_argument('-e', '--empty', action='store_true',
                              default=False,
                              help='clears stash')
    stash_parser.add_argument('-r', '--restore', nargs='?',
                              metavar='PATH_TO_SAVE', const='',
                              help='restores stashed file to existing' +
                                   ' PATH_TO_SAVE. If no ' +
                                   'arguments were done, uses saved file name')
    stash_parser.add_argument('-n', '--name', nargs=1, metavar='NAME',
                              help='used to choose stashed file by its' +
                                   ' stashed name')
    stash_parser.add_argument('-c', '--create', action='store_true',
                              default=False,
                              help='when used with -r, creates ' +
                                   'PATH_TO_SAVE if its not exist')
    stash_parser.add_argument('-i', '--index', action='store_true',
                              default=False,
                              help='allows to use index index CVS.py ' +
                                   'DIRECTORY state as PATH in stash --add')

    merge_parser = subparsers.add_parser('merge',
                                         help='merges changes',
                                         description='merges changes')

    merge_parser.add_argument('-c', '--conflicts', action='store_true',
                              default=False,
                              help='shows unsolved conflicts')

    merge_parser.add_argument('-n', '--name', nargs=1, metavar='NAME',
                              help='name of merging commit. ' +
                                   'using to merge with current commit')

    merge_parser.add_argument('-r', '--reversed', action='store_true',
                              default=False,
                              help='changes priority from ' +
                                   'current commit to merging')

    merge_parser.add_argument('-f', '--forget', action='store_true',
                              default=False,
                              help='makes CVS forget information about'
                                   'conflicts')
    return main_parser


class ConsoleInterface:
    def __init__(self, args):
        self.args = args
        self.silent = args.silent
        self.cvs = self.get_cvs()
        self.commands = {'pull': self.process_pull,
                         'add': self.process_add,
                         'merge': self.process_merge,
                         'stash': self.process_stash,
                         'state': self.process_state,
                         'discard': self.process_discard,
                         'commit': self.process_commit}

    def out(self, massage):
        if not self.silent:
            print(massage)

    def show_exit(self, massage=None):
        self.out('Error: incorrect input')
        if massage is not None:
            self.out(massage)
        self.out('use CVS.py -h to see help massage')
        sys.exit(1)

    def get_cvs(self):
        init = False
        clear = False
        if self.args.command == 'init':
            init = True
            clear = self.args.clear
        try:
            cvs = CVSystem(self.args.DIRECTORY, init, clear)
        except Exception as e:
            self.out(e)
            sys.exit(1)
        return cvs

    def process_pull(self):
        try:
            if self.args.index is not None:
                self.cvs.pull(int(self.args.index[0]) - 1)
            elif self.args.name is not None:
                self.cvs.pull_name(self.args.name[0])
            elif self.args.back:
                self.cvs.go_back()
            elif self.args.backTime:
                self.cvs.go_previous()
            else:
                self.show_exit(
                    'usage: CVS.py DIRECTORY pull [-h] ' +
                    '[-i INDEX] [-n NAME] [-b] [-B]')
        except ValueError as e:
            self.out(e)

    def process_commit(self):
        if self.args.name is not None:
            name = self.args.name[0]
        else:
            name = input('print commit name: ')
        try:
            self.cvs.push(name)
        except ValueError as e:
            self.out(e)

    def process_state(self):
        if self.args.full:
            was = False
            for element in self.cvs.get_big_changes(self.args.with_add):
                was = True
                if element['t'] is None:
                    self.out(f'file {element["n"]} was changed')
                else:
                    if element['t'] == DCT.ADD_FILE:
                        self.out(f'file {element["n"]} was added')
                    if element['t'] == DCT.REMOVE_FILE:
                        self.out(f'file {element["n"]} was removed')
                    if element['t'] == DCT.RENAME:
                        self.out(f'file {element["n"]} renamed')
                    if element['t'] == DCT.ADD_DIR:
                        self.out(f'directory {element["n"]} was added')
                    if element['t'] == DCT.REMOVE_DIR:
                        self.out(f'directory {element["n"]} was removed')
            if not was:
                self.out('no changes were found')
        elif self.args.tree:
            self.cvs.get_tree_drawer().draw(self.silent)
        else:
            was = False
            for element in self.cvs.get_small_changes(self.args.with_add):
                was = True
                if element['i'] is None:
                    self.out(f'{element["n"]} (ADDED)')
                else:
                    self.out(f'{element["i"]}. {element["n"]}')
            if not was:
                self.out('no changes were found')

    def process_discard(self):
        try:
            if self.args.name:
                self.cvs.discard_by_name(self.args.pointer)
            else:
                self.cvs.discard_by_index(int(self.args.pointer) - 1)
        except ValueError as e:
            self.out(e)

    def process_add(self):
        if self.args.index is not None:
            try:
                self.cvs.add_index(int(self.args.index[0]) - 1)
            except ValueError as e:
                self.out(e)
        elif self.args.name is not None:
            self.cvs.add_name(self.args.name[0])
        elif self.args.all:
            try:
                self.cvs.add_all()
            except ValueError as e:
                self.out(e)
        else:
            was = False
            for element in self.cvs.show_add():
                was = True
                self.out(f'{element["i"]}. {element["n"]}')
            if not was:
                self.out("add list is empty")

    def process_stash(self):
        if self.args.name is not None:
            name = self.args.name[0]
        elif self.args.add is not None \
                or self.args.delete \
                or self.args.restore is not None:
            name = input('print stashed name: ')
        if self.args.add is not None:
            if self.args.index:
                index = int(self.args.add[0]) - 1
                try:
                    self.cvs.stash_by_index(index, name, self.args.delete)
                except ValueError as e:
                    self.out(e)
            else:
                try:
                    self.cvs.stash(self.args.add[0], name, self.args.delete)
                except ValueError as e:
                    self.out(e)
                except FileNotFoundError as e:
                    self.out(e)
        elif self.args.restore is not None:
            try:
                self.cvs.restore(self.args.restore, self.args.delete,
                                 self.args.create, name)
            except FileNotFoundError as e:
                self.out(e)
        elif self.args.delete:
            try:
                self.cvs.remove_from_stash(name)
            except ValueError as e:
                self.out(e)
        elif self.args.empty:
            self.cvs.clear_stash()
        else:
            was = False
            for element in self.cvs.show_stash():
                was = True
                self.out(f'{element["k"]}: {element["p"]} saved ' +
                         f'in the commit {element["n"]}')
            if not was:
                self.out("stash is empty")

    def print_collisions(self, collisions):
        for collision in collisions:
            for line in collision.get_str(self.cvs.storage.origin_path):
                self.out(line)

    def process_merge(self):
        if self.args.name is not None:
            try:
                collisions = self.cvs.merge(self.args.name[0],
                                            self.args.reversed)
            except ValueError as e:
                self.out(e)
                sys.exit(1)
            if not collisions:
                self.out('merge was successfully finished')
                self.out('no collision was detected')
            else:
                self.out('merge was finished with collisions')
                self.out('collisions:')
                self.print_collisions(collisions)
        if self.args.forget:
            if self.cvs.forget_conflicts():
                self.out("collisions were forgotten")
        if (self.args.name is None
                and not self.args.forget
                and self.args.conflicts):
            collisions = self.cvs.update_conflicts()
            if collisions:
                self.print_collisions(collisions)
            else:
                self.out('no collisions were detected')

    def start(self):
        if self.args.command in self.commands:
            self.commands[self.args.command]()
        elif self.args.command != 'init':
            self.show_exit()


if __name__ == '__main__':
    parser = get_parser()
    interface = ConsoleInterface(parser.parse_args())
    interface.start()
