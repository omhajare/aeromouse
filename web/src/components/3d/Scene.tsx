import { useRef, useMemo } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { Float, Stars, MeshTransmissionMaterial, Environment } from '@react-three/drei';
import * as THREE from 'three';

function CentralOrb() {
  return (
    <Float speed={2} rotationIntensity={0.5} floatIntensity={2}>
      <mesh>
        <sphereGeometry args={[2.5, 64, 64]} />
        <MeshTransmissionMaterial 
          backside
          samples={4}
          thickness={2}
          chromaticAberration={0.05}
          anisotropy={0.1}
          distortion={0.8}
          distortionScale={0.5}
          temporalDistortion={0.2}
          color="#c084fc"
          emissive="#7e22ce"
          emissiveIntensity={0.2}
        />
        <pointLight color="#d8b4fe" intensity={20} distance={20} />
      </mesh>
    </Float>
  );
}

function OrbitRing({ radius, tiltX, tiltY, speed, sphereCount, color }: { radius: number, tiltX: number, tiltY: number, speed: number, sphereCount: number, color: string }) {
  const groupRef = useRef<THREE.Group>(null);
  const spheresRef = useRef<(THREE.Mesh | null)[]>([]);
  const { camera } = useThree();

  const spheres = useMemo(() => {
    return Array.from({ length: sphereCount }).map((_, i) => ({
      angle: (i / sphereCount) * Math.PI * 2,
      speedOffset: Math.random() * 0.5 + 0.5,
      size: Math.random() * 0.08 + 0.04,
    }));
  }, [sphereCount]);

  useFrame((state) => {
    const time = state.clock.getElapsedTime();
    
    if (groupRef.current) {
      // Subtle wobble for the whole ring
      groupRef.current.rotation.x = tiltX + Math.sin(time * 0.2) * 0.05;
      groupRef.current.rotation.y = tiltY + Math.cos(time * 0.2) * 0.05;
    }

    // Calculate mouse 3D position on a plane slightly in front of the camera
    const vec = new THREE.Vector3(state.pointer.x, state.pointer.y, 0.5);
    vec.unproject(camera);
    vec.sub(camera.position).normalize();
    const distance = -camera.position.z / vec.z;
    const mousePos = new THREE.Vector3().copy(camera.position).add(vec.multiplyScalar(distance));

    spheresRef.current.forEach((sphereMesh, i) => {
      if (!sphereMesh) return;
      const s = spheres[i];
      const currentAngle = s.angle + time * speed * s.speedOffset;
      
      // Base position on the ring (local space)
      let localX = Math.cos(currentAngle) * radius;
      let localY = Math.sin(currentAngle) * radius;
      let localZ = 0;

      // Convert local to world to check distance to mouse
      const worldPos = new THREE.Vector3(localX, localY, localZ);
      if (groupRef.current) {
        worldPos.applyMatrix4(groupRef.current.matrixWorld);
      }

      const dist = mousePos.distanceTo(worldPos);
      const repelRadius = 6.0;
      
      if (dist < repelRadius) {
        const repelForce = Math.pow((repelRadius - dist) / repelRadius, 2) * 5.0;
        const repelDir = worldPos.clone().sub(mousePos).normalize();
        
        // Push away from mouse in world space
        worldPos.add(repelDir.multiplyScalar(repelForce));
        
        // Convert back to local space
        if (groupRef.current) {
          const invMatrix = new THREE.Matrix4().copy(groupRef.current.matrixWorld).invert();
          worldPos.applyMatrix4(invMatrix);
        }
        
        localX = worldPos.x;
        localY = worldPos.y;
        localZ = worldPos.z;
      }

      // Smoothly interpolate to target position
      sphereMesh.position.lerp(new THREE.Vector3(localX, localY, localZ), 0.1);
    });
  });

  return (
    <group ref={groupRef}>
      {/* The visible ring */}
      <mesh rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[radius, 0.01, 32, 100]} />
        <meshBasicMaterial color={color} transparent opacity={0.3} />
      </mesh>
      
      {/* The orbiting spheres */}
      {spheres.map((s, i) => (
        <mesh key={i} ref={(el) => (spheresRef.current[i] = el)}>
          <sphereGeometry args={[s.size, 32, 32]} />
          <meshStandardMaterial color="#ffffff" emissive="#ffffff" emissiveIntensity={1.5} />
        </mesh>
      ))}
    </group>
  );
}

export default function Scene() {
  const groupRef = useRef<THREE.Group>(null);

  useFrame((state) => {
    // Parallax effect for the whole scene based on mouse
    if (groupRef.current) {
      groupRef.current.rotation.y = THREE.MathUtils.lerp(groupRef.current.rotation.y, (state.pointer.x * Math.PI) / 4, 0.1);
      groupRef.current.rotation.x = THREE.MathUtils.lerp(groupRef.current.rotation.x, (-state.pointer.y * Math.PI) / 4, 0.1);
    }
  });

  return (
    <>
      <color attach="background" args={['#03000a']} />
      <ambientLight intensity={0.2} />
      <Environment preset="city" />
      <Stars radius={100} depth={50} count={5000} factor={4} saturation={0} fade speed={1} />
      
      <group ref={groupRef}>
        <CentralOrb />
        
        <OrbitRing radius={4} tiltX={0.2} tiltY={0.5} speed={0.5} sphereCount={8} color="#c084fc" />
        <OrbitRing radius={5.5} tiltX={-0.3} tiltY={0.2} speed={0.3} sphereCount={12} color="#e879f9" />
        <OrbitRing radius={7} tiltX={0.5} tiltY={-0.4} speed={0.2} sphereCount={15} color="#a855f7" />
        <OrbitRing radius={8.5} tiltX={-0.1} tiltY={0.6} speed={0.4} sphereCount={10} color="#d8b4fe" />
        <OrbitRing radius={10} tiltX={0.3} tiltY={-0.2} speed={0.15} sphereCount={20} color="#c084fc" />
      </group>
    </>
  );
}
