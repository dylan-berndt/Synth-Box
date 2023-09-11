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
import time as time_package
import threading

sample_rate = 44100

buffer_size = 2048
process_flag = threading.Event()
generator_flag = threading.Event()
current_time = 0

process_time = buffer_size / sample_rate

sprite_paths = os.listdir("Resources/Devices/")
sprite_paths = [os.path.join("Resources/Devices/", path) for path in sprite_paths]

sequence_edit = None
beatbox_edit = None

state_flag = False


def set_sequence_edit(device):
    global sequence_edit
    sequence_edit = device


def set_beatbox_edit(device):
    global beatbox_edit
    beatbox_edit = device


def generate_thread(generators):
    global current_time
    while not generator_flag.is_set():
        before_process = time_package.time()
        for gen in generators:
            gen.push(current_time)
        total_process = time_package.time() - before_process
        forfeit = (process_time - total_process) / 2
        # if forfeit > 0:
        #     time_package.sleep(forfeit)
        current_time += buffer_size


def process_thread(devices):
    generators = []
    speakers = []

    for device in devices:
        if hasattr(device, "displace"):
            device.displace = 0
        if type(device) in [Sine, Square, Triangle, Sample, Echo, Reverb]:
            generators.append(device)
        elif type(device) == Speaker:
            speakers.append(device)

    for speaker in speakers:
        speaker.queue = []

    generator_thread = threading.Thread(target=generate_thread, args=(generators,))
    generator_thread.setDaemon(True)
    generator_thread.start()

    while not process_flag.is_set() and devices:
        time_package.sleep(0.01)
        for speaker in speakers:
            if not speaker.queue or speaker.switch is False:
                continue
            data = speaker.queue.pop(0)
            data = np.clip(data, -1, 1)
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

        if not state_flag:
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

        self.output_data = np.zeros(buffer_size)

        self.total_inputs = inputs
        self.total_outputs = outputs

        self.anim_time = 0

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
        device.sprite.remove()
        for i in device.inputs:
            Cable.remove(i, device)
        for output in device.outputs:
            Cable.remove(device, output)
        del device

    @staticmethod
    def clear_all():
        while Object.all_objects:
            device = Object.all_objects[0]
            device.sprite.remove()
            del Object.all_objects[0]
        while Cable.all_cables:
            del Cable.all_cables[0]


class Speaker(Device):
    def __init__(self, position):
        self.position = position
        self.switch = True
        audio = pyaudio.PyAudio()
        self.stream = audio.open(format=pyaudio.paFloat32, channels=1, rate=sample_rate, output=True,
                                 frames_per_buffer=buffer_size)
        self.queue = []

        super().__init__(1, 0)

    def _push(self, time):
        for i in self.inputs:
            self.queue.append(i.output_data)


class Splitter(Device):
    def __init__(self, position):
        self.position = position

        super().__init__(1, 2, Vector2(1.6, 1.125), Vector2(0, 0.625 - 3 / 16))

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
            if i.output_data != []:
                m += 1
                data += i.output_data
        return data / m


class Amp(Device):
    def __init__(self, position):
        self.position = position

        self.ui = [NumberEdit("Amplitude", 1)]

        super().__init__(1, 1)

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

    def _push(self, time):
        data = np.zeros(buffer_size)
        s = 2 ** (self.ui[0].value / 12)
        for i in self.inputs:
            data = librosa.effects.pitch_shift(i.output_data, sr=sample_rate, n_steps=s)
        return data


class Reverb(Device):
    def __init__(self, position):
        self.position = position
        super().__init__(1, 1, Vector2(1.6, 0.75), Vector2(0, 0.625))
        self.previous_data = []
        self.ui = []

    def _push(self, time):
        data = np.zeros(buffer_size)
        for i in self.inputs:
            self.previous_data = np.concatenate((self.previous_data, i.output_data))
            data += i.output_data

        return data


class Echo(Device):
    def __init__(self, position):
        self.position = position
        super().__init__(1, 1, Vector2(1.6, 0.75), Vector2(0, 0.625))
        self.previous_data = np.zeros(buffer_size)
        self.ui = [NumberEdit("Amount", 2), NumberEdit("Decay", 0.8),
                   NumberEdit("Spacing", 0.1), NumberEdit("Strength", 0.2)]
        self.creation_time = current_time
        self.flag = 0

    def push(self, time):
        self.output_data = self._push(time)
        if len(self.inputs) + 1 <= self.flag:
            self.flag = 0
            for output in self.outputs:
                output.push(time)
        self.flag += 1

    def _push(self, time):
        data = np.zeros(buffer_size)
        for i in self.inputs:
            data += i.output_data
        self.previous_data = np.concatenate((self.previous_data, data))
        echo_play = np.zeros(buffer_size)
        for echo in range(int(self.ui[0].value)):
            start = time - ((echo + 1) * int(sample_rate * self.ui[2].value))
            end = start + buffer_size
            start, end = start - self.creation_time, end - self.creation_time
            start = max(0, start)
            end = max(0, end)
            echo_data = self.previous_data[start:end] * (self.ui[1].value ** (echo + 1))
            echo_play[:end-start] += echo_data
        data = (1 - self.ui[3].value) * data + self.ui[3].value * echo_play
        return data


