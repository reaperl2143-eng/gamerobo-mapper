"""Ask the virtual Xbox pad (slot 0) to vibrate, exactly like a game would."""
import ctypes, time

x = ctypes.WinDLL("xinput1_4.dll")

class V(ctypes.Structure):
    _fields_ = [("left", ctypes.c_ushort), ("right", ctypes.c_ushort)]

print("3 bursts via XInputSetState on slot 0")
for i in range(3):
    v = V(65535, 65535)
    rc = x.XInputSetState(0, ctypes.byref(v))
    print("  burst %d rc=%d" % (i + 1, rc), flush=True)
    time.sleep(0.9)
    v = V(0, 0)
    x.XInputSetState(0, ctypes.byref(v))
    time.sleep(0.5)
print("done")
