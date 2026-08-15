import { useEffect, useMemo, useRef, useLayoutEffect } from 'react'
import { useFrame } from '@react-three/fiber'
import { useGLTF, Outlines } from '@react-three/drei'
import * as THREE from 'three'
import { PARTS } from './parts.js'

// Respect Vite `base` so GitHub Pages can load the model under /photum-fsoc-mvp/
const MODEL_URL = `${import.meta.env.BASE_URL}FSOC.glb`
useGLTF.preload(MODEL_URL)

// ====================================================================
//  DISPLAY AND EXPLODED-VIEW SETTINGS (matched to FSOC.glb)
// ====================================================================
// The laser is detected automatically through "laser" in the mesh name.
// The remaining names may also contain Blender suffixes such as ".001".
const KEY_ORDER = ['laser', 'Tubus-1', 'Linse-1', 'Röhre-1', 'Diode-1']
const ROW_AXIS = new THREE.Vector3(1, 0, 0)
const ROW_SPACING = 1.0

const BOLT_OUT = 1.8
const NUT_OUT = 1.8
const SCREW_OUT = 1.8
const ASIDE_DROP = 2.15
const DIODE_EXTRA_OUT = 0.35

const VERTICAL_FASTENERS = []

const MODEL_FIT = 2.1
const PART_COLOR = '#2b3138'
const EXPLODE_TIME = 1.6

const BEAM_COLOR = '#ff2b4a'
// Simulated digital transmission
const BIT_SEQUENCE = '010100000110100001101111011101000111010101101101'
const BIT_RATE = 15 // bits per second
const BEAM_RADIUS = 0.00028
const EMITTER_GLOW_RADIUS = 0.0009

const SCREW_MOVE = [0.0, 0.35]
const SCREW_FADE = [0.25, 0.55]
const ASIDE_MOVE = [0.4, 0.9]
const KEY_MOVE = [0.45, 1.0]
// ====================================================================

const norm = (s) => (s || '').toLowerCase().replace(/[\s_]+/g, ' ').trim()

const isFastener = (name) => {
  const n = norm(name)
  return n.startsWith('hex screw') || n.startsWith('hex nut') || n.startsWith('hex bolt')
}

const getInfo = (name) => {
  const n = norm(name)
  const key = Object.keys(PARTS).find((k) => norm(k) === n)
  return key ? PARTS[key] : null
}

const getKeyIndex = (name) => {
  const n = norm(name)
  if (n.includes('laser')) return 0
  if (n.includes('tubus')) return 1
  if (n.includes('linse')) return 2
  if (n.includes('röhre') || n.includes('roehre') || n.includes('rohre')) return 3
  if (n.includes('diode')) return 4
  return -1
}

// The laser in the SOLIDWORKS GLB consists of several meshes. Therefore, the
// actual name "Laser KY-008-1" may be attached to a parent object.
const getPathNames = (object, scene) => {
  const names = []
  let current = object
  while (current && current !== scene) {
    if (current.name) names.push(current.name)
    current = current.parent
  }
  return names
}

const getKeyIndexFromPath = (names) => {
  for (const name of names) {
    const index = getKeyIndex(name)
    if (index !== -1) return index
  }
  return -1
}

const isRedEmitterMaterial = (material) => {
  const materials = Array.isArray(material) ? material : [material]
  return materials.some((m) =>
    m?.color && m.color.r > 0.8 && m.color.g < 0.25 && m.color.b < 0.25
  )
}

function smoothstep(e0, e1, x) {
  const t = THREE.MathUtils.clamp((x - e0) / (e1 - e0), 0, 1)
  return t * t * (3 - 2 * t)
}

