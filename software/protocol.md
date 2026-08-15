# Transmission protocol

Two layers sit on top of each other:

1. **Optical layer** — the laser is either on or off (OOK). That carries a UART-style bit stream through free space.
2. **Frame layer** — host software packages image data into small serial frames with sequence numbers and a CRC so the receiver can rebuild the picture even if some frames are lost.

Host GUIs talk USB-serial to the microcontrollers. The microcontrollers turn those bytes into / from light. This document describes the **frame layer** used by `sender.py` / `receiver.py`.

## Why tiles?

A full JPEG is often larger than the MCU buffers and would need one long uninterrupted optical transfer. Instead the sender:

1. splits the image into a grid of tiles (default tile edge 64 px in the GUI),
2. JPEG-compresses **each tile** separately,
3. sends every tile as several small frames (default **32 payload bytes** each).

The receiver paints each decoded tile into a canvas as soon as it arrives, so you see the image fill in live.

## Frame layout

Every frame looks like this (all multi-byte integers are **big-endian**):

```
┌──────────┬─────────────┬─────────┬────────────────┬──────────┬─────────┐
│ START    │ SEQ         │ LEN     │ PAYLOAD        │ CRC-16   │ END     │
│ 0x02     │ uint16      │ uint8 N │ N bytes        │ uint16   │ 0x03    │
│ 1 byte   │ 2 bytes     │ 1 byte  │                │ 2 bytes  │ 1 byte  │
└──────────┴─────────────┴─────────┴────────────────┴──────────┴─────────┘
```

| Field | Meaning |
|-------|---------|
| `START` `0x02` | Frame delimiter — receiver searches until it sees this |
| `SEQ` | What this frame is (meta vs. data) — see table below |
| `LEN` | Payload length `N` (0…255; demo uses ≤ 32) |
| `PAYLOAD` | Meta fields or JPEG bytes |
| `CRC-16` | `binascii.crc_hqx` over `(SEQ ‖ LEN ‖ PAYLOAD)`, init `0xFFFF` |
| `END` `0x03` | Trailer — frame is rejected if this byte is wrong |

After the TX microcontroller has accepted a frame for optical send, it answers the host with ACK `0x06`. The sender waits for that before the next frame.

## Sequence numbers

| SEQ | Role | Payload |
|-----|------|---------|
| `0xFFFE` | **Image header** (once per transfer) | `width` `uint16`, `height` `uint16` |
| `0xFFFF` | **Tile header** (once per tile) | `x` `uint16`, `y` `uint16`, `jpeg_length` `uint32` |
| `0, 1, 2, …` | **Tile payload chunks** | next ≤ 32 bytes of that tile’s JPEG |

Order for one image:

```
0xFFFE  (full image size)
  0xFFFF  (tile at x,y + jpeg length)
    seq 0   chunk …
    seq 1   chunk …
    …
  0xFFFF  (next tile)
    …
```

Payload sequence numbers restart / continue as ordinary counters for the JPEG chunks of the current tile (see `sender.py`).

## End-to-end flow

```
sender.py
  → USB serial frames
  → Arduino / TX MCU  (OOK onto KY-008, 650 nm)
  → free space
  → lens + aperture → BPW34 → LM393
  → Pico / RX MCU     (bit stream → serial bytes)
  → USB serial frames
  → receiver.py       (CRC check, place tiles on canvas)
```

On the RX host:

- CRC fail → that tile is marked corrupted and not drawn.
- Missing `END` → frame discarded.
- When enough bytes for `jpeg_length` are collected, the tile JPEG is decoded and pasted at `(x, y)`.

## Demo rates

| Setting | Typical value |
|---------|----------------|
| Photonics Night demo | 19 200 baud |
| Lab / GUI | up to 38 400 baud |
| Payload chunk | 32 bytes |

## Roadmap

- Manchester encoding on the optical bit stream
- Better recovery when tiles are lost under misalignment
