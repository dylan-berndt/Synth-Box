import threading
import numpy as np


def process_play(stream, process):
    data = process()
    if type(data) == int:
        return
    stream.write(data.astype(np.float32).tobytes())


def play_once(stream, process):
    play = threading.Thread(target=process_play, args=(stream, process))
    play.setDaemon(True)
    play.start()


def repeat(stream, process):
    data = process()
    if type(data) == int:
        return
    data = data.astype(np.float32).tobytes()
    while True:
        stream.write(data)


def play_repeat(stream, process):
    play = threading.Thread(target=repeat, args=(stream, process))
    play.setDaemon(True)
    play.start()


