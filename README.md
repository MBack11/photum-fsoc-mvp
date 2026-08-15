# phoTUM Free-Space Optical Link — MVP

A working free-space optical link that sends **live image tiles over a red laser** — built and demonstrated with [phoTUM](https://photum.org/) at Photonics Night (TUM, July 2026).

Host software frames the picture, an Arduino drives a KY-008 with on–off keying, light crosses ~1.5 m of free space, and a photodiode front-end plus Raspberry Pi Pico feed a receiver GUI that paints the image tile by tile. An interactive 3D twin lets you explore the same setup in the browser.

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

## Protocol

Images travel as **JPEG tiles** inside small serial **frames** (`0x02` … CRC-16 … `0x03`). Special sequence numbers announce the full image size and each tile’s position; the optical channel itself is plain OOK.

Details: [`software/protocol.md`](software/protocol.md).

## Repository layout

| Path | Contents |
|------|----------|
| [`digital-twin/`](digital-twin/) | React Three Fiber viewer (`FSOC.glb`), clickable parts, explode view |
| [`software/`](software/) | Frame protocol, `sender.py`, `receiver.py` |

## My role

I led this MVP in the **phoTUM** student club at TUM — from system overview down to the pieces that make the link work. In particular I contributed to:

- **3D-printed hardware** — receiver aperture / mechanics that keep the optical path aligned and cut ambient light  
- **Receiver electronics** — BPW34 + LM393 front-end into the Pico  
- **Host software** — framing / protocol work and the sender–receiver GUI path for live tiled images (with the club team)

Hardware, digital twin, and software were a **team** effort; this repo packages the public snapshot of the demo. Club context: [photum.org](https://photum.org/).
