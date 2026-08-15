# FSO link — interactive 3D digital twin

React + React Three Fiber viewer for the photum free-space optical link.

**Live:** [mback11.github.io/photum-fsoc-mvp](https://mback11.github.io/photum-fsoc-mvp/)  
Parent repo: [MBack11/photum-fsoc-mvp](https://github.com/MBack11/photum-fsoc-mvp)

## Run locally

Node.js 18+.

```bash
npm install
npm run dev
```

```bash
npm run build
npm run preview
```

## Controls

- Drag — orbit
- Scroll — zoom
- Click a part — info panel
- Exploded view — separate the assembly
- Hide fasteners — toggle screws/nuts

## Edit

- Part texts / specs → `src/parts.js` and labels in `src/App.jsx`
- Model → replace `.glb` in `public/` and update `MODEL_URL` in `src/Experiment.jsx`
- Style → `src/styles.css`

Built with [photum](https://photum.org/).
