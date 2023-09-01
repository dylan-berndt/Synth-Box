import threading


def play_once(stream, audio):
    play = threading.Thread(target=stream.write, args=(audio,))
    play.start()


