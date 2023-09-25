import scipy.signal

from base import *

process_lag_flag = 0
process_flag = threading.Event()
generator_flag = threading.Event()
current_time = 0

stream = sd.OutputStream(sample_rate, channels=1)
stream.start()


def generate_thread():
    global current_time
    global process_lag_flag

    while not generator_flag.is_set():
        before_process = time_package.time()
        for device in Device.all_objects:
            if type(device) not in [Sine, Square, Triangle, Microphone, Sample, Drumkit]:
                continue
            device.push(current_time)
        total_process = time_package.time() - before_process
        forfeit = (process_time - total_process) - 0.01
        if forfeit > 0:
            time_package.sleep(forfeit)
        elif forfeit < -0.1:
            process_lag_flag = 1
        current_time += buffer_size


def process_thread():
    generator_thread = threading.Thread(target=generate_thread, args=())
    generator_thread.setDaemon(True)
    generator_thread.start()

    while not process_flag.is_set():
        time_package.sleep(0.01)
        for speaker in Device.all_objects:
            if type(speaker) != Speaker:
                continue
            if not speaker.queue:
                continue
            if not speaker.switch:
                speaker.queue.pop(0)
                speaker.timestamp.pop(0)
                continue
            if stream.active:
                stream.write(speaker.queue.pop(0) * speaker.ui[0].value)

    generator_flag.set()
    process_flag.clear()

    generator_thread.join()
    generator_flag.clear()
    return current_time


def reset_process():
    process_flag.set()
    if hasattr(Object, "process"):
        Object.process.join()


def set_process():
    process_flag.clear()
    Object.process = threading.Thread(target=process_thread, args=())
    Object.process.setDaemon(True)
    Object.process.start()


def update_process():
    reset_process()
    set_process()


sequence_edit = None
beatbox_edit = None


def set_sequence_edit(device):
    global sequence_edit
    sequence_edit = device


def set_beatbox_edit(device):
    global beatbox_edit
    beatbox_edit = device


def enter_menu(ui, title):
    reset_process()
    v = full_screen_ui(ui, title)
    set_process()
    return v


sprite = None


class Device(Object):
    def __init__(self, inputs, outputs, size=None, offset=None):
        global sprite

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

        self.sprite = sprite(sprite_paths[spriteIndex.index(type(self))])

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
        for i in device.inputs:
            Cable.remove(i, device)
        for output in device.outputs:
            Cable.remove(device, output)
        Object.all_objects.remove(device)
        device.sprite.remove()
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
        self.queue = []
        self.ui = [NumberEdit("Volume", 1)]

        super().__init__(1, 0)

    def _push(self, time):
        for i in self.inputs:
            data = i.output_data
            x = np.max(np.abs(data))
            if x > 1:
                data = data / x
            self.queue.append(data.astype(np.float32))


class Microphone(Device):
    def __init__(self, position):
        self.position = position
        super().__init__(0, 1)
        self.device_name = ""
        self.find_device()
        self.stream = sd.InputStream(sample_rate, dtype="float32", device=self.device_name,
                                     channels=1, blocksize=buffer_size, callback=self.callback)
        self.stream.start()
        self.flag = False
        self.switch = True

    def find_device(self):
        devices = {}
        for d in sounddevice.query_devices():
            if d['max_input_channels'] >= 1 and d['default_samplerate'] == sample_rate:
                devices[d['name']] = d['index']
        window = tk.Tk()
        window.withdraw()
        ui = [[Button(name, return_screen_ui, devices[name]) for name in devices]]
        self.device_name = enter_menu(ui, "Select Input Device")

    def callback(self, indata, frames, timet, status):
        self.output_data = indata[:, 0]
        self.flag = True

    def push(self, time):
        if self.switch and not self.flag:
            while not self.flag:
                time_package.sleep(0.01)
            self.flag = False
            for output in self.outputs:
                output.push(time)


class Recorder(Device):
    def __init__(self, position):
        self.position = position
        super().__init__(1, 0)
        self.ui = [Button("Save", self.save)]
        self.recorded = {}
        self.switch = False

    def save(self):
        reset_process()

        data = np.zeros(0)
        for key in self.recorded:
            data = np.concatenate((data, self.recorded[key]))

        ui = [[AudioEdit(data)]]
        d = enter_menu(ui, "Select Export Section")
        if d is None:
            return
        data = data[int(d.left):int(d.right)]

        dialog = tk.Tk()
        dialog.withdraw()
        path = file.asksaveasfilename(title="Save Sound", filetypes=[("Audio Files", ".wav .ogg .mp3")])

        if path == "":
            return

        sf.write(path, data, samplerate=sample_rate)

        set_process()

    def push(self, time):
        if not self.switch:
            self.recorded = {}
        else:
            for i in self.inputs:
                self.recorded[time] = i.output_data


