# Optics & Mechanics — FSOC Link (V1.0)

This directory contains the SolidWorks files and documentation for the **optical receiver assembly** and the **laser alignment mechanics** of our Free-Space Optical Communication (FSOC) link.

The receiver optics collect the incoming 650 nm beam and focus it onto the photodiode while shielding it from ambient light. The mechanics carry the laser and allow its beam to be aimed at the receiver over the demo distance. All custom parts are FDM 3D-printed; the lens, rail, fasteners and springs are off-the-shelf components.

This is an **interim documentation**: the state described here corresponds to the working V1.0 link. The subsystem is functional but not finished — open points are listed under [Next steps](#next-steps).

---

## File naming

| SolidWorks file | Original (DE) | Function |
|---|---|---|
| `Lens_Hood` | Tubus | Front shroud, clamps and shades the lens |
| `Cone` | Röhre / Cone | Main receiver barrel |
| `End_Cap` | Deckel | Screw-on rear cap carrying the photodiode |
| `Receiver_Base` | Untersatz | Interface between barrel and rail slider |
| `Rocker` | Mechanische Wippe | Tilting laser mount (vertical aiming) |
| `Rocker_Base` | Untersatz der mechanischen Wippe | Fulcrum and spring anchor for the rocker |
| `Slider` | Slider | Runs inside the rail, carries the assemblies |

---

## Receiver optics

**`Lens_Hood`** — Front section of the receiver. It serves two purposes:
1. Shades the lens aperture so that as little ambient light as possible reaches the photodiode and degrades its sensitivity.
2. Clamps the lens against the front face of the `Cone`.

Bolt holes connect it to the `Cone` and the `Receiver_Base`.

**`Cone`** — Main barrel of the receiver:
1. Its front face forms the seat for the lens, which is clamped between this seat and the `Lens_Hood`.
2. Its rear end carries an internal thread for the `End_Cap`, allowing the photodiode distance to be varied over a range of **100 mm ± 15 mm** by screwing the cap in or out.

Bolt holes connect it to the `Lens_Hood` and the `Receiver_Base`.

**`End_Cap`** — Screwed into the rear thread of the `Cone`. The photodiode is glued to its inner face; turning the cap sets the lens–detector distance.

**`Receiver_Base`** — Structural link between the optical assembly and the rail. Four holes in the upper saddles bolt to `Lens_Hood` and `Cone`; two holes in the base plate bolt to the `Slider`.

**Lens** (off-the-shelf) — 50 × 50 × 2.5 mm, focal length 100 mm.
[Product link](https://www.amazon.de/dp/B08K7JBJVK)

---

## Laser alignment mechanics

**`Rocker`** — Adjusts the vertical (pitch) direction of the laser. It rests on the elliptical fulcrum of the `Rocker_Base`; the remainder of the part is unsupported. Two tension springs preload the rocker against the base, and a set screw acts against that preload: how far the screw is driven in determines the tilt angle, and therefore the elevation of the beam.

> Note: the laser cut-out in this part was printed undersized and had to be reworked by hand. Enlarge it in the next revision.

**`Rocker_Base`** — Carries the elliptical fulcrum in its centre, a clearance hole for the M5 set screw, and two further recesses for the tension springs. The springs are anchored by a continuous pin running through the underside of the part.

---

## Hardware

| Item | Spec |
|---|---|
| Bolts | M8 throughout |
| Nuts | M8, matching the bolts |
| Set screw (rocker) | M5 |
| Tension springs | Ø 4.5 × 16.9 × 0.5 mm |

---

## Rail

| Item | Spec |
|---|---|
| Rail | 2000 mm (length) × 30 mm (height) × 28 mm (width) |
| Slider | Fits the rail profile without additional shimming |

Both the receiver assembly and the laser mechanics are mounted on sliders, so the link distance can be set anywhere along the rail.

---

## Next steps

**1 — Redesign the alignment mechanics (priority).** The current rocker does not provide a usable fine adjustment: the set screw acting against the spring preload is too coarse to resolve small angles, and there is no horizontal adjustment at all. This is the main limitation of the subsystem. Target for the next revision: a fine-pitch adjustment screw and a second axis, i.e. a proper two-axis kinematic mount.

**2 — Rework the `Rocker` laser cut-out.** The printed cut-out is undersized and was widened by hand. Correct it in the CAD model so the part is usable straight off the printer.

**3 — Apply a consistent print allowance.** Printed features come out systematically undersized. Adopt roughly 1 mm of clearance on every mating feature as a design rule (e.g. model a 9 mm hole for an M8 bolt) and update the existing parts accordingly.

**4 — Characterise the detector position.** Placing the photodiode exactly in the focal plane turned out not to be optimal; a position slightly in front of the focus enlarges the spot and makes the link more tolerant to residual misalignment. The `End_Cap` thread allows 100 mm ± 15 mm — the working point should be measured properly (received signal level vs. cap position) instead of set by trial and error.

**5 — Ambient light rejection.** With the `Lens_Hood` alone, performance under daylight is untested. Evaluate whether a bandpass filter (650 nm) in front of the lens is needed for the demo.