class Tremolo(Device):
    def __init__(self, position):
        self.position = position
        super().__init__(1, 1, Vector2(1.6, 0.75), Vector2(0, 0.625))
        self.ui = [NumberEdit("Rate", 4), NumberEdit("Depth", 0.2)]

    def _push(self, time):
        data = np.zeros(buffer_size)
        mod = np.linspace(time / sample_rate, (time + buffer_size) / sample_rate, buffer_size)
        mod = np.sin(mod * 2 * math.pi * self.ui[0].value)
        for i in self.inputs:
            data = (mod * i.output_data * self.ui[1].value) + (i.output_data * (1 - self.ui[1].value))
        return data


class Vibrato(Device):
    def __init__(self, position):
        self.position = position
        super().__init__(1, 1, Vector2(1.6, 0.75), Vector2(0, 0.625))
        self.ui = [NumberEdit("Rate", 4), NumberEdit("Depth", 0.02)]

    def _push(self, time):
        data = np.zeros(buffer_size)
        for i in self.inputs:
            data = i.output_data
            samples = np.linspace(time / sample_rate, (time + buffer_size) / sample_rate, buffer_size)
            mod = self.ui[1].value * np.sin(2 * np.pi * self.ui[0].value * samples)
            data = np.interp(samples + mod, samples, data)
        return data


class Sequencer(Device):
    def __init__(self, position):
        self.position = position
        self.sequence = [0, 0, 0, 0, 0, 0, 0, 0]

        self.switch = True

        self.ui = [NumberEdit("BPM", 120), Button("Edit...", set_sequence_edit, self)]

        super().__init__(1, 1, Vector2(3.2, 1.3125), Vector2(0, 0.34375))

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


class Alternator(Device):
    def __init__(self, position):
        self.position = position
        super().__init__(3, 1, Vector2(1.6, 1.5), Vector2(0, 0.25))
        self.flag = 0

    def push(self, time):
        self.output_data = self._push(time)
        if len(self.inputs) <= self.flag:
            self.flag = 0
            for output in self.outputs:
                output.push(time)
        self.flag += 1

    def _push(self, time):
        if len(self.inputs) <= 1:
            return np.zeros(buffer_size)
        i1 = self.inputs[0].output_data * (self.inputs[1].output_data < 0)
        if len(self.inputs) == 2:
            return i1
        i2 = self.inputs[2].output_data * (self.inputs[1].output_data >= 0)
        if len(self.inputs) == 3:
            return i1 + i2


class Beatbox(Device):
    def __init__(self, position):
        self.position = position
        super().__init__(4, 1, Vector2(3.2, 2))

        self.envelope_data = [0.1, 0.05, 0, 0.2]
        self.ui = [NumberEdit("BPM", 120), Button("Edit...", set_beatbox_edit, self)]
        self.prev_bpm = 120

        self.flags = [0, 0, 0, 0]
        self.time_signature = 4

        self.switch = True

    @property
    def time_signature(self):
        return self._time_signature

    @time_signature.setter
    def time_signature(self, t):
        bpm = max(0.001, self.ui[0].value)
        self.note_duration = int(sample_rate * (60 / bpm))
        self.total_notes = t * 2
        self.note_time = self.total_notes * self.note_duration
        self.notation = [[0 for i in range(t * 2)] for j in range(4)]
        self.masks = [np.array([0 for i in range(self.note_time)], dtype=np.float) for j in range(4)]
        self.envelope = np.array([1 for i in range(self.note_duration)])
        self._time_signature = t
        self.gen_envelope()

    def gen_envelope(self):
        attack, decay, sustain, release = self.envelope_data
        at, dt, rt = int(attack * sample_rate), int(decay * sample_rate), int(release * sample_rate)
        envelope = np.zeros(max(at + dt + rt, self.note_duration + rt))
        a = np.linspace(0, 1, at)
        envelope[0:at] = a
        d = np.linspace(1, sustain, dt)
        envelope[at:at + dt] = d
        envelope[at + dt:] = sustain
        r = np.linspace(sustain, 0, rt)
        envelope[self.note_duration:self.note_duration + rt] = r
        envelope = envelope[:self.note_duration + rt]
        self.envelope = envelope

    def add_note(self, x, y):
        if self.notation[y][x]:
            return
        self.notation[y][x] = 1
        start = x * self.note_duration
        if start + len(self.envelope) > self.note_time:
            left = self.note_time - start
            extra = len(self.envelope) - left
            self.masks[y][start:] += self.envelope[:left]
            self.masks[y][:extra] += self.envelope[left:]
        else:
            self.masks[y][start:start + len(self.envelope)] += self.envelope

    def remove_note(self, x, y):
        if not self.notation[y][x]:
            return
        self.notation[y][x] = 0
        start = x * self.note_duration
        if start + len(self.envelope) > self.note_time:
            left = self.note_time - start
            extra = len(self.envelope) - left
            self.masks[y][start:] -= self.envelope[:left]
            self.masks[y][:extra] -= self.envelope[left:]
        else:
            self.masks[y][start:start + len(self.envelope)] -= self.envelope

    def push(self, time):
        if not self.switch:
            self.output_data = np.zeros(buffer_size)
            return
        if self.prev_bpm != self.ui[0].value:
            self.time_signature = self._time_signature
            self.prev_bpm = self.ui[0].value

        for f in range(4):
            if self.flags[f] != time:
                self.flags[f] = time
                break
        sync = True
        value = self.flags[0]
        for f in range(4):
            clear = self.flags[f] == value or self.flags[f] == 0
            sync = sync and clear

        if sync:
            self.output_data = self._push(time)
            for output in self.outputs:
                output.push(time)

    def _push(self, time):
        data = np.zeros(buffer_size)
        j = 0
        for i in self.inputs:
            y = 3 - j
            d = i.output_data
            left, right = time % self.note_time, (time + buffer_size) % self.note_time
            if left < right:
                d = d * self.masks[y][left:right]
            else:
                mask = np.concatenate((self.masks[y][left:self.note_time], self.masks[y][0:right]))
                d = d * mask
            data += d
            j += 1
        return data


