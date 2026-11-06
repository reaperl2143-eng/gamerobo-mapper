# GameRobo RH-5188 → Xbox 360 (Bluetooth)

This controller advertises itself as a **DualSense** (VID `054C`, PID `0CE6`) but
sends its input as **report ID `0x01`** with a nonstandard 77-byte payload.

That single wrong report ID is why:

- Windows/browsers show the device but with scrambled or dead controls
- **DS4Windows never detects it at all** (it expects report `0x31`)

SDL — which Steam and most games use — decodes it correctly anyway.
So this mapper reads the pad through SDL and re-emits a **real Xbox 360 pad**
via **ViGEmBus** (already installed, signed kernel driver). No custom driver,
no admin, no cable.

## Files

| File | What it does |
|---|---|
| `ds2xinput.py` | the mapper |
| `run-mapper.cmd` | run it visibly (console + errors) |
| `stop-mapper.cmd` | stop the hidden background instance |
| `sdl_probe.py` | debug: print SDL button/axis indices |
| `verify_pad.py` | debug: watch the virtual pad's XInput output |
| `rumble_test.py` | debug: rumble the pad directly (`fw` = read firmware) |
| `vibrate_pad.py` | debug: make the virtual pad vibrate like a game would |

It also starts automatically at login (shortcut in
`shell:startup` → **GameRobo Mapper**).

## Verified mapping

| Controller | Xbox 360 |
|---|---|
| ✕ / ○ / □ / △ | A / B / X / Y |
| D-pad | D-pad |
| L1 / R1 | LB / RB |
| L2 / R2 | LT / RT (analog, 0–255) |
| L3 / R3 (stick click) | Left/Right thumb |
| Create / Options | Back / Start |
| PS button | Guide |

Sticks and trigggers have a small deadzone because this unit drifts slightly at rest.

## Rumble

Game vibration is forwarded to the real pad. The virtual pad's left/right motor
values are turned into a DualSense Bluetooth effects report (report `0x31`,
CRC-32 seeded `0xA2`) and written straight to the controller at 20 Hz.

This unit reports firmware `0x0988`, so the **modern** rumble path is used
(`enableBits3 |= 0x04`, full-strength values). Verified end to end.

## If something looks wrong

- **joypad.ai / browser tests:** you will see **two** pads — `Xbox 360 Controller
  for Windows` (the correct one) and `DualSense Wireless Controller` (the raw,
  scrambled one). Always look at the Xbox entry. Browsers read the raw HID
  descriptor directly, so they can never see the clone correctly.
- **Double input in a Steam game:** Steam Input is also translating the physical
  pad. Turn off *Steam → Settings → Controller → Steam Input for PlayStation
  controllers*.
- **Controller reconnects:** the mapper waits and re-attaches automatically.
- **Check it's running:** `Get-Process pythonw` or run `run-mapper.cmd`.

## Wired alternative (no software at all)

If you ever have a USB-C data cable: plug it in and **hold Home for 3 s** —
the light turns green and Windows sees a native `Xbox 360 Controller for
Windows`. Then you can stop this mapper.
