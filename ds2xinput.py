#!/usr/bin/env python3
"""
GameRobo RH-5188 (Bluetooth) -> virtual Xbox 360 pad.

Why this exists
---------------
The controller advertises VID 054C / PID 0CE6 (DualSense) but streams its
input as report ID 0x01 with a nonstandard payload. Windows' HID parser and
browsers' Gamepad API therefore decode it wrong, and DS4Windows never even
sees it.

SDL, however (what Steam and most games use), decodes it correctly:
    Cross=0  Circle=1  Square=2  Triangle=3  Create=4  PS=5  Options=6
    L3=7  R3=8  L1=9  R1=10  Dpad=11/12/13/14
    axes: LX=0 LY=1 RX=2 RY=3 L2=4 R2=5

So we read the pad through SDL and emit a real Xbox 360 controller through
ViGEmBus (already installed, signed kernel driver). User-mode only.

Usage:
    python ds2xinput.py            # map pad -> virtual Xbox 360
    python ds2xinput.py --list     # list SDL joysticks
    python ds2xinput.py --probe    # watch SDL button/axis changes
"""

import argparse
import os
import struct
import sys
import time
import zlib

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
os.environ.setdefault("SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS", "1")

# pythonw.exe has no stdout/stderr; print() would crash there
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")

# SDL button indices (standard DualSense mapping)
BTN_X, BTN_CIRCLE, BTN_SQUARE, BTN_TRI = 0, 1, 2, 3
BTN_CREATE, BTN_PS, BTN_OPTIONS = 4, 5, 6
BTN_L3, BTN_R3 = 7, 8
BTN_L1, BTN_R1 = 9, 10
BTN_UP, BTN_DOWN, BTN_LEFT, BTN_RIGHT = 11, 12, 13, 14

TITLE_OK = ("dualsense", "wireless controller", "ps5")

VID_SONY, PID_DUALSENSE = 0x054C, 0x0CE6
RUMBLE_HZ = 20


def _crc_bt(d74):
    """DualSense BT output CRC: CRC-32 seeded with the hidp header 0xA2."""
    return struct.pack("<I", zlib.crc32(b"\xA2" + d74) & 0xFFFFFFFF)


def build_rumble(left, right):
    """78-byte DualSense BT effects report, modern-rumble path (fw >= 2.24)."""
    d = bytearray(78)
    d[0] = 0x31
    d[1] = 0x02
    d[2] |= 0x02          # disable audio haptics
    d[4] = right & 0xFF   # small / high-frequency motor
    d[5] = left & 0xFF    # large / low-frequency motor
    d[40] |= 0x04         # enableBits3: improved rumble emulation
    d[74:78] = _crc_bt(bytes(d[:74]))
    return bytes(d)


def open_output_device():
    """Separate hidapi handle used only for rumble output reports."""
    try:
        import hid
        for x in hid.enumerate():
            if x["vendor_id"] == VID_SONY and x["product_id"] == PID_DUALSENSE:
                dev = hid.device()
                dev.open_path(x["path"])
                return dev
    except Exception:
        pass
    return None


def open_joystick():
    import pygame
    pygame.init()
    pygame.joystick.init()
    pygame.event.pump()          # let SDL process hot-plug events
    count = pygame.joystick.get_count()
    if count == 0:
        return None

    chosen = None
    for i in range(count):
        j = pygame.joystick.Joystick(i)
        j.init()
        name = (j.get_name() or "").lower()
        if any(t in name for t in TITLE_OK):
            chosen = j
            break
    # Never fall back to joystick 0: that is the virtual Xbox pad this
    # process creates, and reading our own output makes the pad look alive
    # while ignoring the real controller. Wait for the DualSense instead.
    return chosen


def list_pads():
    import pygame
    pygame.init()
    pygame.joystick.init()
    print("SDL joysticks:", pygame.joystick.get_count())
    for i in range(pygame.joystick.get_count()):
        j = pygame.joystick.Joystick(i); j.init()
        print("  [%d] %-36s axes=%d buttons=%d hats=%d" %
              (i, j.get_name(), j.get_numaxes(), j.get_numbuttons(), j.get_numhats()))


def probe():
    import pygame
    j = open_joystick()
    if not j:
        print("controller not found"); return 1
    print("device:", j.get_name())
    print("press buttons; Ctrl+C to stop\n")
    prev = None
    while True:
        pygame.event.pump()
        state = (tuple(j.get_button(b) for b in range(j.get_numbuttons())),
                 tuple(round(j.get_axis(a), 2) for a in range(j.get_numaxes())))
        if state != prev:
            btns, axes = state
            print("buttons=%s axes=%s" % ([b for b, v in enumerate(btns) if v] or "-",
                                          ["a%d=%+.2f" % (i, v) for i, v in enumerate(axes) if abs(v) > 0.2] or "-"),
                  flush=True)
            prev = state
        time.sleep(0.008)


