# Receiver electronics

The free-space optical receiver reconstructs a clean digital bitstream from the photodiode current.

## Front-end

- **BPW34** photodiode — converts the focused 650 nm beam into photocurrent
- **LM393** comparator with Schmitt-trigger hysteresis — thresholds the signal and rejects small ambient-light fluctuations
- Output goes to the **Raspberry Pi Pico**, which recovers UART-like frames and forwards them over USB serial to the host GUI

Schematic and breadboard photos are documented on the club MVP page:

→ [Receiver circuit on photum.org/mvp.html](https://photum.org/mvp.html#electronics)

If `circuit.png` is present in this folder, it is the same schematic used on that page.

## Design notes

- Hysteresis is essential: the free-space channel and ambient light make a single threshold unreliable.
- The mechanical aperture (see [`../hardware`](../hardware/)) reduces ambient light before the detector; the comparator finishes the job electrically.
- Demo baud rate at Photonics Night: **19 200**; lab GUIs also support **38 400**.
