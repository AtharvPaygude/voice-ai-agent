import React, { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { useCallStore } from '../../stores/callStore';
import type { OrbState } from '../../types';

// State color schemes
const STATE_COLORS: Record<OrbState, { primary: string; secondary: string; glow: string; speed: number; roughness: number }> = {
  idle: { primary: '#00dbe9', secondary: '#191f2f', glow: '#00f0ff', speed: 0.6, roughness: 0.3 },
  listening: { primary: '#00f0ff', secondary: '#006970', glow: '#7df4ff', speed: 1.6, roughness: 0.15 },
  thinking: { primary: '#8b5cf6', secondary: '#571bc1', glow: '#c4abff', speed: 2.8, roughness: 0.4 },
  speaking: { primary: '#00f0ff', secondary: '#c4abff', glow: '#6ffbbe', speed: 2.2, roughness: 0.2 },
  interrupted: { primary: '#f43f5e', secondary: '#881337', glow: '#fda4af', speed: 4.5, roughness: 0.1 },
  language_switch: { primary: '#6ffbbe', secondary: '#00f0ff', glow: '#d0bcff', speed: 3.5, roughness: 0.5 },
  tool_action: { primary: '#f59e0b', secondary: '#93000a', glow: '#fde68a', speed: 2.0, roughness: 0.25 },
  success: { primary: '#10b981', secondary: '#003824', glow: '#6ffbbe', speed: 1.4, roughness: 0.2 },
  error: { primary: '#ef4444', secondary: '#690005', glow: '#ffdad6', speed: 1.2, roughness: 0.6 },
  human_transfer: { primary: '#e9ddff', secondary: '#5516be', glow: '#ffffff', speed: 0.9, roughness: 0.3 },
};

const AnimatedSphere: React.FC<{ orbState: OrbState; audioLevel: number }> = ({ orbState, audioLevel }) => {
  const meshRef = useRef<THREE.Mesh>(null);
  const ringRef1 = useRef<THREE.Mesh>(null);
  const ringRef2 = useRef<THREE.Mesh>(null);
  const ringRef3 = useRef<THREE.Mesh>(null);

  const config = STATE_COLORS[orbState] || STATE_COLORS.idle;
  const primaryColor = useMemo(() => new THREE.Color(config.primary), [config.primary]);
  const secondaryColor = useMemo(() => new THREE.Color(config.secondary), [config.secondary]);

  useFrame((state, delta) => {
    const time = state.clock.getElapsedTime();
    const effectiveSpeed = config.speed;

    if (meshRef.current) {
      meshRef.current.rotation.y += delta * 0.4 * effectiveSpeed;
      meshRef.current.rotation.x += delta * 0.2 * effectiveSpeed;

      // Audio-reactive scale breathing
      const baseScale = 1.35 + Math.sin(time * 2.0 * effectiveSpeed) * 0.05;
      const reactiveScale = baseScale + (orbState === 'speaking' || orbState === 'listening' ? audioLevel * 0.35 : 0);
      meshRef.current.scale.set(reactiveScale, reactiveScale, reactiveScale);
    }

    if (ringRef1.current) {
      ringRef1.current.rotation.z += delta * 0.8 * effectiveSpeed;
      ringRef1.current.rotation.x += delta * 0.3 * effectiveSpeed;
    }
    if (ringRef2.current) {
      ringRef2.current.rotation.y -= delta * 0.7 * effectiveSpeed;
      ringRef2.current.rotation.z += delta * 0.4 * effectiveSpeed;
    }
    if (ringRef3.current) {
      ringRef3.current.rotation.x -= delta * 0.6 * effectiveSpeed;
      ringRef3.current.rotation.y += delta * 0.5 * effectiveSpeed;
    }
  });

  return (
    <group>
      {/* Central Core Mesh */}
      <mesh ref={meshRef}>
        <sphereGeometry args={[1, 64, 64]} />
        <meshPhysicalMaterial
          color={primaryColor}
          emissive={secondaryColor}
          emissiveIntensity={0.6}
          roughness={config.roughness}
          metalness={0.8}
          clearcoat={1.0}
          clearcoatRoughness={0.1}
          wireframe={orbState === 'thinking' || orbState === 'tool_action'}
          transparent
          opacity={0.92}
        />
      </mesh>

      {/* Orbital Glowing Signal Rings */}
      <mesh ref={ringRef1}>
        <torusGeometry args={[1.75, 0.018, 16, 100]} />
        <meshStandardMaterial
          color={primaryColor}
          emissive={primaryColor}
          emissiveIntensity={1.2}
          transparent
          opacity={0.7}
        />
      </mesh>

      <mesh ref={ringRef2}>
        <torusGeometry args={[2.05, 0.012, 16, 100]} />
        <meshStandardMaterial
          color={secondaryColor}
          emissive={primaryColor}
          emissiveIntensity={0.9}
          transparent
          opacity={0.5}
        />
      </mesh>

      <mesh ref={ringRef3}>
        <torusGeometry args={[2.3, 0.008, 16, 100]} />
        <meshStandardMaterial
          color={primaryColor}
          emissive={primaryColor}
          emissiveIntensity={0.6}
          transparent
          opacity={0.35}
        />
      </mesh>
    </group>
  );
};

const ParticleField: React.FC<{ orbState: OrbState }> = ({ orbState }) => {
  const count = 120;
  const pointsRef = useRef<THREE.Points>(null);

  const particles = useMemo(() => {
    const positions = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      const radius = 2.0 + Math.random() * 2.5;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(Math.random() * 2 - 1);

      positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
      positions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
      positions[i * 3 + 2] = radius * Math.cos(phi);
    }
    return positions;
  }, []);

  useFrame((_, delta) => {
    if (pointsRef.current) {
      const speed = STATE_COLORS[orbState]?.speed || 1.0;
      pointsRef.current.rotation.y += delta * 0.15 * speed;
      pointsRef.current.rotation.x += delta * 0.05 * speed;
    }
  });

  return (
    <points ref={pointsRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          args={[particles, 3]}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.045}
        color={STATE_COLORS[orbState]?.glow || '#00f0ff'}
        transparent
        opacity={0.75}
        blending={THREE.AdditiveBlending}
      />
    </points>
  );
};

export const AiOrb: React.FC = () => {
  const orbState = useCallStore((state) => state.orbState);
  const audioLevel = useCallStore((state) => state.audioLevel);

  return (
    <div className="w-full h-full min-h-[320px] flex items-center justify-center relative">
      {/* Background Soft Glow Aura */}
      <div 
        className="absolute w-72 h-72 rounded-full blur-3xl opacity-30 transition-all duration-700 pointer-events-none"
        style={{
          backgroundColor: STATE_COLORS[orbState]?.glow || '#00f0ff',
          transform: `scale(${orbState === 'speaking' ? 1.3 : 1})`,
        }}
      />

      {/* 3D WebGL Canvas */}
      <Canvas
        camera={{ position: [0, 0, 5.2], fov: 45 }}
        style={{ background: 'transparent' }}
      >
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} intensity={1.5} color="#00f0ff" />
        <pointLight position={[-10, -10, -10]} intensity={1.2} color="#571bc1" />
        <pointLight position={[0, 5, 0]} intensity={0.8} color="#65f2b5" />

        <AnimatedSphere orbState={orbState} audioLevel={audioLevel} />
        <ParticleField orbState={orbState} />
      </Canvas>
    </div>
  );
};
