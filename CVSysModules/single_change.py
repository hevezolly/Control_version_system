import struct
from CVSysModules.change_step import ChangeStep


class Change:
    def __init__(self, *steps):
        self.steps = []
        self.add_steps(*steps)

    @staticmethod
    def from_bytes(b, start_index=0):
        number, = struct.unpack('i', b[start_index: start_index + 4])
        current_index = start_index+4
        change = Change()
        for i in range(number):
            length, = struct.unpack('i', b[current_index: current_index + 4])
            step = ChangeStep.from_bytes(b, current_index + 4)
            change.add_steps(step)
            current_index += length + 4
        return change

    def add_steps(self, *steps):
        for step in steps:
            self.steps.append(step)

    def apply_to(self, origin):
        for step in self.steps:
            step.apply(origin)

    def encode(self):
        b = struct.pack('i', len(self.steps))
        for step in self.steps:
            encoded_step = step.encode()
            length = struct.pack('i', len(encoded_step))
            b += length + encoded_step
        return b
