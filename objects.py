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

buffer_size = 4096
process_flag = threading.Event()
generator_flag = threading.Event()
current_time = 0

sprite_paths = os.listdir("Resources/Devices/")
sprite_paths = [os.path.join("Resources/Devices/", path) for path in sprite_paths]

sequence_edit = None
beatbox_edit = None


def set_sequence_edit(device):
    global sequence_edit
    sequence_edit = device


def set_beatbox_edit(device):
    global beatbox_edit
    beatbox_edit = device


def generate_thread(generators):
    global current_time
    while not generator_flag.is_set():
        print("", end="\r")
        for gen in generators:
            gen.push(current_time)
        current_time += buffer_size


def process_thread(devices):
    generators = []
    speakers = []

    for device in devices:
        if hasattr(device, "displace"):
            device.displace = 0
        if type(device) in [Oscillator, Sample]:
            generators.append(device)
        elif type(device) == Speaker:
            speakers.append(device)

    for speaker in speakers:
        speaker.queue = []

    generator_thread = threading.Thread(target=generate_thread, args=(generators,))
    generator_thread.setDaemon(True)
    generator_thread.start()

    while not process_flag.is_set() and devices:
        print("", end="\r")
        for speaker in speakers:
            if not speaker.queue or speaker.switch is False:
                continue
            data = np.clip(speaker.queue.pop(0), -1, 1)
            speaker.stream.write(data.astype(np.float32).tobytes())

    generator_flag.set()
    process_flag.clear()

    generator_thread.join()
    generator_flag.clear()
    return current_time


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

        update_process()


def reset_process():
    process_flag.set()
    if hasattr(Object, "process"):
        Object.process.join()


def set_process():
    process_flag.clear()
    Object.process = threading.Thread(target=process_thread, args=(Object.all_objects,))
    Object.process.setDaemon(True)
    Object.process.start()


def update_process():
    reset_process()
    set_process()


class Device(Object):
    def __init__(self, inputs, outputs, size=None, offset=None):
        self.inputs = []
        self.outputs = []
        self.size = size if size is not None else Vector2(1.6, 2)
        self.offset = offset if offset is not None else Vector2(0, 0)

        self.output_data = []

        self.total_inputs = inputs
        self.total_outputs = outputs

        if not hasattr(self, "ui"):
            self.ui = []
        if not hasattr(self, "data"):
            self.data = []
        if not hasattr(self, "_switch"):
            self._switch = None

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
        if len(self.inputs) < 1 and self.total_inputs > 0:
            self.data = 0
            return self.data
        if self.switch or self.switch is None:
            self.data = self._process()
            return self.data
        return 0

    def _process(self):
        print(type(self), "needs a _process")
        return 0

    def push(self, time):
        if self.switch is None or self.switch:
            self.output_data = self._push(time)
        else:
            self.output_data = np.zeros(buffer_size)
        for output in self.outputs:
            output.push(time)

    def _push(self, time):
        print(type(self), "needs a _push")
        return np.zeros(buffer_size)

    @property
    def switch(self):
        return self._switch

    @switch.setter
    def switch(self, switch):
        self._switch = switch

    @staticmethod
    def remove(device):
        Object.all_objects.remove(device)
        Sprite.all_sprites.remove(device.sprite)
        for i in device.inputs:
            Cable.remove(i, device)
        for output in device.outputs:
            Cable.remove(device, output)
        del device


class Speaker(Device):
    def __init__(self, position):
        self.position = position
        self.switch = True
        audio = pyaudio.PyAudio()
        self.stream = audio.open(format=pyaudio.paFloat32, channels=1, rate=sample_rate, output=True)
        self.queue = []

        super().__init__(1, 0)

    def _process(self):
        return self.inputs[0].process()

    def _push(self, time):
        for i in self.inputs:
            self.queue.append(i.output_data)


class Splitter(Device):
    def __init__(self, position):
        self.position = position

        super().__init__(1, 2, Vector2(1.6, 1.125), Vector2(0, 0.625 - 3 / 16))

    def _process(self):
        return self.inputs[0].process()

    def _push(self, time):
        data = np.zeros(buffer_size)
        for i in self.inputs:
            data = i.output_data
        return data


