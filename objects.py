import tkinter

from MathBasic import *
from ui import *
import colorsys
from random import randint
import numpy as np
import tkinter.filedialog as file
import soundfile as sf
import librosa
from screen import Sprite
import os

sample_rate = 44100

sprite_paths = os.listdir("Resources/Devices/")
sprite_paths = [os.path.join("Resources/Devices/", path) for path in sprite_paths]


class Object:
    all_objects = []

    def __init__(self):
        if not hasattr(self, "size"):
            self.size = Vector2(0.8, 1)
        if not hasattr(self, "position"):
            self.position = Vector2(0, 0)
        if not hasattr(self, "velocity"):
            self.velocity = Vector2(0, 0)

        self.sprite = Sprite(sprite_paths[spriteIndex.index(type(self))])

        Object.all_objects.append(self)


class Device(Object):
    def __init__(self, inputs, outputs, size=None):
        self.inputs = []
        self.outputs = []
        self.size = size if size is not None else Vector2(1.6, 2)

        self.input_positions = inputs
        self.output_positions = outputs

        if not hasattr(self, "ui"):
            self.ui = []
        self.switch = None

        super().__init__()

    def focus(self):
        pass

    def unfocus(self):
        pass

    def process(self):
        return self.inputs[0].process()


class Speaker(Device):
    def __init__(self, position):
        self.position = position
        self.switch = True

        super().__init__(1, 0)


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

        super().__init__(1, 1)

    def process(self):
        return self.ui[0].value * self.inputs[0].process()


class Pitch(Device):
    def __init__(self, position):
        self.position = position

        self.ui = [NumberEdit("Semitones", 12)]

        super().__init__(1, 1, Vector2(2, 2))

    def process(self):
        data = self.inputs[0].process()
        s = 2 ** (self.ui[0].value / 12)
        return librosa.effects.pitch_shift(data, sr=sample_rate, n_steps=s)


class Attack(Device):
    def __init__(self, position):
        self.position = position
        super().__init__(1, 1, Vector2(2, 2))

        self.ui = [NumberEdit("Attack Time", 0.1)]

    def process(self):
        data = self.inputs[0].process()
        space = np.ones(len(data) - int(sample_rate * self.ui[0].value))
        attack = np.linspace(0, 1, int(sample_rate * self.ui[0].value))
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

        self.ui = [NumberEdit("BPM", 120), Button("Edit...", None)]

        super().__init__(1, 1, Vector2(2, 2))

    def process(self):
        data = self.inputs[0].process()
        beat_length = int(sample_rate * (60 / self.ui[0].value))
        length = len(self.sequence) * beat_length
        sequence = np.zeros(length)
        for v, value in enumerate(self.sequence):
            i = v * beat_length
            if i + len(data) >= length:
                difference = i + len(data) - length
                sequence[i:i + len(data)] += data[0:len(data) - difference] * value
                sequence[0:difference] += data[len(data) - difference:len(data)] * value
            else:
                sequence[i:i + len(data)] += data * value
        return sequence


class Beatbox(Device):
    def __init__(self, position):
        self.position = position
        super().__init__(1, 1)

        self.ui = [NumberEdit("BPM", 120), Button("Edit...", None)]

    def process(self):
        pass


class Oscillator(Device):
    def __init__(self, position):
        super().__init__(0, 1)

        self.position = position
        self.ui = [NumberEdit("Signal 1", 440), NumberEdit("Signal 2", 0)]

        self.switch = True

    def process(self):
        samples = np.linspace(0, 1, sample_rate)
        signal1 = np.sin(2 * np.pi * self.ui[0].value * samples)
        signal2 = np.sin(2 * np.pi * self.ui[1].value * samples)
        return signal1 + signal2


class Sample(Device):
    def __init__(self, position):
        dialog = tkinter.Tk()
        dialog.withdraw()
        self.path = file.askopenfilename(title="Open Sample", filetypes=[("Audio Files", ".wav .ogg .mp3")])

        if not self.path:
            del self
            return

        super().__init__(0, 1)

        self.data, data_rate = sf.read(self.path)

        if len(self.data.shape) > 1:
            self.data = np.mean(self.data, axis=1)

        if data_rate != sample_rate:
            target = sample_rate / data_rate
            length = int(len(self.data) * target)
            resample = np.interp(np.linspace(0, len(self.data), length, endpoint=False),
                                np.arange(len(self.data)), self.data)
            self.data = resample

        self.position = position
        self.ui = [Button("Select...", None)]

        self.switch = True

    def process(self):
        return self.data


class Cable:
    def __init__(self):
        self.left = None
        self.right = None

        color = colorsys.hsv_to_rgb(randint(0, 100) / 100, 0.8, 0.9)

        self.color = [255 * channel for channel in color]

    def opposite(self, start: Device):
        return self.left if self.left != start else self.right


spriteIndex = [Speaker, Splitter, Adder, Oscillator, Attack, Decay, Sample, Amp,
               Beatbox, Sequencer, Pitch]

