import { Hand } from 'lucide-react';
import type { SystemStatus } from '../../api';

const MODE_LABELS: Record<number, string> = {
  0: 'STANDBY',
  1: 'VIRTUAL MOUSE',
  2: 'FACIAL CONTROL',
  3: 'AIR SIGNATURE',
};

interface DashboardHeaderProps {
  systemStatus: SystemStatus;
  currentMode: number | null;
}

export function DashboardHeader({ systemStatus, currentMode }: DashboardHeaderProps) {
  const statusConfig = {
    stopped: {
      dot: 'bg-red-500 shadow-[0_0_8px_#ef4444]',
      label: 'OFFLINE',
      labelClass: 'text-red-400',
      pulse: false,
    },
    starting: {
      dot: 'bg-yellow-400 shadow-[0_0_8px_#facc15]',
      label: 'STARTING',
      labelClass: 'text-yellow-400',
      pulse: true,
    },
    running: {
      dot: 'bg-green-400 shadow-[0_0_8px_#4ade80]',
      label: 'ONLINE',
      labelClass: 'text-green-400',
      pulse: true,
    },
  }[systemStatus];

  const modeLabel =
    currentMode !== null && currentMode !== undefined
      ? (MODE_LABELS[currentMode] ?? 'UNKNOWN')
      : '—';

  return (
    <div className="flex flex-wrap justify-start items-center gap-8">
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 bg-white rounded-full flex items-center justify-center text-black shadow-[0_0_15px_rgba(255,255,255,0.3)]">
          <Hand className="w-6 h-6" />
        </div>
        <div>
          <h2 className="text-3xl font-black tracking-tighter uppercase text-white">AeroMouse</h2>
          <p className="text-[10px] font-mono text-gray-400 tracking-widest uppercase">
            Multi-Modal Touchless HCI System
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2 bg-white/10 border border-white/20 px-4 py-2 rounded-full text-[10px] font-mono tracking-widest">
        <div
          className={`w-2 h-2 rounded-full ${statusConfig.dot} ${statusConfig.pulse ? 'animate-pulse' : ''}`}
        />
        <span className={statusConfig.labelClass}>{statusConfig.label}</span>
        <span className="text-gray-500">•</span>
        <span className="text-white font-bold">{modeLabel}</span>
      </div>
    </div>
  );
}
