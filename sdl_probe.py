import os, time, sys
os.environ["SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS"] = "1"
import pygame

pygame.init(); pygame.joystick.init()
if pygame.joystick.get_count() == 0:
    print("no joystick"); sys.exit(1)
j = pygame.joystick.Joystick(0); j.init()
print("device:", j.get_name())
print("axes=%d buttons=%d hats=%d" % (j.get_numaxes(), j.get_numbuttons(), j.get_numhats()))
print("listening 10 min - press buttons now\n")

prev = None
t0 = time.time()
while time.time() - t0 < 600:
    pygame.event.pump()
    state = (
        tuple(round(j.get_axis(a), 2) for a in range(j.get_numaxes())),
        tuple(j.get_button(b) for b in range(j.get_numbuttons())),
        tuple(j.get_hat(h) for h in range(j.get_numhats())),
    )
    if state != prev:
        axes, btns, hats = state
        pressed = [b for b, v in enumerate(btns) if v]
        moved = ["a%d=%+.2f" % (i, v) for i, v in enumerate(axes) if abs(v) > 0.15]
        print("t=%5.1f  buttons=%s  axes=%s  hats=%s" % (time.time() - t0, pressed or "-", moved or "-", hats or "-"), flush=True)
        prev = state
    time.sleep(0.008)
print("done")
