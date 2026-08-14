# Transmission protocol (host ↔ microcontrollers)

Images are sent as JPEG tiles over a framed serial protocol. The optical channel uses on–off keying (OOK).

## Frame layout

```
+------------+---------------+----------------+---------------+----------+----------+
| START 0x02 | SEQ (uint16)  | LEN (uint8)    | PAYLOAD       | CRC-16   | END 0x03 |
| 1 byte     | big-endian    | N              | N bytes       | 2 bytes  | 1 byte   |
+------------+---------------+----------------+---------------+----------+----------+
```

- CRC-16: `binascii.crc_hqx` over `(SEQ || LEN || PAYLOAD)`, init `0xFFFF`
- ACK from the TX microcontroller after each frame: `0x06`
- Default payload chunk size: **32 bytes**

## Special sequence numbers

| SEQ | Meaning |
|-----|---------|
| `0xFFFE` | Global image meta: width, height (`uint16`, `uint16`) |
| `0xFFFF` | Tile meta: x, y, jpeg_length (`uint16`, `uint16`, `uint32`) |
| `0…` | Tile payload chunks |

## Pipeline

1. **Parser / sender GUI** — splits the image into tiles, JPEG-compresses each tile, builds frames
2. **TX MCU** — drives the KY-008 with OOK
3. **RX front-end** — BPW34 + LM393 → Pico
4. **Receiver GUI** — CRC check, reassemble tiles into the full RGB image, show live progress

See also the internal architecture notes in [`protocol-notes.md`](protocol-notes.md).

## Next steps (club roadmap)

- Manchester encoding
- Stronger recovery for lost tiles under misalignment
