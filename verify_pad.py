import ctypes, time, sys

x = ctypes.WinDLL("xinput1_4.dll")

class S(ctypes.Structure):
    _fields_ = [("pkt", ctypes.c_uint32), ("btn", ctypes.c_uint16),
                ("lt", ctypes.c_ubyte), ("rt", ctypes.c_ubyte),
                ("lx", ctypes.c_short), ("ly", ctypes.c_short),
                ("rx", ctypes.c_short), ("ry", ctypes.c_short)]

NAMES = {
    0x0001: "DUP", 0x0002: "DDOWN", 0x0004: "DLEFT", 0x0008: "DRIGHT",
    0x0010: "START", 0x0020: "BACK", 0x0040: "LTHUMB", 0x0080: "RTHUMB",
    0x0100: "LB", 0x0200: "RB", 0x1000: "A", 0x2000: "B", 0x4000: "X", 0x8000: "Y",
}

s = S()
if x.XInputGetState(0, ctypes.byref(s)) != 0:
    print("no virtual pad on slot 0"); sys.exit(1)

print("watching virtual Xbox pad for 300s\n", flush=True)
prev = (s.btn, s.lt // 16, s.rt // 16, s.lx // 2048, s.ly // 2048, s.rx // 2048, s.ry // 2048)
t0 = time.time()
while time.time() - t0 < 300:
    s = S()
    if x.XInputGetState(0, ctypes.byref(s)) != 0:
        time.sleep(0.05); continue
    cur = (s.btn, s.lt // 16, s.rt // 16, s.lx // 2048, s.ly // 2048, s.rx // 2048, s.ry // 2048)
    if cur != prev:
        names = [n for bit, n in NAMES.items() if s.btn & bit]
        extra = []
        if s.lt > 10: extra.append("LT=%d" % s.lt)
        if s.rt > 10: extra.append("RT=%d" % s.rt)
        for lbl, v in (("LX", s.lx), ("LY", s.ly), ("RX", s.rx), ("RY", s.ry)):
            if abs(v) > 3000: extra.append("%s=%d" % (lbl, v))
        print("t=%5.1f  %s" % (time.time() - t0, " ".join(names + extra) or "-"), flush=True)
        prev = cur
    time.sleep(0.01)
print("done")
