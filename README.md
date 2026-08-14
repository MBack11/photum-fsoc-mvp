# phoTUM Free-Space Optical Link — MVP

Interactive digital twin, receiver optics/mechanics, receiver electronics, and host software for the [phoTUM](https://photum.org/) free-space optical (FSOC) link demonstrated at Photonics Night (TUM, July 2026).

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
| [`hardware/`](hardware/) | Optics & mechanics V1.0 (lens hood, cone, rocker, rail) |
| [`electronics/`](electronics/) | Receiver front-end notes (BPW34 + LM393) |
| [`software/`](software/) | Frame protocol, `sender.py`, `receiver.py` |
| [`media/`](media/) | Prototype photos |

## My role

Work done in the phoTUM student club at TUM. This public repo packages the MVP for portfolio use. Hardware and digital twin are a **team** effort — see [photum.org](https://photum.org/). As project lead I overviewed the whole process and especially contributed to the 3D printed Hardware as well as to the Electronics. 

## Quick start

### Digital twin

```bash
cd digital-twin
npm install
npm run dev
```

### Host software (image over laser)

```bash
cd software
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python sender.py    # TX host
python receiver.py  # RX host
```

Firmware for the Arduino OOK driver and Pico receiver is not in this snapshot yet; the serial frame format is documented in [`software/protocol.md`](software/protocol.md).

## Attribution

Built with **[phoTUM](https://photum.org/)**, Photonics Student Club at the Technical University of Munich.  
Contact: photum.studentclub@gmail.com

## License

Code in this repository is released under the MIT License unless noted otherwise. CAD-derived 3D models and photos remain phoTUM project assets; reuse with attribution.
