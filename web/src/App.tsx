import { useState } from 'react';
import { Canvas } from '@react-three/fiber';
import Scene from './components/3d/Scene';
import { Hero } from './components/layout/Hero';
import { BrutalistCard } from './components/ui/BrutalistCard';
import { MousePointer2, Smile, PenTool, ArrowDown } from 'lucide-react';

export default function App() {
  const scrollToFeatures = () => {
    window.scrollTo({ top: window.innerHeight, behavior: 'smooth' });
  };

  return (
    <div className="w-full min-h-screen font-sans text-white bg-[#03000a]">
      {/* FIXED 3D BACKGROUND */}
      <div className="fixed inset-0 z-0">
        <Canvas camera={{ position: [0, 0, 15], fov: 45 }}>
          <Scene />
        </Canvas>
      </div>

      {/* SCROLLABLE CONTENT */}
      <div className="relative z-10 w-full pointer-events-none mb-12">
        <Hero onDiscoverClick={scrollToFeatures} />

        {/* FEATURES SECTION (Showcase) */}
        <section className="w-full min-h-screen bg-transparent pt-8 pb-20 px-8 md:px-12 pointer-events-auto flex flex-col justify-center">
          <div className="mb-12">
            <h3 className="text-[10px] font-mono text-[#a855f7] tracking-widest uppercase mb-2">
              Capabilities
            </h3>
            <h4 className="text-3xl font-bold mb-4">Multi-Modal Control</h4>
            <p className="text-gray-400 max-w-2xl text-sm leading-relaxed">
              Aero-Mouse completely reimagines human-computer interaction by utilizing
              advanced machine learning models running locally on your hardware. 
              No dedicated sensors required — just your standard webcam.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <BrutalistCard
              title="Virtual Mouse"
              description="Control your cursor using hand gestures. Point, click, drag, and scroll — all touchless. Uses MediaPipe Hands for high-precision joint tracking."
              icon={<MousePointer2 className="w-6 h-6" />}
              tags={['☝️ Point/Move', '✌️ Left Click', '✊ Drag & Drop', '🖐️ Scroll']}
            />
            <BrutalistCard
              title="Facial Control"
              description="Use head movements to scroll and navigate. Tilt down to scroll down, tilt up to scroll up. Perfect for reading long documents hands-free."
              icon={<Smile className="w-6 h-6" />}
              tags={['⬆️ Scroll Up', '⬇️ Scroll Down', '🟢 Hands-free', '🖥️ Presentation']}
            />
            <BrutalistCard
              title="Air Signature"
              description="Draw your signature in the air to authenticate. Utilizes dynamic time warping algorithm to match spatial-temporal trajectory data."
              icon={<PenTool className="w-6 h-6" />}
              tags={['✍️ Air Draw', '🔒 DTW Auth', '☁️ Cloud Sync', '⚡ Biometric']}
            />
          </div>

          <div className="mt-24 border-t border-white/20 pt-12 flex flex-col md:flex-row justify-between items-center gap-8">
            <div>
              <h2 className="text-2xl font-black uppercase tracking-tight mb-2">Built for Performance</h2>
              <p className="text-sm text-gray-400 font-mono">React 19 • Vite • Three.js • Python Flask • OpenCV • MediaPipe • PostgreSQL</p>
            </div>
            
            <a 
              href="https://github.com/omhajare/aeromouse"
              target="_blank" 
              rel="noopener noreferrer"
              className="px-6 py-3 border border-white/30 hover:border-white hover:bg-white/10 transition-all font-mono text-sm tracking-wider uppercase font-bold"
            >
              View on GitHub
            </a>
          </div>
        </section>
      </div>
    </div>
  );
}
