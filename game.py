from physics import *
from screen import *
import screen
from objects import *
import json
import objects


def save_state():
    reset_process()

    dialog = tkinter.Tk()
    dialog.withdraw()
    path = file.asksaveasfilename(title="Save State", filetypes=[("State File", ".stt")], defaultextension=".stt")
    if path == "":
        return
    save = open(path, "w+")

    for device in Object.all_objects:
        pos = Vector2(round(device.position.x * 100) / 100, round(device.position.y * 100) / 100)
        save.write('{"type": "%s", "position": %s, "values": %s' %
                   (str(type(device).__name__), str(pos),
                    str([ui.value for ui in device.ui])))
        if type(device) == Sample:
            save.write(', "path": "%s"' % device.path)
        if type(device) == Beatbox:
            save.write(', "notation": %s' % device.notation)
            save.write(', "time": %s' % device.time_signature)
        if type(device) == Sequencer:
            save.write(', "sequence": %s' % device.sequence)
        save.write("}\n")

    save.write("\n###\n")

    for cable in Cable.all_cables:
        left, right = Object.all_objects.index(cable.left), Object.all_objects.index(cable.right)
        save.write(str(left) + ", " + str(right) + "\n")

    set_process()


def open_state():
    reset_process()

    dialog = tkinter.Tk()
    dialog.withdraw()
    path = file.askopenfilename(title="Open Save State", filetypes=[("State File", ".stt")])
    if path == "":
        return

    Device.clear_all()

    devices = []

    device_read = True

    objects.state_flag = True

    state = open(path)
    for line in state.readlines():
        if line == "###\n":
            device_read = False
            continue
        if device_read and line[:-1]:
            data = json.loads(line[:-1])
            constructor = globals()[data['type']]
            position = tuple(data['position'])
            position = Vector2(position[0], position[1])
            if data['type'] == "Sample":
                device = constructor(position, path=data['path'])
            else:
                device = constructor(position)
            if data['type'] == "Beatbox":
                device.time_signature = data['time']
                notation = data['notation']
                for y in range(len(notation)):
                    for x in range(len(notation[0])):
                        if notation[y][x]:
                            device.add_note(x, y)
            if data['type'] == "Sequencer":
                device.sequence = data['sequence']
            devices.append(device)

            for u, ui in enumerate(device.ui):
                ui.value = data['values'][u]
        elif line[:-1]:
            interpret = eval(line[:-1])
            left, right = devices[interpret[0]], devices[interpret[1]]
            Device.connect(left, right)

    objects.state_flag = False

    set_process()


def create(item_type):
    item_type(Vector2(0, -6) + screen.camera_position)


generator_list = [Button("Sine", create, Sine),
                  Button("Square", create, Square),
                  Button("Triangle", create, Triangle),
                  Button("Sampler", create, Sample)]

effects_list = [Button("Amp", create, Amp),
                Button("Pitch", create, Pitch),
                Button("Tremolo", create, Tremolo),
                Button("Echo", create, Echo)]

mixer_list = [Button("Alternator", create, Alternator),
              Button("Splitter", create, Splitter),
              Button("Mixer", create, Mixer),
              Button("Beatbox", create, Beatbox),
              Button("Sequencer", create, Sequencer)]

utility_list = [Button("Speaker", create, Speaker)]


def attempt_cable(mp, cabling):
    if cabling is None:
        return
    for device in Object.all_objects:
        if not point_in_object(mp, device):
            continue
        if cabling == device:
            if device.switch is not None:
                device.switch = not device.switch
                update_process()
            return
        if cabling not in device.inputs:
            if not len(cabling.outputs) < cabling.total_outputs:
                return
            if len(device.inputs) < device.total_inputs:
                Device.connect(cabling, device)
        else:
            Cable.remove(cabling, device)


def run_ui(ui, pos, mx, my):
    left_focus = True
    ui_click = False
    typing = None
    if pos.x - 72 < mx < pos.x + 72:
        j = 0
        for e, element in enumerate(ui):
            for i, item in enumerate(element.items):
                if pos.y + (j * 48) < my < pos.y + ((j + 1) * 48):
                    ui_click = True
                    left_focus = False
                    if type(item) == Number:
                        typing = element
                    if type(element) == Button:
                        if element.args is not None:
                            element.function(element.args)
                        else:
                            element.function()
                        update_process()
                j += 1
    return left_focus, ui_click, typing


def check_menu_ui(mx, my, menu_list):
    height = sum(element.height for element in menu_list)
    height *= 48
    pos = Vector2(1200 - 72, 48)

    return run_ui(menu_list, pos, mx, my)


def check_focus_ui(focus, mx, my):
    height = sum(element.height for element in focus.ui)
    height *= 48
    pos = world_to_camera(focus.position + focus.offset * 2)
    pos.y -= focus.sprite.get_height() / 2 + 16 + height

    return run_ui(focus.ui, pos, mx, my)


def beatbox_num(beat, mx, my, add=True):
    if my > 400:
        divisions = len(beat.notation[0]), 4
        size = 1200 / divisions[0], 200 / divisions[1]
        button = int(mx / size[0]), int((my - 400) / size[1])
        if add:
            beat.add_note(button[0], button[1])
        else:
            beat.remove_note(button[0], button[1])


def sequence_num(beat, mx, my, add=True):
    if my > 136 * 4:
        size = 1200 / 8
        button = int(mx / size)
        if add:
            beat.sequence[button] = 1
        else:
            beat.sequence[button] = 0
