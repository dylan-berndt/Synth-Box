from MathBasic import *
from ui import *
import colorsys
from random import randint
import numpy as np

sampleRate = 44100


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

        self.data = np.zeros(44100)

        Device.all_devices.append(self)

    def focus(self):
        pass

    def unfocus(self):
        pass

    def process(self):
        return self.inputs[0].process()

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

    def process(self):
        return self.inputs[0].process() + self.inputs[1].process()


class Amp(Device):
    def __init__(self, position):
        self.position = position

        self.ui = [NumberEdit("Amplitude", 1)]

        super().__init__(1, 1, Vector2(2, 2))

    def process(self):
        return self.ui[0].value * self.inputs[0].process()


class Attack(Device):
    def __init__(self, position):
        self.position = position
        super().__init__(1, 1, Vector2(2, 2))

        self.ui = [NumberEdit("Attack Time", 0.1)]

    def process(self):
        data = self.inputs[0].process()
        space = np.ones(len(data) - int(sampleRate * self.ui[0].value))
        attack = np.linspace(0, 1, int(sampleRate * self.ui[0].value))
        return np.append(attack, space) * data


class Decay(Device):
    def __init__(self, position):
        self.position = position
        super().__init__(1, 1, Vector2(2, 2))

        self.ui = [NumberEdit("Decay Time", 0.3)]

    def process(self):
        data = self.inputs[0].process()
        samples = np.linspace(0, 1, len(data))
        decay = np.exp(-samples / self.ui[0].value)
        return decay * data


class Sequencer(Device):
    def __init__(self, position):
        self.position = position
        self.sequence = []

        self.switch = True

        super().__init__(1, 1, Vector2(2, 2))

    def process(self):
        data = self.inputs[0].process()
        return sum(data if self.sequence[i] else data * 0 for i in range(len(self.sequence)))


class Beatbox(Device):
    def __init__(self, position):
        self.position = position
        super().__init__(1, 1, Vector2(3, 3))

        self.ui = [Button("Edit...", None)]

    def process(self):
        pass


class Oscillator(Device):
    def __init__(self, position):
        super().__init__(0, 1, Vector2(2, 2))

        self.position = position
        self.ui = [NumberEdit("Signal 1", 440), NumberEdit("Signal 2", 0)]

        self.switch = True

    def process(self):
        samples = np.linspace(0, 1, sampleRate)
        return np.sin(2 * np.pi * self.ui[0].value * samples)


class Cable:
    def __init__(self):
        self.left = None
        self.right = None

        color = colorsys.hsv_to_rgb(randint(0, 100) / 100, 0.8, 0.9)

        self.color = [255 * channel for channel in color]

    def opposite(self, start: Device):
        return self.left if self.left != start else self.right

