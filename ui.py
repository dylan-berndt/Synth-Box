
import pygame
import sys
import ctypes
import numpy as np

pygame.font.init()
font = pygame.font.Font("Resources/04B03.ttf", 24)

names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
values = [261.63 * ((2 ** (1/12)) ** i) for i in range(len(names))]
notes = dict(zip(names, values))

signal_height = 40

pygame.mixer.init()


def timestamp(num):
    t = num / 44100
    sM, ss = divmod(t, 60)
    ss = int(ss)
    sm = 100 * (t - int(t))
    return "{:02.0f}:{:02.0f}:{:02.0f}".format(sM, ss, sm)


def close():
    pygame.quit()
    sys.exit()


def minimize():
    hwnd = pygame.display.get_wm_info()["window"]
    ctypes.windll.user32.ShowWindow(hwnd, 6)


def set_window_position(x, y):
    hwnd = pygame.display.get_wm_info()["window"]
    ctypes.windll.user32.MoveWindow(hwnd, x, y, 1200, 600, True)


def tab_check(mx, my):
    if my > 48:
        return
    if mx > 1120:
        if mx > 1160:
            close()
        else:
            minimize()


def interpret(data):
    if data == "":
        return 0, ""
    if data == "-":
        return 0, "-"
    if type(data) == str:
        try:
            num = float(data)
            return num, data
        except ValueError:
            if data[0] in names:
                if len(data) > 1 and data[1] == "#":
                    if len(data) > 2 and data[2].isnumeric():
                        num = round(notes[data[0:2]] * (2 ** (int(data[2]) - 4)), 2)
                        return num, str(num)
                    else:
                        return notes[data[0:2]], data
                elif len(data) > 1 and data[1].isnumeric():
                    num = round(notes[data[0]] * (2 ** (int(data[1]) - 4)), 2)
                    return num, str(num)
                else:
                    return notes[data[0]], data
            else:
                return 0, ""
    if type(data) in [int, float]:
        return data, str(data)
    return 0, ""


class ListItem:
    def __init__(self):
        self.text = ""


class Text(ListItem):
    def __init__(self, text):
        super().__init__()
        self.text = text


class Number(ListItem):
    def __init__(self, num):
        super().__init__()
        self.text = str(num)


class List(ListItem):
    def __init__(self, text, items):
        super().__init__()
        self.text = text + ">"
        self.items = items


class Audio(ListItem):
    def __init__(self, audio):
        self.audio = audio
        super().__init__()


class ListElement:
    all_elements = []

    def __init__(self, rows):
        self.height = len(rows)
        self.items = rows
        if not hasattr(self, "value"):
            self.value = 0

        ListElement.all_elements.append(self)


class NumberEdit(ListElement):
    def __init__(self, name, value):
        super().__init__([Text(name), Number(value)])

        self.name = name
        self.value = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, data):
        data = interpret(data)
        self._value = data[0]
        self.items[1].text = data[1]


class Button(ListElement):
    def __init__(self, name, function, args=None):
        self.name = name
        self.function = function
        self.args = args

        super().__init__([Text(name)])