class Mixer(Device):
    def __init__(self, position):
        self.position = position
        self.flag = 0

        super().__init__(2, 1, Vector2(1.6, 1.125), Vector2(0, 0.625 - 3 / 16))

    def _process(self):
        if len(self.inputs) < 2:
            return self.inputs[0].process()
        else:
            left, right = self.inputs[0].process(), self.inputs[1].process()
            smaller, larger = (left, right) if min(len(left), len(right)) == len(left) else (right, left)
            diff = abs(len(left) - len(right))
            smaller = np.append(smaller, np.zeros(diff))
            return (smaller + larger) * 0.5

    def push(self, time):
        self.output_data = self._push(time)
        if len(self.inputs) <= self.flag:
            self.flag = 0
            for output in self.outputs:
                output.push(time)
        self.flag += 1

    def _push(self, time):
        m = 0
        data = np.zeros(buffer_size)
        for i in self.inputs:
            m += 1
            data += i.output_data
        return data / m


class Amp(Device):
    def __init__(self, position):
        self.position = position

        self.ui = [NumberEdit("Amplitude", 1)]

        super().__init__(1, 1)

    def _process(self):
        return self.ui[0].value * self.inputs[0].process()

    def _push(self, time):
        data = np.zeros(buffer_size)
        for i in self.inputs:
            data = i.output_data
        return data * self.ui[0].value


class Pitch(Device):
    def __init__(self, position):
        self.position = position

        self.ui = [NumberEdit("Semitones", 12)]

        super().__init__(1, 1, Vector2(1.6, 0.75), Vector2(0, 0.625))

    def _process(self):
        data = self.inputs[0].process()
        s = 2 ** (self.ui[0].value / 12)
        return librosa.effects.pitch_shift(data, sr=sample_rate, n_steps=s)


class Attack(Device):
    def __init__(self, position):
        self.position = position
        super().__init__(1, 1, Vector2(1.6, 0.75), Vector2(0, 0.625))
        self.displace = 0

        self.ui = [NumberEdit("Attack", 0.1)]

    def _process(self):
        data = self.inputs[0].process()
        space = np.ones(len(data) - int(sample_rate * self.ui[0].value))
        attack = np.linspace(0, 1, int(sample_rate * self.ui[0].value))
        return np.append(attack, space) * data

    def _push(self, time):
        data = np.zeros(buffer_size)
        for i in self.inputs:
            t = time - self.displace
            attack = np.linspace(t / sample_rate, (t + buffer_size) / sample_rate, buffer_size)
            attack = np.clip(attack, 0, 1)
            data = i.output_data * attack
        if np.all(data == np.zeros(buffer_size)):
            self.displace = time + buffer_size
        return data


class Decay(Device):
    def __init__(self, position):
        self.position = position
        super().__init__(1, 1, Vector2(1.6, 0.75), Vector2(0, 0.625))
        self.displace = 0

        self.ui = [NumberEdit("Decay", 0.3)]

    def _process(self):
        data = self.inputs[0].process()
        samples = np.linspace(0, 1, len(data))
        decay = np.exp(-samples / self.ui[0].value)
        return decay * data

    def _push(self, time):
        data = np.zeros(buffer_size)
        for i in self.inputs:
            t = time - self.displace
            samples = np.linspace(t / sample_rate, (t + buffer_size) / sample_rate, buffer_size)
            decay = np.exp(-samples / self.ui[0].value)
            data = i.output_data * decay
        if np.all(data == np.zeros(buffer_size)):
            self.displace = time + buffer_size
        return data


class Sustain(Device):
    def __init__(self, position):
        self.position = position
        self.ui = [NumberEdit("Sustain", 0.2)]
        super().__init__(1, 1, Vector2(1.6, 0.75), Vector2(0, 0.625))

    def _push(self, time):
        data = np.zeros(buffer_size)
        for i in self.inputs:
            data = i.output_data
        return data


class Release(Device):
    def __init__(self, position):
        self.position = position
        self.ui = [NumberEdit("Release", 0.2)]
        super().__init__(1, 1, Vector2(1.6, 0.75), Vector2(0, 0.625))

    def _push(self, time):
        data = np.zeros(buffer_size)
        for i in self.inputs:
            data = i.output_data
        return data


class Tremolo(Device):
    def __init__(self, position):
        self.position = position
        super().__init__(1, 1, Vector2(1.6, 0.75), Vector2(0, 0.625))
        self.ui = [NumberEdit("Rate", 4), NumberEdit("Depth", 0.2)]

    def _process(self):
        data = self.inputs[0].process()
        ratio = len(data) / sample_rate
        mod = np.linspace(0, ratio, len(data))
        mod = np.sin(mod * 2 * math.pi * self.ui[0].value)
        tremolo = data * self.ui[1].value * mod
        return tremolo

    def _push(self, time):
        data = np.zeros(buffer_size)
        mod = np.linspace(time / sample_rate, (time + buffer_size) / sample_rate, buffer_size)
        mod = np.sin(mod * 2 * math.pi * self.ui[0].value)
        for i in self.inputs:
            data = mod * i.output_data * self.ui[1].value
        return data