class Bus(Device):
    def __init__(self, position):
        self.position = position
        super().__init__(4, 4)

    def push(self, time):
        flag_push(self, time)

    def _push(self, time):
        data = np.zeros(buffer_size)
        for i in self.inputs:
            data += i.output_data / len(self.inputs)
        x = np.max(np.abs(data))
        if x > 1:
            data = data / x
        return data


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

        self.ui = [NumberEdit("Semitones", 4)]

        super().__init__(1, 1, Vector2(1.6, 0.75), Vector2(0, 0.625))

    def _push(self, time):
        data = np.zeros(buffer_size)
        s = self.ui[0].value
        for i in self.inputs:
            data = pitch_shift(i.output_data, s)
        return data


class Echo(Device):
    def __init__(self, position):
        self.position = position
        super().__init__(1, 1, Vector2(1.6, 0.75), Vector2(0, 0.625))
        self.previous_data = np.zeros(buffer_size)
        self.ui = [NumberEdit("Echoes", 4), NumberEdit("Decay", 0.6),
                   NumberEdit("Depth", 0.2), NumberEdit("Strength", 0.4)]
        self.c = 0

    def _push(self, time):
        data = np.zeros([])
        if time - self.c >= buffer_size * 2:
            self.previous_data = np.zeros(buffer_size)
            self.c = time
        for i in self.inputs:
            data = i.output_data
            self.previous_data = np.concatenate((self.previous_data, data))
            echo_play = np.zeros(buffer_size)
            for echo in range(int(self.ui[0].value)):
                start = len(self.previous_data) - ((echo + 1) * int(sample_rate * self.ui[2].value)) - buffer_size
                end = start + buffer_size
                start = max(0, start)
                end = max(0, end)
                echo_data = self.previous_data[start:end] * (self.ui[1].value ** (echo + 1))
                echo_play[:end-start] += echo_data
            data = (1 - self.ui[3].value) * data + self.ui[3].value * echo_play
            self.c = time + buffer_size
        return data


class Tremolo(Device):
    def __init__(self, position):
        self.position = position
        super().__init__(1, 1, Vector2(1.6, 0.75), Vector2(0, 0.625))
        self.ui = [NumberEdit("Rate", 4), NumberEdit("Strength", 0.2)]

    def _push(self, time):
        data = np.zeros(buffer_size)
        mod = np.linspace(time / sample_rate, (time + buffer_size) / sample_rate, buffer_size)
        mod = np.sin(mod * 2 * math.pi * self.ui[0].value)
        for i in self.inputs:
            data = (mod * i.output_data * self.ui[1].value) + (i.output_data * (1 - self.ui[1].value))
        return data