// ---- Thin laser beam that switches on and off as a whole ----
function LaserBeam({ start, end, progress }) {
  const lineRef = useRef()
  const emitterRef = useRef()

  const { mid, quat, len } = useMemo(() => {
    const dir = end.clone().sub(start)
    const len = dir.length()
    const mid = start.clone().add(end).multiplyScalar(0.5)
    const quat = new THREE.Quaternion().setFromUnitVectors(
      new THREE.Vector3(0, 1, 0),
      dir.clone().normalize()
    )
    return { mid, quat, len }
  }, [start, end])

  useFrame((state) => {
    const t = state.clock.getElapsedTime()
    const fade = 1 - smoothstep(0.0, 0.3, progress.current)
    const bitIndex = Math.floor(t * BIT_RATE) % BIT_SEQUENCE.length
    const switchedOn = BIT_SEQUENCE[bitIndex] === '1'
    const opacity = switchedOn ? fade : 0

    if (lineRef.current) {
      lineRef.current.material.opacity = 0.85 * opacity
      lineRef.current.visible = opacity > 0.02
    }

    if (emitterRef.current) {
      emitterRef.current.material.opacity = opacity
      emitterRef.current.visible = opacity > 0.02
    }
  })

  return (
    <group>
      <mesh ref={lineRef} position={mid} quaternion={quat} renderOrder={10}>
        <cylinderGeometry args={[BEAM_RADIUS, BEAM_RADIUS, len, 8]} />
        <meshBasicMaterial
          color={BEAM_COLOR}
          transparent
          opacity={0.85}
          toneMapped={false}
          depthWrite={false}
          depthTest
        />
      </mesh>

      <mesh ref={emitterRef} position={start} renderOrder={11}>
        <sphereGeometry args={[EMITTER_GLOW_RADIUS, 12, 12]} />
        <meshBasicMaterial
          color="#ff2b4a"
          transparent
          opacity={1}
          toneMapped={false}
          depthWrite={false}
          depthTest
        />
      </mesh>
    </group>
  )
}

// ---- A single component ----
function Part({ part, progress, selected, glass, onSelect }) {
  const ref = useRef()
  const tmp = useRef(new THREE.Vector3()).current

  useLayoutEffect(() => {
    ref.current.position.copy(part.base)
    ref.current.quaternion.copy(part.quat)
    ref.current.scale.copy(part.scl)
  }, [part])

  useFrame(() => {
    const p = progress.current

    if (part.role === 'key') {
      const k = smoothstep(KEY_MOVE[0], KEY_MOVE[1], p)
      ref.current.position.copy(tmp.copy(part.base).lerp(part.target, k))
    } else if (part.role === 'aside') {
      const a = smoothstep(ASIDE_MOVE[0], ASIDE_MOVE[1], p)
      ref.current.position.copy(tmp.copy(part.base).lerp(part.target, a))
    } else {
      const m = smoothstep(SCREW_MOVE[0], SCREW_MOVE[1], p)
      ref.current.position.copy(tmp.copy(part.base).lerp(part.target, m))
      const opacity = 1 - smoothstep(SCREW_FADE[0], SCREW_FADE[1], p)
      ref.current.visible = opacity > 0.02
      ref.current.material.opacity = opacity
    }
  })
  const partName = norm(part.name)
  const isRail = partName === 'schiene-1'
  const isDiode = partName.includes('diode')

  return (
    <mesh
      ref={ref}
      geometry={part.geometry}
      onClick={(event) => {
        event.stopPropagation()
        onSelect()
      }}
      onPointerOver={(event) => {
        event.stopPropagation()
        document.body.style.cursor = 'pointer'
      }}
      onPointerOut={() => { document.body.style.cursor = 'auto' }}
    >
      {glass ? (
        <meshPhysicalMaterial
          color="#7fb8c9"
          roughness={0.05}
          metalness={0}
          transmission={0.85}
          thickness={0.4}
          ior={1.5}
          transparent
          opacity={0.6}
        />
      ) : part.fastener ? (
        <meshStandardMaterial
          color="#8c949c"
          roughness={0.22}
          metalness={0.9}
          envMapIntensity={1.2}
          transparent
          opacity={1}
        />
      ) : isRail ? (
        <meshStandardMaterial
          color="#8c949c"
          roughness={0.22}
          metalness={0.9}
          envMapIntensity={1.2}
        />
      ) : isDiode ? (
        <meshStandardMaterial
          color="#d99a35"
          roughness={0.38}
          metalness={0.15}
        />
      ) : (
        <meshStandardMaterial
          color={PART_COLOR}
          roughness={0.6}
          metalness={0.15}
          transparent={part.role === 'fade'}
          opacity={1}
        />
      )}
      {selected && <Outlines thickness={5} color="#3b8ef0" transparent opacity={0.9} />}
    </mesh>
  )
}

