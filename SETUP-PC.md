# GameRobo RH-5188 mapper — PC setup

This is the same thing that was set up on the laptop. **There is no custom
driver and no admin hack.** It works in two user-mode pieces:

1. **ViGEmBus** — a signed, free kernel driver that creates a *virtual Xbox 360
   controller* in Windows.
2. **ds2xinput.py** — reads the real GameRobo pad through SDL/pygame (which
   decodes its odd report correctly) and re-emits every button/stick/trigger
   through ViGEmBus as a genuine Xbox 360 pad.

Why the workaround: the GameRobo advertises itself as a DualSense
(VID `054C` / PID `0CE6`) but sends report ID `0x01` instead of `0x31`.
Windows, browsers and DS4Windows misread it. SDL (Steam/games) reads it fine,
so the mapper uses SDL.

## What you need on the PC

- Windows 10/11, 64-bit
- Bluetooth (the controller is used wirelessly)
- Python **3.10–3.12**, 64-bit, from python.org — tick **“Add python.exe to PATH”**
- ViGEmBus driver — installer is included in `vgamepad\win\vigem\install\x64\`
  (skip if the PC already has it; the installer checks)
- Python packages: `pygame`, `hidapi` — `vgamepad` is bundled in this folder

## Steps

1. **Copy this whole folder** to the PC somewhere simple, e.g. `E:\GameRobo`.
   Do not run it from inside the ZIP.

2. **Pair the controller**
   Windows Settings → Bluetooth & devices → Add device → **DualSense Wireless
   Controller** (or “Wireless Controller”).
   Put the pad in pairing mode with **PS/Home + Create** held together until the
   light bar flashes.

3. **Install the Python bits** — open Command Prompt in the folder and run:

   ```
   python -m pip install pygame hidapi
   ```

   (`vgamepad` is included in this folder, so it does not need pip. If you
   prefer, `pip install vgamepad` also works.)

4. **Install ViGEmBus if needed** — double-click
   `vgamepad\win\vigem\install\x64\ViGEmBusSetup_x64.msi`, reboot.
   If it is already installed you will see **Nefarius Virtual Gamepad Emulation
   Bus** under *Device Manager → System devices*.

5. **Test it** — double-click `run-mapper.cmd`.
   It should print `controller: ...` and then `virtual Xbox 360 pad created`.
   Leave it open; press buttons to test in any game/emulator.

   Optional checks in a second Command Prompt:
   ```
   python ds2xinput.py --list     # show SDL devices
   python ds2xinput.py --probe    # show live button/axis indices
   python verify_pad.py           # watch the virtual pad's XInput output
   ```

6. **Make it start with Windows** (optional) — double-click
   `install-autostart.cmd`. It creates a minimized `pythonw.exe` shortcut in
   your Startup folder named **GameRobo Mapper**. Re-run it any time you move
   the folder.

7. **Stop it** — run `stop-mapper.cmd`, or close the console from step 5.

## Verified mapping

| GameRobo (DualSense labels) | Virtual Xbox 360 |
|---|---|
| ✕ / ○ / □ / △ | A / B / X / Y |
| D-pad | D-pad |
| L1 / R1 | LB / RB |
| L2 / R2 | LT / RT (analog 0–255) |
| L3 / R3 (stick click) | Left / Right thumb click |
| Create / Options | Back / Start |
| PS button | Guide |

Sticks and triggers have a small deadzone because this unit drifts slightly at
rest. Game rumble is forwarded to the real pad via a DualSense Bluetooth report.

## If something looks wrong

- **Browser/joypad tests show two pads:** `Xbox 360 Controller for Windows` is
  the correct one; `DualSense Wireless Controller` is the raw, scrambled one.
  Browsers read raw HID and can never see the clone correctly. Use the Xbox one.
- **Double input in a Steam game:** Steam Input is translating the physical pad
  too. Steam → Settings → Controller → disable **Steam Input for PlayStation
  controllers**.
- **Buttons are in the wrong place on a different unit:** run `sdl_probe.py` or
  `python ds2xinput.py --probe`, then edit the `BTN_*` indices at the top of
  `ds2xinput.py`.
- **Sticks drift:** increase the `d=0.08` value in `dz()`.
- **Triggers rest half-pressed:** increase the `0.12` value in `trig()`.
- **Error about `VIGEM_ERROR_BUS_NOT_FOUND`:** ViGEmBus is not installed — do
  step 4.
- **Mapper keeps saying `waiting for controller...`:** the pad is off, paired to
  something else, or Steam grabbed it exclusively.
- **Controller sleeps/reconnects:** the mapper waits and re-attaches by itself.

## Wired alternative (no software)

With a USB-C **data** cable, plug it in and **hold Home for 3 seconds** — the
light goes green and Windows sees a native `Xbox 360 Controller for Windows`.
Then you can stop the mapper. The Bluetooth mapper is for when you want no
cable.