def run():
    import pygame
    import vgamepad as vg

    pad = vg.VX360Gamepad()
    B = vg.XUSB_BUTTON
    held = set()

    # --- rumble: game -> virtual pad -> real DualSense ---
    rumble = {"left": 0, "right": 0}

    def on_rumble(client, target, large_motor, small_motor, led_number, user_data):
        rumble["left"] = large_motor
        rumble["right"] = small_motor

    pad.register_notification(on_rumble)
    out = open_output_device()
    tx_last = 0.0
    tx_active = False

    def set_btn(btn, down):
        if down and btn not in held:
            pad.press_button(btn); held.add(btn)
        elif not down and btn in held:
            pad.release_button(btn); held.discard(btn)

    def trig(v):
        t = max(0.0, min(1.0, (v + 1.0) / 2.0))
        return 0.0 if t < 0.12 else t          # this clone's L2 rests slightly engaged

    def dz(v, d=0.08):
        return 0.0 if abs(v) < d else v

    while True:                                # survive disconnects / late connection
        j = open_joystick()
        if not j:
            print("waiting for controller...", flush=True)
            time.sleep(2)
            continue

        print("controller:", j.get_name(), flush=True)
        if not held and not getattr(run, "_announced", False):
            print("virtual Xbox 360 pad created (ViGEmBus)", flush=True)
            run._announced = True

        try:
            while True:
                pygame.event.pump()

                # sticks: SDL y grows downward, XInput y grows upward
                pad.left_joystick_float(dz(j.get_axis(0)), -dz(j.get_axis(1)))
                pad.right_joystick_float(dz(j.get_axis(2)), -dz(j.get_axis(3)))
                pad.left_trigger_float(trig(j.get_axis(4)))
                pad.right_trigger_float(trig(j.get_axis(5)))

                set_btn(B.XUSB_GAMEPAD_A, j.get_button(BTN_X))
                set_btn(B.XUSB_GAMEPAD_B, j.get_button(BTN_CIRCLE))
                set_btn(B.XUSB_GAMEPAD_X, j.get_button(BTN_SQUARE))
                set_btn(B.XUSB_GAMEPAD_Y, j.get_button(BTN_TRI))

                set_btn(B.XUSB_GAMEPAD_LEFT_SHOULDER, j.get_button(BTN_L1))
                set_btn(B.XUSB_GAMEPAD_RIGHT_SHOULDER, j.get_button(BTN_R1))
                set_btn(B.XUSB_GAMEPAD_LEFT_THUMB, j.get_button(BTN_L3))
                set_btn(B.XUSB_GAMEPAD_RIGHT_THUMB, j.get_button(BTN_R3))
                set_btn(B.XUSB_GAMEPAD_BACK, j.get_button(BTN_CREATE))
                set_btn(B.XUSB_GAMEPAD_START, j.get_button(BTN_OPTIONS))
                set_btn(B.XUSB_GAMEPAD_GUIDE, j.get_button(BTN_PS))

                set_btn(B.XUSB_GAMEPAD_DPAD_UP, j.get_button(BTN_UP))
                set_btn(B.XUSB_GAMEPAD_DPAD_DOWN, j.get_button(BTN_DOWN))
                set_btn(B.XUSB_GAMEPAD_DPAD_LEFT, j.get_button(BTN_LEFT))
                set_btn(B.XUSB_GAMEPAD_DPAD_RIGHT, j.get_button(BTN_RIGHT))

                pad.update()

                # forward game rumble to the physical pad
                now = time.time()
                if rumble["left"] or rumble["right"]:
                    if out is not None and now - tx_last >= 1.0 / RUMBLE_HZ:
                        try:
                            out.write(build_rumble(rumble["left"], rumble["right"]))
                        except Exception:
                            out = open_output_device()
                        tx_last = now
                    tx_active = True
                elif tx_active:
                    if out is not None:
                        try:
                            out.write(build_rumble(0, 0))
                        except Exception:
                            out = open_output_device()
                    tx_active = False

                time.sleep(0.008)
        except Exception as e:
            print("controller lost (%s) - waiting..." % e, flush=True)
            for b in list(held):
                pad.release_button(b)
            held.clear()
            pad.reset()
            pad.update()
            pygame.joystick.quit()
            pygame.joystick.init()
            time.sleep(1.5)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    if a.list:
        list_pads(); sys.exit(0)

    try:
        sys.exit(probe() if a.probe else run())
    except KeyboardInterrupt:
        print("\nstopped")
