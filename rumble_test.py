"""DualSense Bluetooth rumble probe: read firmware + run a distinguishable pattern test."""
import struct, sys, time, zlib
import hid

VID, PID = 0x054C, 0x0CE6


def crc_bt(d74: bytes) -> bytes:
    return struct.pack("<I", zlib.crc32(b"\xA2" + d74) & 0xFFFFFFFF)


def build(rumble_left, rumble_right, legacy=False):
    d = bytearray(78)
    d[0] = 0x31
    d[1] = 0x02
    if legacy:
        d[2] |= 0x01
        d[2] |= 0x02
        d[4] = rumble_right >> 1
        d[5] = rumble_left >> 1
    else:
        d[2] |= 0x02
        d[4] = rumble_right
        d[5] = rumble_left
        d[40] |= 0x04
    d[74:78] = crc_bt(bytes(d[:74]))
    return bytes(d)


def open_dev():
    for x in hid.enumerate():
        if x["vendor_id"] == VID and x["product_id"] == PID:
            dev = hid.device(); dev.open_path(x["path"]); return dev
    return None


def hold(dev, seconds, left=255, right=255, legacy=False):
    pkt = build(left, right, legacy=legacy)
    t0 = time.time()
    while time.time() - t0 < seconds:
        dev.write(pkt)
        time.sleep(0.05)


def stop(dev):
    dev.write(build(0, 0, legacy=False))
    dev.write(build(0, 0, legacy=True))


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "pattern"
    dev = open_dev()
    if not dev:
        print("controller not found"); sys.exit(1)

    if mode == "fw":
        try:
            r = dev.get_feature_report(0x20, 64)
            print("feature 0x20 len:", len(r))
            print("bytes 40..50:", " ".join("%02x" % b for b in r[40:50]))
            print("firmware (offset 44-45): 0x%04X" % (r[44] | (r[45] << 8)))
        except Exception as e:
            print("feature read failed:", e)
        sys.exit(0)

    # Modern path: three short buzzes.  Legacy path: one long buzz.
    print("phase A: three short buzzes (modern packet)", flush=True)
    for _ in range(3):
        hold(dev, 0.30, legacy=False)
        stop(dev); time.sleep(0.25)
    stop(dev)
    time.sleep(2.0)

    print("phase B: one long buzz (legacy packet)", flush=True)
    hold(dev, 2.0, legacy=True)
    stop(dev)
    print("done")
