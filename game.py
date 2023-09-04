from physics import *
from screen import *
import screen
from objects import *


def save_state():
    dialog = tkinter.Tk()
    dialog.withdraw()
    path = file.asksaveasfilename(title="Save State")


def open_state():
    dialog = tkinter.Tk()
    dialog.withdraw()
    path = file.asksaveasfilename(title="Open Save State", filetypes=[("State File", ".stt")])


def create(item_type):
    item_type(Vector2(0, -6) + screen.camera_position)


generator_list = [Button("Oscillator", create, Oscillator),
                  Button("Sampler", create, Sample)]

effects_list = [Button("Amp", create, Amp),
                Button("Attack", create, Attack),
                Button("Decay", create, Decay),
                Button("Pitch", create, Pitch),
                Button("Tremolo", create, Tremolo),
                Button("Vibrato", create, Vibrato)]

mixer_list = [Button("Sequencer", create, Sequencer),
              Button("Beatbox", create, Beatbox)]

utility_list = [Button("Splitter", create, Splitter),
                Button("Mixer", create, Mixer),
                Button("Speaker", create, Speaker)]


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
