/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState, useEffect, useCallback } from 'react';
import { Canvas } from '@react-three/fiber';
import Scene from './components/3d/Scene';
import { Zap, Lock, Folder } from 'lucide-react';
import { SignatureAuth } from './components/auth/SignatureAuth';
import { Hero } from './components/layout/Hero';
import { DashboardHeader } from './components/dashboard/DashboardHeader';
import { SystemControl } from './components/dashboard/SystemControl';
import { SavedSignatures } from './components/dashboard/SavedSignatures';
import { OfflineBanner } from './components/ui/OfflineBanner';
import { getStatus } from './api';
import type { SystemStatus } from './api';

const POLL_INTERVAL_MS = 2000;

export default function App() {
  const [activeTab, setActiveTab] = useState('system_control');

  // ── Shared system state (lifted up, passed to children) ──
  const [systemStatus, setSystemStatus] = useState<SystemStatus>('stopped');
  const [currentMode, setCurrentMode] = useState<number | null>(null);

  // ── Status polling ────────────────────────────────────────
  const pollStatus = useCallback(async () => {
    try {
      const res = await getStatus();
      setSystemStatus(res.status);
      setCurrentMode(res.mode ?? null);
    } catch {
      // Backend unreachable — mark as stopped
      setSystemStatus('stopped');
      setCurrentMode(null);
    }
  }, []);

  useEffect(() => {
    // Initial fetch on mount
    pollStatus();

    // Keep polling while app is open
    const interval = setInterval(pollStatus, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [pollStatus]);

  const scrollToDashboard = () => {
    window.scrollTo({ top: window.innerHeight, behavior: 'smooth' });
  };

  return (
    <div className="w-full min-h-screen font-sans text-white bg-[#03000a]">
      {/* OFFLINE / DEGRADED SERVICE BANNER */}
      <OfflineBanner />

      {/* FIXED 3D BACKGROUND */}
      <div className="fixed inset-0 z-0">
        <Canvas camera={{ position: [0, 0, 15], fov: 45 }}>
          <Scene />
        </Canvas>
      </div>

      {/* SCROLLABLE CONTENT */}
      <div className="relative z-10 w-full pointer-events-none">

        <Hero onDiscoverClick={scrollToDashboard} />

        {/* DASHBOARD SECTION */}
        <section className="w-full min-h-screen bg-transparent pt-8 pb-20 px-8 md:px-12 pointer-events-auto">
          <div className="w-full flex flex-col gap-12">

            {/* Live status header */}
            <DashboardHeader systemStatus={systemStatus} currentMode={currentMode} />

            {/* Tabs */}
            <div className="flex flex-wrap gap-8 border-b border-white/20">
              <button
                onClick={() => setActiveTab('system_control')}
                className={`flex items-center gap-2 pb-4 border-b-2 font-bold uppercase tracking-wider text-xs transition-colors ${
                  activeTab === 'system_control'
                    ? 'border-[#a855f7] text-[#a855f7]'
                    : 'border-transparent text-gray-400 hover:text-white'
                }`}
              >
                <Zap className="w-4 h-4" /> System Control
              </button>
              <button
                onClick={() => setActiveTab('signature_auth')}
                className={`flex items-center gap-2 pb-4 border-b-2 font-bold uppercase tracking-wider text-xs transition-colors ${
                  activeTab === 'signature_auth'
                    ? 'border-[#a855f7] text-[#a855f7]'
                    : 'border-transparent text-gray-400 hover:text-white'
                }`}
              >
                <Lock className="w-4 h-4" /> Signature Auth
              </button>
              <button
                onClick={() => setActiveTab('saved_signatures')}
                className={`flex items-center gap-2 pb-4 border-b-2 font-bold uppercase tracking-wider text-xs transition-colors ${
                  activeTab === 'saved_signatures'
                    ? 'border-[#a855f7] text-[#a855f7]'
                    : 'border-transparent text-gray-400 hover:text-white'
                }`}
              >
                <Folder className="w-4 h-4" /> Saved Signatures
              </button>
            </div>

            {/* Tab Content */}
            {activeTab === 'system_control' && (
              <SystemControl
                systemStatus={systemStatus}
                currentMode={currentMode}
                onStatusChange={setSystemStatus}
                onModeChange={setCurrentMode}
              />
            )}

            {activeTab === 'signature_auth' && <SignatureAuth currentMode={currentMode} />}

            {activeTab === 'saved_signatures' && <SavedSignatures />}

          </div>
        </section>
      </div>
    </div>
  );
}
