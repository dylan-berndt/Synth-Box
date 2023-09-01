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
import pyaudio
from sound import *

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
        if not hasattr(self, "offset"):
            self.offset = Vector2(0, 0)

        Object.all_objects.append(self)


class Device(Object):
    def __init__(self, inputs, outputs, size=None, offset=None):
        self.inputs = []
        self.outputs = []
        self.size = size if size is not None else Vector2(1.6, 2)
        self.offset = offset if offset is not None else Vector2(0, 0)

        self.total_inputs = inputs
        self.total_outputs = outputs

        if not hasattr(self, "ui"):
            self.ui = []
        self.switch = None

        self.sprite = Sprite(sprite_paths[spriteIndex.index(type(self))])

        super().__init__()

    @staticmethod
    def connect(first, second):
        if len(first.outputs) < first.total_outputs:
            if len(second.inputs) < second.total_inputs:
                first.outputs.append(second)
                second.inputs.append(first)
        Cable(first, second, len(first.outputs), len(second.inputs))

    def process(self):
        return self.inputs[0].process()


class Speaker(Device):
    def __init__(self, position):
        self.position = position
        self.switch = True
        audio = pyaudio.PyAudio()
        self.stream = audio.open(format=pyaudio.paFloat32, channels=1, rate=sample_rate, output=True)

        self.ui = [Button("Play Once", self.play_once)]

        super().__init__(1, 0)

    def play_once(self):
        play_once(self.stream, self.process().astype(np.float32).tobytes())

    def play_repeat(self):
        pass


class Splitter(Device):
    def __init__(self, position):
        self.position = position

        super().__init__(1, 2, Vector2(1.6, 1.125), Vector2(0, 0.625 - 3/16))


class Adder(Device):
    def __init__(self, position):
        self.position = position

        super().__init__(2, 1, Vector2(1.6, 1.125), Vector2(0, 0.625 - 3/16))

    def process(self):
        if len(self.inputs) < 2:
            return self.inputs[0].process()
        else:
            return (self.inputs[0].process() + self.inputs[1].process()) * 0.5


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

        super().__init__(1, 1, Vector2(1.6, 0.75), Vector2(0, 0.625))

    def process(self):
        data = self.inputs[0].process()
        s = 2 ** (self.ui[0].value / 12)
        return librosa.effects.pitch_shift(data, sr=sample_rate, n_steps=s)


class Attack(Device):
    def __init__(self, position):
        self.position = position
        super().__init__(1, 1, Vector2(1.6, 0.75), Vector2(0, 0.625))

        self.ui = [NumberEdit("Attack", 0.1)]

    def process(self):
        data = self.inputs[0].process()
        space = np.ones(len(data) - int(sample_rate * self.ui[0].value))
        attack = np.linspace(0, 1, int(sample_rate * self.ui[0].value))
        return np.append(attack, space) * data


class Decay(Device):
    def __init__(self, position):
        self.position = position
        super().__init__(1, 1, Vector2(1.6, 0.75), Vector2(0, 0.625))

        self.ui = [NumberEdit("Decay", 0.3)]

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

        super().__init__(1, 1, Vector2(1.6, 1.3125), Vector2(0, 0.34375))

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
        super().__init__(0, 2)

        self.position = position
        self.ui = [NumberEdit("Frequency", 440)]

        self.switch = True

    def process(self):
        samples = np.linspace(0, 1, sample_rate)
        signal = np.sin(2 * np.pi * self.ui[0].value * samples)
        return signal


class Sample(Device):
    def __init__(self, position):
        self.path = ""
        self.data = []
        self.get_data()

        super().__init__(0, 1)

        self.position = position
        self.ui = [Button("Select...", self.get_data)]

        self.switch = True

    def process(self):
        return self.data

    def get_data(self):
        dialog = tkinter.Tk()
        dialog.withdraw()
        self.path = file.askopenfilename(title="Open Sample", filetypes=[("Audio Files", ".wav .ogg .mp3")])

        if not self.path:
            del self
            return

        self.data, data_rate = sf.read(self.path)

        if len(self.data.shape) > 1:
            self.data = np.mean(self.data, axis=1)

        if data_rate != sample_rate:
            target = sample_rate / data_rate
            length = int(len(self.data) * target)
            resample = np.interp(np.linspace(0, len(self.data), length, endpoint=False),
                                 np.arange(len(self.data)), self.data)
            self.data = resample


class Cable:
    all_cables = []

    def __init__(self, left, right, lp, rp):
        self.midpoint = None
        self.right_point = None
        self.left_point = None
        self.left = left
        self.right = right

        self.lp = lp
        self.rp = rp

        color = colorsys.hsv_to_rgb(randint(0, 100) / 100, 0.8, 0.8)

        self.color = [255 * channel for channel in color]

        self.time = 0
        self.find_points()

        Cable.all_cables.append(self)

    def find_points(self):
        self.left_point = Vector2(self.left.position.x + 7 / 16, self.left.position.y + 9 / 16)
        self.right_point = Vector2(self.right.position.x - 7 / 16, self.right.position.y + 9 / 16)
        self.left_point -= Vector2(0, (self.lp - 1) * 6 / 16)
        self.right_point -= Vector2(0, (self.rp - 1) * 6 / 16)
        self.midpoint = (self.left_point + self.right_point) / 2

    def x_pos(self):
        return 0.4 / math.sqrt(self.time) * math.sin(self.time)

    def y_pos(self):
        return -1 * math.cos(self.time * math.pi / 0.4) if self.time < 0.4 else 1

    def update(self, delta):
        self.time += delta
        shift = Vector2(self.x_pos(), self.y_pos())
        self.find_points()
        self.midpoint += shift

    @staticmethod
    def remove(left, right):
        for cable in Cable.all_cables:
            if cable.left == left and cable.right == right:
                left.outputs.remove(right)
                right.inputs.remove(left)
                Cable.all_cables.remove(cable)
                del cable


spriteIndex = [Speaker, Splitter, Adder, Oscillator, Attack, Decay, Sample, Amp,
               Beatbox, Sequencer, Pitch]