export default function Experiment({ selected, exploded, onSelect, onFocusReady }) {
  const { scene } = useGLTF(MODEL_URL)
  const progress = useRef(0)

  useFrame((_, delta) => {
    const target = exploded ? 1 : 0
    const step = delta / EXPLODE_TIME

    if (progress.current < target) {
      progress.current = Math.min(target, progress.current + step)
    } else if (progress.current > target) {
      progress.current = Math.max(target, progress.current - step)
    }
  })

  const { parts, center, scale, beamStart, beamEnd, explosionFocus } = useMemo(() => {
    scene.updateWorldMatrix(true, true)

    const list = []
    const box = new THREE.Box3()
    const corner = new THREE.Vector3()

    scene.traverse((object) => {
      if (!object.isMesh) return

      const pos = new THREE.Vector3()
      const quat = new THREE.Quaternion()
      const scl = new THREE.Vector3()
      object.matrixWorld.decompose(pos, quat, scl)

      const pathNames = getPathNames(object, scene)
      const keyIndex = getKeyIndexFromPath(pathNames)
      const semanticName = pathNames.find((value) => getKeyIndex(value) === keyIndex)
      const fastenerName = pathNames.find(isFastener)
      const name = semanticName || fastenerName || object.name || object.parent?.name || 'unnamed'
      const fastener = Boolean(fastenerName)
      const material = fastener ? object.material.clone() : null
      if (fastener) material.transparent = true

      object.geometry.computeBoundingBox()
      const bb = object.geometry.boundingBox

      const localCenter = bb.getCenter(new THREE.Vector3())
      const visualCenter = localCenter.clone().applyMatrix4(object.matrixWorld)
      const worldBox = new THREE.Box3()

      for (let xi = 0; xi < 2; xi++) {
        for (let yi = 0; yi < 2; yi++) {
          for (let zi = 0; zi < 2; zi++) {
            corner.set(
              xi ? bb.max.x : bb.min.x,
              yi ? bb.max.y : bb.min.y,
              zi ? bb.max.z : bb.min.z
            )
            corner.applyMatrix4(object.matrixWorld)
            box.expandByPoint(corner)
            worldBox.expandByPoint(corner)
          }
        }
      }

      list.push({
        id: object.uuid,
        name,
        geometry: object.geometry,
        material,
        base: pos.clone(),
        center: visualCenter,
        worldBox,
        quat,
        scl,
        fastener,
        keyIndex,
        redEmitter: keyIndex === 0 && isRedEmitterMaterial(object.material)
      })
    })

    const sphere = new THREE.Sphere()
    box.getBoundingSphere(sphere)
    const cen = sphere.center.clone()
    const rad = sphere.radius || 1

    // Related submeshes, especially the seven laser meshes, are treated as one
    // component so that their relative positions remain unchanged.
    const componentBoxes = KEY_ORDER.map(() => new THREE.Box3())
    list.forEach((part) => {
      if (part.keyIndex !== -1) componentBoxes[part.keyIndex].union(part.worldBox)
    })

    const componentCenters = componentBoxes.map((componentBox) =>
      componentBox.isEmpty() ? null : componentBox.getCenter(new THREE.Vector3())
    )

    const averageBase = (index) => {
      const matching = list.filter((part) => part.keyIndex === index)
      if (!matching.length) return componentCenters[index]
      const result = new THREE.Vector3()
      matching.forEach((part) => result.add(part.base))
      return result.divideScalar(matching.length)
    }

    // Physical reference axes of this model:
    // The lens barrel, lens, and receiver tube use their SOLIDWORKS origins.
    // The photodiode uses its visible body center because its GLB origin is
    // offset from the optical axis by approximately 2.5 mm.
    const componentAnchors = [...componentCenters]
    componentAnchors[1] = averageBase(1)
    componentAnchors[2] = averageBase(2)
    componentAnchors[3] = averageBase(3)

    // The red emitter element of the KY-008 defines the actual laser axis.
    const redEmitterBox = new THREE.Box3()
    list
      .filter((part) => part.redEmitter)
      .forEach((part) => redEmitterBox.union(part.worldBox))
    if (!redEmitterBox.isEmpty()) {
      componentAnchors[0] = redEmitterBox.getCenter(new THREE.Vector3())
    }

    // The lens defines the shared optical x-axis.
    const axisCenter = componentAnchors[2]?.clone() || cen.clone()

    const receiverX = componentAnchors
      .slice(1)
      .filter(Boolean)
      .map((anchor) => anchor.x)
    const receiverSpread = receiverX.length
      ? Math.max(...receiverX) - Math.min(...receiverX)
      : rad * 0.3
    const unit = Math.max(receiverSpread / 1.5, rad * 0.12)

    // Transmitter center used to separate the transmitter and receiver sides.
    const senderParts = list.filter((part) =>
      /laser|wippe|sender|schiene/.test(norm(part.name))
    )
    const senderCenter = new THREE.Vector3()
    senderParts.forEach((part) => senderCenter.add(part.base))
    if (senderParts.length) senderCenter.divideScalar(senderParts.length)

    const splitX = senderParts.length
      ? (axisCenter.x + senderCenter.x) / 2
      : axisCenter.x
    const isReceiverSide = (part) => part.base.x > splitX

    // 1) Place the laser and the core optical components on one visible axis.
    // Move all other printed parts aside or downward.
    list.forEach((part) => {
      const keyIndex = part.keyIndex

      if (keyIndex !== -1) {
        part.role = 'key'
        const slot = keyIndex - (KEY_ORDER.length - 1) / 2
        const desiredAnchor = axisCenter.clone().add(
          ROW_AXIS.clone().multiplyScalar(slot * ROW_SPACING * unit)
        )
        if (keyIndex === 4) {
          desiredAnchor.addScaledVector(ROW_AXIS, DIODE_EXTRA_OUT * unit)
        }
        const sourceAnchor = componentAnchors[keyIndex] || part.center
        const componentShift = desiredAnchor.sub(sourceAnchor)
        part.target = part.base.clone().add(componentShift)
      } else if (!part.fastener) {
        const partName = norm(part.name)
        const rearCover = partName.includes('kleiner deckel') ||
          partName.includes('rückdeckel') || partName.includes('rueckdeckel')

        if (rearCover) {
          part.role = 'fade'
          part.target = part.base.clone().addScaledVector(ROW_AXIS, 1.2 * unit)
        } else {
          part.role = 'aside'
          part.target = part.base.clone().add(new THREE.Vector3(0, -ASIDE_DROP * unit, 0))
        }
      }
    })

    // 2) Screws and bolts
    const drivers = []
    list.forEach((part) => {
      if (!part.fastener) return

      const n = norm(part.name)
      if (n.startsWith('hex nut')) return

      let axis
      if (n.startsWith('hex screw')) axis = 'y'
      else axis = VERTICAL_FASTENERS.some((value) => n.startsWith(value)) ? 'y' : 'x'

      const component = axis === 'y' ? part.base.y - cen.y : part.base.x - cen.x
      const sign = component >= 0 ? 1 : -1
      const axisDir = axis === 'y'
        ? new THREE.Vector3(0, sign, 0)
        : new THREE.Vector3(sign, 0, 0)

      if (isReceiverSide(part)) axisDir.negate()

      part.axisDir = axisDir
      const amount = n.startsWith('hex screw') ? SCREW_OUT : BOLT_OUT
      part.role = 'fastener'
      part.target = part.base.clone().add(axisDir.clone().multiplyScalar(amount * unit))
      drivers.push(part)
    })

    // 3) Nuts move in the opposite direction to their nearest screw or bolt.
    list.forEach((part) => {
      if (!part.fastener) return

      const n = norm(part.name)
      if (!n.startsWith('hex nut')) return

      part.role = 'fastener'
      let nearest = null
      let best = Infinity

      drivers.forEach((driver) => {
        const distance = driver.base.distanceTo(part.base)
        if (distance < best) {
          best = distance
          nearest = driver
        }
      })

      const direction = nearest
        ? nearest.axisDir.clone().multiplyScalar(-1)
        : new THREE.Vector3(0, -1, 0)

      part.target = part.base.clone().add(direction.multiplyScalar(NUT_OUT * unit))
    })

    // Beam from the front of the red KY-008 emitter to the front of the lens.
    // These points are derived from the actual GLB geometry.
    let bStart = null
    let bEnd = null
    if (componentAnchors[0] && componentAnchors[2]) {
      bStart = componentAnchors[0].clone()
      bStart.x = redEmitterBox.isEmpty()
        ? componentBoxes[0].max.x
        : redEmitterBox.max.x

      bEnd = componentAnchors[2].clone()
      bEnd.x = componentBoxes[2].min.x
    }

    const worldScale = MODEL_FIT / rad
    const focusTarget = axisCenter.clone().sub(cen).multiplyScalar(worldScale)
    const explodedRowWidth = unit * (KEY_ORDER.length - 1 + DIODE_EXTRA_OUT) * worldScale

    return {
      parts: list,
      center: cen,
      scale: worldScale,
      beamStart: bStart,
      beamEnd: bEnd,
      explosionFocus: {
        target: focusTarget.toArray(),
        distance: Math.max(2.2, explodedRowWidth * 1.45)
      }
    }
  }, [scene])

  useEffect(() => {
    onFocusReady?.(explosionFocus)
  }, [explosionFocus, onFocusReady])

  return (
    <group scale={scale}>
      <group position={[-center.x, -center.y, -center.z]}>
        {parts.map((part) => (
          <Part
            key={part.id}
            part={part}
            progress={progress}
            selected={part.fastener ? selected === 'fasteners' : selected === part.name}
            glass={getInfo(part.name)?.material === 'glass'}
            onSelect={() => onSelect(part.fastener ? 'fasteners' : part.name)}
          />
        ))}

        {beamStart && beamEnd && (
          <LaserBeam start={beamStart} end={beamEnd} progress={progress} />
        )}
      </group>
    </group>
  )
}
