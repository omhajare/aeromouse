import { useState } from 'react';
import { Play, Square, MousePointer2, Smile, PenTool, Loader2, AlertCircle, CheckCircle } from 'lucide-react';
import { BrutalistCard } from '../ui/BrutalistCard';
import { startSystem, stopSystem, setMode } from '../../api';
import type { SystemStatus } from '../../api';

interface SystemControlProps {
  systemStatus: SystemStatus;
  currentMode: number | null;
  onStatusChange: (status: SystemStatus) => void;
  onModeChange: (mode: number | null) => void;
}

interface Toast {
  type: 'success' | 'error';
  message: string;
}

export function SystemControl({
  systemStatus,
  currentMode,
  onStatusChange,
  onModeChange,
}: SystemControlProps) {
  const [isStarting, setIsStarting] = useState(false);
  const [isStopping, setIsStopping] = useState(false);
  const [switchingMode, setSwitchingMode] = useState<number | null>(null);
  const [toast, setToast] = useState<Toast | null>(null);

  const showToast = (type: Toast['type'], message: string) => {
    setToast({ type, message });
    setTimeout(() => setToast(null), 3500);
  };

  const handleStart = async () => {
    setIsStarting(true);
    try {
      await startSystem();
      onStatusChange('starting');
      showToast('success', 'System is warming up…');
    } catch (err) {
      showToast('error', err instanceof Error ? err.message : 'Failed to start system');
    } finally {
      setIsStarting(false);
    }
  };

  const handleStop = async () => {
    setIsStopping(true);
    try {
      await stopSystem();
      onStatusChange('stopped');
      onModeChange(null);
      showToast('success', 'System stopped successfully');
    } catch (err) {
      showToast('error', err instanceof Error ? err.message : 'Failed to stop system');
    } finally {
      setIsStopping(false);
    }
  };

  const handleModeSwitch = async (mode: 1 | 2 | 3) => {
    if (systemStatus !== 'running') {
      showToast('error', 'System must be running to switch modes');
      return;
    }

    // Toggle logic: if clicking the active mode, switch to 0 (Standby)
    const targetMode = mode === currentMode ? 0 : mode;
    setSwitchingMode(mode);
    try {
      await setMode(targetMode);
      onModeChange(targetMode);
      const modeNames: Record<number, string> = {
        0: 'Standby / Deactivated',
        1: 'Virtual Mouse',
        2: 'Facial Control',
        3: 'Air Signature',
      };
      showToast('success', targetMode === 0 ? 'Mode Deactivated' : `Switched to ${modeNames[targetMode]}`);
    } catch (err) {
      showToast('error', err instanceof Error ? err.message : 'Failed to switch mode');
    } finally {
      setSwitchingMode(null);
    }
  };

  const isRunning = systemStatus === 'running';
  const isSystemBusy = isStarting || isStopping || systemStatus === 'starting';

  return (
    <div className="flex flex-col gap-12 animate-in fade-in duration-500">

      {/* Toast notification */}
      {toast && (
        <div
          className={`fixed top-6 right-6 z-50 flex items-center gap-3 px-5 py-3 border-2 font-mono text-sm font-bold shadow-[4px_4px_0_rgba(0,0,0,0.5)] animate-in slide-in-from-right duration-300
            ${toast.type === 'success'
              ? 'bg-black border-green-400 text-green-400'
              : 'bg-black border-red-500 text-red-400'
            }`}
        >
          {toast.type === 'success'
            ? <CheckCircle className="w-4 h-4 shrink-0" />
            : <AlertCircle className="w-4 h-4 shrink-0" />
          }
          {toast.message}
        </div>
      )}

      {/* Power Management */}
      <div className="bg-black/50 p-8 rounded-2xl border border-white/20 shadow-[8px_8px_0_rgba(255,255,255,0.1)]">
        <div className="flex justify-between items-end mb-6">
          <div>
            <h3 className="text-[10px] font-mono text-[#a855f7] tracking-widest uppercase mb-2">
              System Control
            </h3>
            <h4 className="text-2xl font-bold">Power Management</h4>
          </div>
          <div className="hidden sm:flex gap-6 text-[10px] font-mono text-gray-400">
            <div className="flex flex-col gap-2">
              <span>STATUS</span>
              <div
                className={`text-xs font-black uppercase px-3 py-1 border-2 ${systemStatus === 'running'
                    ? 'border-green-400 text-green-400'
                    : systemStatus === 'starting'
                      ? 'border-yellow-400 text-yellow-400'
                      : 'border-gray-600 text-gray-600'
                  }`}
              >
                {systemStatus.toUpperCase()}
              </div>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap gap-6">
          {/* Initialize button */}
          <button
            onClick={handleStart}
            disabled={isSystemBusy || isRunning}
            className="flex-1 min-w-[200px] bg-[#a855f7] text-white border-4 border-white shadow-[4px_4px_0_#fff] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0_#fff] active:translate-x-[4px] active:translate-y-[4px] active:shadow-none transition-all px-6 py-4 flex items-center gap-4 font-black uppercase disabled:opacity-40 disabled:cursor-not-allowed disabled:transform-none disabled:shadow-none"
          >
            {isStarting || systemStatus === 'starting' ? (
              <Loader2 className="w-8 h-8 animate-spin" />
            ) : (
              <Play className="w-8 h-8" />
            )}
            <div className="text-left">
              <div className="text-lg">
                {systemStatus === 'starting' ? 'Starting...' : 'Initialize'}
              </div>
              <div className="text-[10px] font-bold opacity-70">Start System</div>
            </div>
          </button>

          {/* Terminate button */}
          <button
            onClick={handleStop}
            disabled={isSystemBusy || !isRunning}
            className="flex-1 min-w-[200px] bg-red-600 text-white border-4 border-white shadow-[4px_4px_0_#fff] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0_#fff] active:translate-x-[4px] active:translate-y-[4px] active:shadow-none transition-all px-6 py-4 flex items-center gap-4 font-black uppercase disabled:opacity-40 disabled:cursor-not-allowed disabled:transform-none disabled:shadow-none"
          >
            {isStopping ? (
              <Loader2 className="w-8 h-8 animate-spin" />
            ) : (
              <Square className="w-8 h-8 fill-current" />
            )}
            <div className="text-left">
              <div className="text-lg">{isStopping ? 'Stopping...' : 'Terminate'}</div>
              <div className="text-[10px] font-bold text-red-200">Stop System</div>
            </div>
          </button>
        </div>

        {!isRunning && systemStatus !== 'starting' && (
          <p className="mt-4 text-xs font-mono text-gray-500 italic">
            ↑ Initialize the system before activating a mode
          </p>
        )}
      </div>

      {/* Control Modes */}
      <div className="mt-4">
        <h3 className="text-[10px] font-mono text-[#a855f7] tracking-widest uppercase mb-2">
          Interaction Modes
        </h3>
        <h4 className="text-2xl font-bold mb-2">Select Control Mode</h4>
        <p className="text-sm text-gray-400 mb-8">
          System must be running to activate a mode
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          <BrutalistCard
            title="Virtual Mouse"
            description="Control your cursor using hand gestures. Point, click, drag, and scroll — all touchless."
            icon={<MousePointer2 className="w-6 h-6" />}
            tags={['☝️ Move', '✌️ Click', '✊ Drag', '🖐️ Scroll']}
            isActive={isRunning && currentMode === 1}
            isLoading={switchingMode === 1}
            disabled={!isRunning || (switchingMode !== null && switchingMode !== 1)}
            onClick={() => handleModeSwitch(1)}
          />
          <BrutalistCard
            title="Facial Control"
            description="Use head movements to scroll and navigate. Tilt up/down to scroll through content hands-free."
            icon={<Smile className="w-6 h-6" />}
            tags={['⬆️ Scroll Up', '⬇️ Scroll Down', '▶️ Play/Pause']}
            isActive={isRunning && currentMode === 2}
            isLoading={switchingMode === 2}
            disabled={!isRunning || (switchingMode !== null && switchingMode !== 2)}
            onClick={() => handleModeSwitch(2)}
          />
          <BrutalistCard
            title="Air Signature"
            description="Draw your signature in the air. Use index finger to trace, fist to clear, pinch to save."
            icon={<PenTool className="w-6 h-6" />}
            tags={['✍️ Draw', '✊ Clear', '🤏 Save']}
            isActive={isRunning && currentMode === 3}
            isLoading={switchingMode === 3}
            disabled={!isRunning || (switchingMode !== null && switchingMode !== 3)}
            onClick={() => handleModeSwitch(3)}
          />
        </div>
      </div>
    </div>
  );
}
