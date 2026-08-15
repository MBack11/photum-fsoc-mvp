# phoTUM Free-Space Optical Link — MVP

Interactive digital twin and host software for the [phoTUM](https://photum.org/) free-space optical (FSOC) link demonstrated at Photonics Night (TUM, July 2026).

**Live 3D twin:** [mback11.github.io/photum-fsoc-mvp](https://mback11.github.io/photum-fsoc-mvp/)  
**Club write-up:** [photum.org/mvp.html](https://photum.org/mvp.html)

## Demo results

| Spec | Value |
|------|--------|
| Modulation | On–off keying (OOK) |
| Demo baud rate | 19 200 baud |
| GUI / lab baud rate | up to 38 400 baud |
| Range | ~1.5 m (limited by the KY-008 laser) |
| Payload | Live image tiles across the free-space link |

## Data path

```
Host (sender GUI)
  → Arduino (OOK drive)
  → KY-008 laser (650 nm)
  → free space
  → lens + 3D-printed receiver aperture
  → BPW34 photodiode
  → LM393 comparator (Schmitt trigger)
  → Raspberry Pi Pico
  → Host (receiver GUI)
```

## Repository layout

| Path | Contents |
|------|----------|
| [`digital-twin/`](digital-twin/) | React Three Fiber viewer (`FSOC.glb`), clickable parts, explode view |
| [`software/`](software/) | Frame protocol, `sender.py`, `receiver.py` |

## Protocol (short)

Images are sent as **JPEG tiles** in small serial **frames** (start `0x02`, sequence, length, payload, CRC-16, end `0x03`). Special sequences mark the full image size (`0xFFFE`) and each tile’s position/length (`0xFFFF`); normal sequences carry the JPEG bytes. The laser channel itself is plain OOK.

Full write-up: [`software/protocol.md`](software/protocol.md).

## My role

Work done in the phoTUM student club at TUM. This public repo packages the MVP for portfolio use. Hardware and digital twin are a **team** effort — see [photum.org](https://photum.org/). As project lead I overviewed the whole process and especially contributed to the 3D printed hardware as well as to the electronics.

## Quick start

### Digital twin

```bash
cd digital-twin
npm install
npm run dev
```

### Host software (image over laser)

Needs Python 3 with PyQt6, pyserial, Pillow, numpy, and opencv-python.

```bash
cd software
python3 -m venv .venv && source .venv/bin/activate
pip install PyQt6 pyserial Pillow numpy opencv-python
python sender.py    # TX host
python receiver.py  # RX host
```

Firmware for the Arduino OOK driver and Pico receiver is not in this snapshot yet; the serial frame format is documented in [`software/protocol.md`](software/protocol.md).

## Attribution

Built with **[phoTUM](https://photum.org/)**, Photonics Student Club at the Technical University of Munich.  
Contact: photum.studentclub@gmail.com
