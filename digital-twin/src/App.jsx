import { Suspense, useEffect, useRef, useState } from 'react'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { OrbitControls, Environment, Html } from '@react-three/drei'
import * as THREE from 'three'
import Experiment from './Experiment.jsx'
import { PARTS } from './parts.js'

// Normalize names (Three.js may replace spaces with underscores)
const norm = (s) => (s || '').toLowerCase().replace(/[\s_]+/g, ' ').trim()

const LASER_INFO = {
  label: 'KY-008 Laser Module',
  desc: 'The KY-008 is the optical transmitter of the setup. It converts the digital signal from the microcontroller into modulated red laser light and directs it toward the receiver. It currently sends 01010000011010000110111101110100011 1010101101101 which is Photum in ASCII.',
  specs: {
    Model: 'KY-008',
    Role: 'Optical transmitter',
    Control: 'Digital input signal'
  }
}

const PHOTODIODE_INFO = {
  label: 'BPW34 Photodiode',
  desc: 'The BPW34 detects the incoming laser light and converts it into a photocurrent. The receiver circuit converts this current into a voltage and reconstructs the transmitted digital signal.',
  specs: {
    Model: 'BPW34',
    Role: 'Optical receiver',
    'Operating mode': 'Reverse-biased photodiode'
  }
}

const FASTENER_INFO = {
  label: 'Fasteners',
  desc: 'Standard screws, bolts, and nuts secure the optical components and their mounts to the rail.',
  specs: {
    Category: 'Standard hardware',
    Function: 'Mechanical fastening'
  }
}

const COMPONENT_INFO = {
  'tubus-1': {
    label: 'Lens Barrel',
    desc: 'Holds the lens and keeps it aligned with the optical axis.',
    specs: { Function: 'Lens positioning', Material: '3D-printed polymer' }
  },
  'linse-1': {
    label: 'Lens',
    desc: 'Collects the incoming laser light and focuses it onto the BPW34 photodiode.',
    specs: { Function: 'Optical focusing', Material: 'Optical glass' }
  },
  'röhre-1': {
    label: 'Receiver Tube',
    desc: 'Shields the optical path from ambient light and keeps the receiver components aligned.',
    specs: { Function: 'Light shielding and alignment', Material: '3D-printed polymer' }
  },
  'schiene-1': {
    label: 'Mounting Rail',
    desc: 'Provides a rigid reference for aligning the transmitter and receiver assemblies.',
    specs: { Function: 'Mechanical alignment', Material: 'Metal' }
  },
  'kleiner deckel-1': {
    label: 'Rear Cover',
    desc: 'Closes the receiver housing and protects the photodiode and internal components.',
    specs: { Function: 'Protection and enclosure', Material: '3D-printed polymer' }
  },
  'untersatz-1': {
    label: 'Receiver Base',
    desc: 'Connects the receiver assembly to the mounting rail.',
    specs: { Function: 'Receiver support', Material: '3D-printed polymer' }
  },
  'wippe untersatz-1': {
    label: 'Transmitter Base',
    desc: 'Supports the adjustable laser holder on the mounting rail.',
    specs: { Function: 'Transmitter support', Material: '3D-printed polymer' }
  },
  'wippe oben-1': {
    label: 'Laser Holder',
    desc: 'Holds the KY-008 module and allows its direction to be aligned with the receiver.',
    specs: { Function: 'Laser positioning', Material: '3D-printed polymer' }
  }
}

const getInfo = (name) => {
  const n = norm(name)
  if (n.includes('laser')) return LASER_INFO
  if (n.includes('diode')) return PHOTODIODE_INFO
  if (COMPONENT_INFO[n]) return COMPONENT_INFO[n]
  const key = Object.keys(PARTS).find((k) => norm(k) === n)
  return key ? PARTS[key] : null
}

function Loader() {
  return (
    <Html center>
      <div className="loader">Loading model…</div>
    </Html>
  )
}

