from CVSysModules.change_step import ChangeStep, DirChange, DCT, FileChange
from CVSysModules.file_change import FCT
from CVSysModules.single_change import Change
import unittest


class ChangeTest(unittest.TestCase):

    def test_encode(self):
        s1 = ChangeStep("asdf\\eew",
                        FileChange(2, bytes([1, 3, 2]), FCT.INSERT), False)
        s2 = ChangeStep("asf\\ee", FileChange(5, 3, FCT.DELETE), False)
        s3 = ChangeStep("easf\\ee", DirChange('aewew', DCT.RENAME, 'ffee'),
                        False)
        s4 = ChangeStep("f\\ee", DirChange('aew', DCT.ADD_DIR), False)
        s5 = ChangeStep("ease", DirChange('weew', DCT.REMOVE_FILE), False)
        change = Change(s1, s2, s3, s4, s5)
        encoded = change.encode()
        new_encoded = bytes(4) + encoded + bytes(6)
        decoded = Change.from_bytes(new_encoded, 4)
        for i in range(5):
            self.assertEqual(change.steps[i].target, decoded.steps[i].target)
            self.assertEqual(change.steps[i].change.type,
                             decoded.steps[i].change.type)
