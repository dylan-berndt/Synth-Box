import tkinter as tk

import sounddevice

from MathBasic import *
from ui import *
import colorsys
from random import randint
from sound import *
import tkinter.filedialog as file
import soundfile as sf
import os
import sounddevice as sd
import time as time_package
import threading
import scipy.io
import pygame

ppu = 64

sample_rate = 44100

buffer_size = 11025

process_time = buffer_size / sample_rate

sprite_paths = os.listdir("Resources/Devices/")
sprite_paths = [os.path.join("Resources/Devices/", path) for path in sprite_paths]

state_flag = False


def check_io(self):
    if not hasattr(self, "io"):
        self.io = []
    if not hasattr(self, "flags"):
        self.flags = [0 for _ in range(self.total_inputs)]
    if self.inputs + self.outputs != self.io:
        self.flags = [0 for _ in range(self.total_inputs)]
    self.io = self.inputs + self.outputs


def flag_push(self, time):
    check_io(self)
    self.output_data = self._push(time)
    for f in range(len(self.flags)):
        if self.flags[f] != time:
            self.flags[f] = time
            break
    sync = True
    value = self.flags[0]
    found = 0
    for f in range(len(self.flags)):
        clear = self.flags[f] == value or self.flags[f] == 0
        found += clear
        sync = sync and clear
    if sync and found >= len(self.inputs):
        for output in self.outputs:
            output.push(time)


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