function CameraRig({ exploded, focus }) {
  const camera = useThree((state) => state.camera)
  const controls = useThree((state) => state.controls)
  const fromPosition = useRef(new THREE.Vector3())
  const toPosition = useRef(new THREE.Vector3())
  const fromTarget = useRef(new THREE.Vector3())
  const toTarget = useRef(new THREE.Vector3())
  const elapsed = useRef(0)
  const active = useRef(false)

  useEffect(() => {
    if (!controls) return

    fromPosition.current.copy(camera.position)
    fromTarget.current.copy(controls.target)

    if (exploded && focus) {
      toTarget.current.fromArray(focus.target)
      const viewDirection = new THREE.Vector3(0, 0.18, 1).normalize()
      toPosition.current.copy(toTarget.current).addScaledVector(viewDirection, focus.distance)
    } else {
      toTarget.current.set(0, 0, 0)
      toPosition.current.set(2.8, 1.7, 3.3)
    }

    elapsed.current = 0
    active.current = true
  }, [camera, controls, exploded, focus])

  useFrame((_, delta) => {
    if (!active.current || !controls) return

    elapsed.current = Math.min(1, elapsed.current + delta / 0.85)
    const t = elapsed.current
    const eased = t * t * (3 - 2 * t)

    camera.position.lerpVectors(fromPosition.current, toPosition.current, eased)
    controls.target.lerpVectors(fromTarget.current, toTarget.current, eased)
    controls.update()

    if (t >= 1) active.current = false
  })

  return null
}

export default function App() {
  const [selected, setSelected] = useState(null)   // Node name | 'fasteners' | null
  const [exploded, setExploded] = useState(false)
  const [explosionFocus, setExplosionFocus] = useState(null)

  const info = selected === 'fasteners' ? FASTENER_INFO : getInfo(selected)

  return (
    <div className="app">
      {/* ---------- 3D scene ---------- */}
      <Canvas
        className="canvas"
          dpr={[1, 1.5]}
  gl={{
    antialias: true,
    powerPreference: 'high-performance'
  }}
        camera={{ position: [2.8, 1.7, 3.3], fov: 42 }}
        onPointerMissed={() => setSelected(null)}
      >
        <color attach="background" args={['#e6ebf2']} />
        <ambientLight intensity={0.5} />
        <hemisphereLight args={['#ffffff', '#e8edf2', 0.7]} />
        <directionalLight position={[5, 8, 5]} intensity={1.1} />
        <directionalLight position={[-6, 3, -4]} intensity={0.3} color="#3b8ef0" />

        <Suspense fallback={<Loader />}>
          <Experiment
            selected={selected}
            exploded={exploded}
            onSelect={setSelected}
            onFocusReady={setExplosionFocus}
          />
          {/* Environment lighting for glass and metal reflections. Remove for offline use. */}
          <Environment preset="city" />
        </Suspense>

        <OrbitControls
          makeDefault
          enableDamping
          dampingFactor={0.08}
          minDistance={0.4}
          maxDistance={18}
        />
        <CameraRig exploded={exploded} focus={explosionFocus} />
      </Canvas>

      {/* ---------- Title overlay ---------- */}
      <header className="topbar">
        <div className="eyebrow">Experiment Model</div>
        <h1>Free-Space Optical Link <span>· Transmitter and Receiver</span></h1>
      </header>

      {/* ---------- Toolbar overlay ---------- */}
      <div className="toolbar">
        <button
          className={exploded ? 'btn active' : 'btn'}
          onClick={() => setExploded((v) => !v)}
        >
          {exploded ? 'Assemble' : 'Exploded View'}
        </button>
        {selected && (
          <button className="btn" onClick={() => setSelected(null)}>
            Clear Selection
          </button>
        )}
      </div>

      {/* ---------- Interaction hint ---------- */}
      {!selected && (
        <div className="hint">Drag to rotate · Click a component for details</div>
      )}

      {/* ---------- Information panel ---------- */}
      <aside className={info ? 'panel open' : 'panel'}>
        {info && (
          <>
            <button className="panel-close" onClick={() => setSelected(null)}>✕</button>
            <div className="panel-tag">
              {selected === 'fasteners' ? 'Standard Parts' : 'Component'}
            </div>
            <h2>{info.label}</h2>
            <p>{info.desc}</p>
            <div className="specs">
              {Object.entries(info.specs || {}).map(([k, v]) => (
                <div className="spec-row" key={k}>
                  <span>{k}</span>
                  <span>{v}</span>
                </div>
              ))}
            </div>
          </>
        )}
      </aside>
    </div>
  )
}
