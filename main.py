from physics import *
from sound import *
from screen import *

window = pygame.display.set_mode((1200, 600))
pygame.display.set_caption("Synth Stomp")

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