class Sine(Device):
    def __init__(self, position):
        super().__init__(0, 1)

        self.position = position
        self.ui = [NumberEdit("Frequency", 440)]

        self.switch = True

    def _push(self, time):
        if not self.ui:
            return []
        r1, r2 = time / sample_rate, (time + buffer_size) / sample_rate
        samples = np.linspace(r1, r2, buffer_size)
        signal = np.sin(2 * np.pi * self.ui[0].value * samples)
        return signal


class Square(Device):
    def __init__(self, position):
        super().__init__(0, 1)

        self.position = position
        self.ui = [NumberEdit("Frequency", 440)]

        self.switch = True

    def _push(self, time):
        if not self.ui:
            return []
        r1, r2 = time / sample_rate, (time + buffer_size) / sample_rate
        samples = np.linspace(r1, r2, buffer_size)
        signal = ((self.ui[0].value * samples) % 1 < 0.5) * 2 - 1
        return signal


class Triangle(Device):
    def __init__(self, position):
        super().__init__(0, 1)

        self.position = position
        self.ui = [NumberEdit("Frequency", 440)]

        self.switch = True

    def _push(self, time):
        if not self.ui:
            return []
        r1, r2 = time / sample_rate, (time + buffer_size) / sample_rate
        samples = np.linspace(r1, r2, buffer_size)
        signal = (np.abs(((self.ui[0].value * samples) % 1) - 0.5) * 4) - 1
        return signal


class Sample(Device):
    def __init__(self, position, path=""):
        self.path = path
        self.data = []
        self.get_data(path)

        super().__init__(0, 1, Vector2(1.6, 25/16), Vector2(0, 3.5/16))

        self.position = position
        self.ui = [Button("Select...", self.get_data)]

        self.switch = True

    def _push(self, time):
        if len(self.data) < 1:
            Device.remove(self)
            return np.zeros(buffer_size)
        left, right = time % len(self.data), (time + buffer_size) % len(self.data)
        if left < right:
            return self.data[left:right]
        else:
            return np.concatenate((self.data[left:len(self.data)], self.data[0:right]))

    def get_data(self, path=""):
        reset_process()
        if path == "":
            dialog = tkinter.Tk()
            dialog.withdraw()
            self.path = file.askopenfilename(title="Open Sample", filetypes=[("Audio Files", ".wav .ogg .mp3")])

            if self.path == "":
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

        set_process()


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

        if not state_flag:
            update_process()

    def find_points(self):
        width = self.left.size.x / 1.6, self.right.size.x / 1.6
        self.left_point = Vector2(self.left.position.x + width[0] * 7 / 16, self.left.position.y + 9 / 16)
        self.right_point = Vector2(self.right.position.x - width[1] * 7 / 16, self.right.position.y + 9 / 16)
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


spriteIndex = [Speaker, Splitter, Mixer, Sine, Reverb, Echo, Sample, Amp,
               Beatbox, Sequencer, Pitch, Tremolo, Vibrato, None, None, None,
               Square, Triangle, Alternator]
