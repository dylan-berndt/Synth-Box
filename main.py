from physics import *
from sound import *
from screen import *

import pyaudio

window = pygame.display.set_mode((1200, 600))
pygame.display.set_caption("Synth Stomp")

speaker = Speaker(Vector2(0, 0))
decay = Decay(Vector2(0, 0))
oscillator = Oscillator(Vector2(0, 0))

speaker.inputs = [decay]
decay.inputs = [oscillator]

audio = pyaudio.PyAudio()
stream = audio.open(format=pyaudio.paFloat32, channels=1, rate=sampleRate, output=True)
stream.write(speaker.process().astype(np.float32).tobytes())
stream.stop_stream()
stream.close()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_t:
                if event.mod & pygame.KMOD_LSHIFT | pygame.KMOD_RSHIFT:
                    pass

            if event.key == pygame.K_SPACE:
                pass

    pygame.display.update()
