from MathBasic import *
from ui import *
import colorsys
from random import randint


class Device:
    all_devices = []

    def __init__(self, inputs, outputs, size):
        self.inputs = []
        self.outputs = []
        self.size = size

        self.input_positions = inputs
        self.output_positions = outputs

        self.ui = []
        self.switch = None

        Device.all_devices.append(self)

    def focus(self):
        pass

    def unfocus(self):
        pass

    def transform(self):
        pass

    def delete(self):
        Device.all_devices.remove(self)


class Speaker(Device):
    def __init__(self, position):
        self.position = position
        self.switch = True

        super().__init__(1, 0, Vector2(2, 2))


class Splitter(Device):
    def __init__(self, position):
        self.position = position

        super().__init__(1, 2, Vector2(2, 2))


class Adder(Device):
    def __init__(self, position):
        self.position = position

        super().__init__(2, 1, Vector2(2, 2))

    def transform(self):
        pass


class Sequencer(Device):
    def __init__(self, position):
        self.position = position
        self.sequence = []

        self.switch = True

        super().__init__(1, 1, Vector2(2, 2))


class Oscillator(Device):
    def __init__(self, position):
        self.position = position
        self.ui = [NumberEdit("Signal 1", 400), NumberEdit("Signal 2", 0)]

        self.switch = True

        super().__init__(0, 1, Vector2(2, 2))

    def transform(self):
        pass


class Cable:
    def __init__(self):
        self.left = None
        self.right = None

        color = colorsys.hsv_to_rgb(randint(0, 100) / 100, 0.8, 0.9)

        self.color = [255 * channel for channel in color]

    def opposite(self, start: Device):
        return self.left if self.left != start else self.right