class Chorus(Device):
    def __init__(self, position):
        self.position = position
        super().__init__(1, 1, Vector2(1.6, 0.75), Vector2(0, 0.625))
        self.ui = [NumberEdit("Voices", 2), NumberEdit("Depth", 0.2),
                   NumberEdit("Semitones", 0.2), NumberEdit("Strength", 0.4)]
        self.previous_data = np.zeros(buffer_size)
        self.c = 0

    def _push(self, time):
        data = np.zeros([])
        if time - self.c >= buffer_size * 2:
            self.previous_data = np.zeros(buffer_size)
            self.c = time
        for i in self.inputs:
            data = i.output_data
            self.previous_data = np.concatenate((self.previous_data, data))

            voices, depth, semitones, strength = [u.value for u in self.ui]
            voices = int(voices)
            depth = int(depth * sample_rate)
            semitones = 2 ** (semitones / 12)

            chorus = np.zeros(buffer_size)
            for v in range(voices):
                direction = (v % 2 == 0) * 2 - 1
                start = len(self.previous_data) - ((v + 1) * depth) - buffer_size
                end = start + buffer_size
                start = max(0, start)
                end = max(0, end)
                sample = self.previous_data[start:end]

                voice = pitch_shift(sample, direction * semitones * ((v // 2) + 1))

                chorus[:end - start] += voice / voices

            data = (1 - strength) * data + strength * chorus
            self.c = time + buffer_size
        return data


class Fuzz(Device):
    def __init__(self, position):
        self.position = position
        super().__init__(1, 1, Vector2(1.6, 0.75), Vector2(0, 0.625))
        self.ui = [NumberEdit("Smooth", 0.5), NumberEdit("Strength", 0.1)]

    def _push(self, time):
        data = np.zeros(buffer_size)
        for i in self.inputs:
            smooth, strength = [u.value for u in self.ui]
            d = i.output_data
            fuzz = np.random.normal(0, 1, buffer_size)
            smoothed = scipy.signal.savgol_filter(fuzz, 21, 3)
            data = (1 - strength) * d + strength * ((1 - smooth) * fuzz + smooth * smoothed)
        return data


class Overdrive(Device):
    def __init__(self, position):
        self.position = position
        super().__init__(1, 1, Vector2(1.6, 0.75), Vector2(0, 0.625))
        self.ui = [NumberEdit("Strength", 1)]

    def _push(self, time):
        data = np.zeros(buffer_size)
        for i in self.inputs:
            strength = min(1, max(0, self.ui[0].value))
            d = np.clip(i.output_data, -0.01, 0.01) * 100
            data = (1 - strength) * i.output_data + strength * d
        return data


class Bitcrusher(Device):
    def __init__(self, position):
        self.position = position
        super().__init__(1, 1, Vector2(1.6, 0.75), Vector2(0, 0.625))
        self.ui = [NumberEdit("Bits", 8)]

    def _push(self, time):
        data = np.zeros(buffer_size)
        for i in self.inputs:
            depth = 1 / (2 ** (int(self.ui[0].value) - 1))
            d = i.output_data
            x = np.max(np.abs(d))
            if x > 1:
                d = d / x
            data = np.round(d / depth) * depth
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
            sequence_index = (np.arange(0, length) / beat_length).astype(int)
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
        self.signal = np.zeros(buffer_size)
        check_io(self)

    def push(self, time):
        flag_push(self, time)

    def _push(self, time):
        self.signal = np.zeros(buffer_size)
        if len(self.inputs) <= 1:
            return np.zeros(buffer_size)

        self.signal = self.inputs[1].output_data
        filter_high = self.signal < 0
        filter_low = 1 - filter_high
        i1 = self.inputs[0].output_data * filter_high
        if len(self.inputs) == 2:
            return i1

        i2 = self.inputs[2].output_data * filter_low
        if len(self.inputs) == 3:
            return i1 + i2


class Beatbox(Device):
    def __init__(self, position):
        self.position = position
        super().__init__(4, 1, Vector2(3.2, 2))

        self.ui = [NumberEdit("Attack", 0.1), NumberEdit("Decay", 0.2),
                   NumberEdit("Sustain", 0.2), NumberEdit("Release", 0.2),
                   NumberEdit("BPM", 120), Button("Edit...", set_beatbox_edit, self)]
        self.prev_bpm = 120
        self.length = 4

        check_io(self)

        self.switch = True

    @property
    def length(self):
        return self._length

    @length.setter
    def length(self, t):
        bpm = max(2, self.ui[4].value)
        self.note_duration = int(sample_rate * (60 / bpm))
        self.total_notes = t
        self.note_time = self.total_notes * self.note_duration
        self.masks = [np.array([0 for i in range(self.note_time)], dtype=float) for j in range(4)]
        self.envelope = np.array([1 for i in range(self.note_duration)])
        self.gen_envelope()
        if getattr(self, "_length", None) != t:
            self.notation = [[0 for i in range(t)] for j in range(4)]
        self.notation_update()
        self._length = t

    def notation_update(self):
        for y in range(len(self.notation)):
            for x in range(len(self.notation[0])):
                if self.notation[y][x] != 0:
                    self.add_note(x, y, override=True)

    def gen_envelope(self):
        attack, decay, sustain, release = [self.ui[i].value for i in range(4)]
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

    def add_note(self, x, y, override=False):
        if self.notation[y][x] and not override:
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
        self.masks[y] = np.clip(self.masks[y], 0, 1)

    def remove_note(self, x, y, override=False):
        if not self.notation[y][x] and not override:
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
        self.masks[y] = np.clip(self.masks[y], 0, 1)

    def push(self, time):
        if not self.switch:
            self.output_data = np.zeros(buffer_size)
            return
        if self.prev_bpm != self.ui[4].value:
            self.length = self._length
            self.prev_bpm = self.ui[4].value

        flag_push(self, time)

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
            data += d / len(self.inputs)
            j += 1
        return data


class Drumkit(Device):
    def __init__(self, position):
        self.position = position
        super().__init__(0, 1, Vector2(3.2, 2))
        self.ui = [NumberEdit("BPM", 120), Button("Edit...", set_beatbox_edit, self)]
        self.prev_bpm = 120
        self.switch = True

        self.length = 4

        # Hi-hat, Kick, Percussion, Snare
        paths = os.listdir("Resources/Drums")
        samples = [sf.read(os.path.join("Resources/Drums", paths[i]))[0] for i in range(4)]
        self.samples = [sample[:, 0] for sample in samples]

    @property
    def length(self):
        return self._length

    @length.setter
    def length(self, value):
        bpm = max(2, self.ui[0].value)
        self.note_duration = int(sample_rate * (60 / bpm))
        self.total_notes = value
        self.note_time = self.total_notes * self.note_duration
        self.data = np.zeros(self.note_time)
        if getattr(self, "_length", None) != value:
            self.notation = [[0 for i in range(value)] for j in range(4)]
        self.notation_update()
        self._length = value

    def notation_update(self):
        for y in range(len(self.notation)):
            for x in range(len(self.notation[0])):
                if self.notation[y][x] != 0:
                    self.add_note(x, y, force=True)

    def paste(self, left, right, sample):
        if right < left:
            self.data[left:] += sample[right:]
            self.data[:right] += sample[:right]
        else:
            self.data[left:right] += sample

    def add_note(self, x, y, force=False):
        if self.notation[y][x] and not force:
            return
        sample = self.samples[y]
        self.notation[y][x] = 1
        left, right = (x * self.note_duration) % self.note_time, \
                      (x * self.note_duration + len(sample)) % self.note_time
        self.paste(left, right, sample)

    def remove_note(self, x, y, force=False):
        if not self.notation[y][x] and not force:
            return
        sample = self.samples[y]
        self.notation[y][x] = 0
        left, right = (x * self.note_duration) % self.note_time, \
                      (x * self.note_duration + len(sample)) % self.note_time
        self.paste(left, right, -sample)

    def push(self, time):
        if self.prev_bpm != self.ui[0].value:
            self.length = self._length
            self.prev_bpm = self.ui[0].value

        data = np.zeros(buffer_size) if not self.switch else self._push(time)
        self.output_data = data

        for output in self.outputs:
            output.push(time)

    def _push(self, time):
        left, right = time % self.note_time, (time + buffer_size) % self.note_time
        if right < left:
            l, r = self.data[left:], self.data[:right]
            return np.concatenate((l, r))
        else:
            return self.data[left:right]


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

        self.ui = [Button("Edit...", self.edit), Button("Select...", self.get_data)]
        self.get_data(path)

        self.left, self.right = 0, len(self.data)

        super().__init__(0, 1, Vector2(1.6, 25/16), Vector2(0, 3.5/16))

        self.position = position

        self.switch = True

    def _push(self, time):
        if len(self.data) < 1:
            Device.remove(self)
            return np.zeros(buffer_size)
        loop = self.data[self.left:self.right]
        data = np.take(loop, range(time, time + buffer_size), mode="wrap")
        return data

    def edit(self):
        ui = [[AudioEdit(self.data)]]
        d = enter_menu(ui, "Select Sample Range")
        if d is not None:
            self.left, self.right = int(d.left), int(d.right)

    def get_data(self, path=""):
        reset_process()
        if path == "":
            dialog = tk.Tk()
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

        self.ui[0].value = format(len(self.data) / sample_rate, ".2f")

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
        lp, rp = 0, 0
        for cable in Cable.all_cables:
            if cable.left == left and cable.right == right:
                left.outputs.remove(right)
                right.inputs.remove(left)
                Cable.all_cables.remove(cable)
                lp, rp = cable.lp, cable.rp
                del cable
        r = [cable for cable in Cable.all_cables if cable.right == right and cable.rp > rp]
        l = [cable for cable in Cable.all_cables if cable.left == left and cable.lp > lp]
        for cable in r:
            cable.rp -= 1
        for cable in l:
            cable.lp -= 1


spriteIndex = [Speaker, None, None, Sine, None, Echo, Sample, Amp,
               Beatbox, Sequencer, Pitch, Tremolo, None, Microphone, Recorder, Bus,
               Square, Triangle, Alternator, Drumkit, Chorus, Fuzz, Overdrive, None,
               Bitcrusher]