class Vibrato(Device):
    def __init__(self, position):
        self.position = position
        super().__init__(1, 1, Vector2(1.6, 0.75), Vector2(0.0625))
        self.ui = [NumberEdit("Rate", 4), NumberEdit("Depth", 0.2)]

    def _process(self):
        data = self.inputs[0].process()
        ratio = len(data) / sample_rate
        mod = np.linspace(0, ratio, len(data))
        mod = np.sin(mod * 2 * math.pi * self.ui[0].value)
        stretch = mod * self.ui[1].value
        vibrato = np.interp(np.arange(len(data)) * stretch, np.arange(len(data)), data)
        return vibrato


class Sequencer(Device):
    def __init__(self, position):
        self.position = position
        self.sequence = [1, 0, 1, 0, 1, 1, 0, 0]

        self.switch = True

        self.ui = [NumberEdit("BPM", 120), Button("Edit...", set_sequence_edit, self)]

        super().__init__(1, 1, Vector2(1.6, 1.3125), Vector2(0, 0.34375))

    def _process(self):
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

    def _push(self, time):
        data = np.zeros(buffer_size)
        for i in self.inputs:
            if self.ui[0].value == 0:
                continue
            beat_length = int(sample_rate * 60 / self.ui[0].value)
            length = len(self.sequence) * beat_length
            sequence_index = (np.arange(0, length) / beat_length).astype(np.int)
            left, right = time % length, (time + buffer_size) % length
            if left < right:
                buffer_sequence = sequence_index[left:right]
            else:
                buffer_sequence = np.concatenate((sequence_index[left:length], sequence_index[0:right]))
            buffer_mult = np.array(self.sequence)[buffer_sequence]
            data = i.output_data * buffer_mult
        return data


class Beatbox(Device):
    def __init__(self, position):
        self.position = position
        super().__init__(4, 1)

        self.ui = [NumberEdit("BPM", 120), Button("Edit...", set_beatbox_edit, self)]

    def _process(self):
        pass


class Oscillator(Device):
    def __init__(self, position):
        super().__init__(0, 2)

        self.position = position
        self.ui = [NumberEdit("Frequency", 440)]

        self.switch = True

    def _process(self):
        samples = np.linspace(0, 1, sample_rate)
        signal = np.sin(2 * np.pi * self.ui[0].value * samples)
        return signal

    def _push(self, time):
        if not self.ui:
            return []
        r1, r2 = time / sample_rate, (time + buffer_size) / sample_rate
        samples = np.linspace(r1, r2, buffer_size)
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

    def _process(self):
        return self.data

    def _push(self, time):
        left, right = time % len(self.data), (time + buffer_size) % len(self.data)
        if left < right:
            return self.data[left:right]
        else:
            return np.concatenate((self.data[left:len(self.data)], self.data[0:right]))

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

        color = colorsys.hsv_to_rgb(randint(0, 100) / 100, 0.8, 0.8 + randint(0, 100) / 500)

        self.color = [255 * channel for channel in color]

        self.time = 0
        self.find_points()

        Cable.all_cables.append(self)
        update_process()

    def find_points(self):
        self.left_point = Vector2(self.left.position.x + 7 / 16, self.left.position.y + 9 / 16)
        self.right_point = Vector2(self.right.position.x - 7 / 16, self.right.position.y + 9 / 16)
        self.left_point -= Vector2(0, (self.lp - 1) * 6 / 16)
        self.right_point -= Vector2(0, (self.rp - 1) * 6 / 16)
        self.midpoint = (self.left_point + self.right_point) / 2

    def x_pos(self):
        return 0.4 / math.sqrt(self.time) * math.sin(self.time)

    def y_pos(self):
        if self.time >= 1.5:
            return 1
        t = self.time / 1.5
        c4 = (2 * math.pi) / 3
        num = math.pow(2, -10 * t) * math.sin((t * 10 - 0.75) * c4) + 1
        return num

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
        update_process()


spriteIndex = [Speaker, Splitter, Mixer, Oscillator, Attack, Decay, Sample, Amp,
               Beatbox, Sequencer, Pitch, Tremolo, Vibrato, Sustain, Release]
