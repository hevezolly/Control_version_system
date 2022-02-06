import unittest
from CVSysModules.change_step import ChangeStep
from CVSysModules.file_change import FileChange, FCT
from CVSysModules.dir_change import DirChange, DCT


class StepChangeTest(unittest.TestCase):
    def test_encode1(self):
        step = ChangeStep(".\\fefea\\ffekfef\\rrr.test",
                          FileChange(2, 3, FCT.DELETE), True)
        encoded = step.encode()
        new = bytes(3) + encoded + bytes(6)
        decoded = ChangeStep.from_bytes(new, 3)
        self.assertEqual(step.target, decoded.target)
        self.assertIs(FileChange, type(decoded.change))
        self.assertEqual(step.change.type, decoded.change.type)
        self.assertEqual(step.change.index, decoded.change.index)
        self.assertEqual(step.change.data, decoded.change.data)

    def test_encode2(self):
        step = ChangeStep(".\\fefea\\ffekfef\\rrr.test",
                          DirChange("asdde", DCT.RENAME, "eew"), True)
        encoded = step.encode()
        new = bytes(6) + encoded + bytes(2)
        decoded = ChangeStep.from_bytes(new, 6)
        self.assertEqual(step.target, decoded.target)
        self.assertIs(DirChange, type(decoded.change))
        self.assertEqual(step.change.type, decoded.change.type)
        self.assertEqual(step.change.name, decoded.change.name)
        self.assertEqual(step.change.new_name, decoded.change.new_name)