class AudioEdit(ListElement):
    def __init__(self, audio):
        self.signal = None
        self.audio = audio
        self.left = 0
        self.right = len(audio)
        self.gen_signal()
        super().__init__([Audio(audio)])

    def gen_signal(self):
        signal = pygame.Surface((295, signal_height + 1))
        signal.fill((255, 255, 255))
        window_length = int(len(self.audio) / 295)
        maximum = np.max(np.abs(self.audio))
        for i in range(0, len(self.audio), window_length):
            height = np.max(np.abs(self.audio[i:i + window_length])) / maximum
            draw_height = 1 + (2 * (int(height * (signal_height - 2)) // 2))
            pygame.draw.rect(signal, (40, 40, 255),
                             (i // window_length, int((signal_height / 2) - (draw_height // 2)), 1, draw_height))
        self.signal = pygame.transform.scale(signal, (1180, (signal_height + 1) * 4))

    def draw_stats(self, surface, x, y, width):
        surface.blit(self.signal, (x + 10, y + 14))

        start, end = timestamp(self.left), timestamp(self.right)
        length = str(self.right - self.left) + " / 44100 = " + format((self.right - self.left) / 44100, ".3f") + "s"
        stamps = font.render(start, True, (255, 255, 255)), font.render(end, True, (255, 255, 255))
        time = font.render(length, True, (255, 255, 255))
        surface.blit(stamps[0], (x + 10, y + (signal_height * 4) + 28 + 6))
        surface.blit(stamps[1], (x + 130, y + (signal_height * 4) + 28 + 6))
        surface.blit(time, (width - 10 - time.get_width(), y + (signal_height * 4) + 28 + 6))

        sample = pygame.Surface((295, signal_height + 1), pygame.SRCALPHA)
        pygame.draw.rect(sample, (0, 0, 0, 180),
                         (0, 0, int(295 * (self.left / len(self.audio))), signal_height + 1))
        pygame.draw.rect(sample, (0, 0, 0, 180),
                         (int(295 * (self.right / len(self.audio))), 0,
                          int(295 * ((len(self.audio) - self.right) / len(self.audio))) + 1, signal_height + 1))
        pygame.draw.rect(sample, (255, 255, 255),
                         (int(295 * (self.left / len(self.audio))) - 2, 0, 1, signal_height + 1))
        pygame.draw.rect(sample, (255, 255, 255),
                         (int(295 * (self.right / len(self.audio))) + 1, 0, 1, signal_height + 1))

        sample = pygame.transform.scale(sample, (1180, (signal_height + 1) * 4))
        surface.blit(sample, (x + 10, y + 14))


complete = False
value = None


def return_screen_ui(v):
    global value
    global complete

    value = v
    complete = True


def exit_screen_ui():
    global complete

    complete = True


def full_screen_ui(ui, title):
    global complete

    complete = False
    clicking = False

    left = 0
    right = 0
    g = False

    window = pygame.display.get_surface()
    clock = pygame.time.Clock()

    surface = pygame.Surface((300, 138))
    pygame.draw.line(surface, (255, 255, 255), (0, 0), (300, 0))
    surface = pygame.transform.scale(surface, (1200, 552))

    title_draw = font.render(title, True, (255, 255, 255))
    pygame.draw.rect(window, (0, 0, 0), (80, 0, 1020, 48))
    window.blit(title_draw, (88, 14))

    audio = None
    left_edit = True
    for c in ui:
        for r in c:
            if type(r) == AudioEdit:
                audio = r

    if audio is not None:
        ui[0].append(Button("Select", return_screen_ui, audio))

    while not complete:
        surface.fill((0, 0, 0))

        click = False
        mx, my = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    complete = True
                if audio is not None:
                    if event.key == pygame.K_SPACE:
                        data = audio.audio[audio.left:audio.right]
                        data = np.stack((data, data), axis=-1).astype(np.int16)
                        sound = pygame.sndarray.make_sound(data)
                        sound.play()
                    if event.key == pygame.K_LEFT:
                        left = 0.01
                    if event.key == pygame.K_RIGHT:
                        right = 0.01

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT:
                    left = 0
                    g = False
                if event.key == pygame.K_RIGHT:
                    right = 0
                    g = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    tab_check(mx, my)

                    click = True
                    clicking = True

            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    clicking = False

        fps = clock.get_fps()
        if fps != 0:
            delta = 1 / fps
            if left > 0:
                left += delta
                if not g:
                    if left_edit:
                        audio.left = max(0, audio.left - 1)
                    else:
                        audio.right = max(audio.left + 1, audio.right - 1)
                g = True
            if left > 0.4:
                if left_edit:
                    audio.left = max(0, audio.left - 1)
                else:
                    audio.right = max(audio.left + 1, audio.right - 1)
            if right > 0:
                right += delta
                if not g:
                    if left_edit:
                        audio.left = min(audio.right - 1, audio.left + 1)
                    else:
                        audio.right = min(len(audio.audio), audio.right + 1)
                g = True
            if right > 0.4:
                if left_edit:
                    audio.left = min(audio.right - 1, audio.left + 1)
                else:
                    audio.right = min(len(audio.audio), audio.right + 1)

        x, y = 0, 0
        width = 1200 / len(ui)
        for column in ui:
            for row in column:
                height = 48 if type(row) != AudioEdit else signal_height * 4 + 28 + 48

                if type(row) == AudioEdit:
                    row.draw_stats(surface, x, y, width)

                    if clicking:
                        mean = (row.left + row.right) / 2
                        ms = min(len(row.audio), max(0, int(len(row.audio) * (mx - 10) / 1180)))
                        if ms < mean:
                            left_edit = True
                            row.left = ms
                        else:
                            left_edit = False
                            row.right = ms
                else:
                    for item in row.items:
                        if click and type(row) == Button:
                            if x < mx < x + width:
                                if y < my - 48 < y + height:
                                    if row.args is not None:
                                        row.function(row.args)
                                    else:
                                        row.function()
                        render = font.render(item.text, True, (255, 255, 255))
                        surface.blit(render, (x + 16, y + 16))

                y += height
            x += width
            y = 0

        window.blit(surface, (0, 48))

        pygame.display.update()
        clock.tick(120)

    complete = False
    return value

