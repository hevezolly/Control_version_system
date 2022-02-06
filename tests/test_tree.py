import unittest
import os
from CVSysModules.tree import Tree


class TreeTest(unittest.TestCase):
    FILE = 'asdf.json'

    def setUp(self) -> None:
        if os.path.isfile(self.FILE):
            os.remove(self.FILE)
        open(self.FILE, 'w+').close()

    def tearDown(self) -> None:
        if os.path.isfile(self.FILE):
            os.remove(self.FILE)

    def test_create(self):
        tree1 = Tree(self.FILE, create_new=True)
        tree1.index = 12
        tree1.tree.append([1, 2, 3])
        tree1.dump()
        tree2 = Tree(self.FILE)
        self.assertEqual(tree1.index, tree2.index)
        self.assertListEqual(tree1.tree, tree2.tree)

    def test_add_branch(self):
        tree = Tree(self.FILE, create_new=True)
        n = 10
        for i in range(n):
            tree.index = tree.add_branch(str(i))
        tree.index = 1
        tree.add_branch(str(n))
        for i in range(n):
            self.assertListEqual([j for j in range(i + 1)], tree.tree[i])
        self.assertListEqual([0, 1, n], tree.tree[n])

    def test_add(self):
        tree = Tree(self.FILE, create_new=True)
        origin = os.path.join('asfd', 'zxcv', 'qwer', 'kkkr')
        path = os.path.join(origin, 'ffee', 'wqe', 'ffefs')
        tree.add_path(path, origin)
        real_path = os.path.join('ffee', 'wqe', 'ffefs')
        self.assertListEqual(['ffee', os.path.join('ffee', 'wqe'), real_path],
                             tree.add)
