import { useState, useEffect } from 'react';
import { WifiOff, Wifi, Database, Cloud, Monitor } from 'lucide-react';

interface ServiceStatus {
  backend: boolean;
  database: boolean;
  cloudinary: boolean;
}

export function OfflineBanner() {
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [services, setServices] = useState<ServiceStatus | null>(null);

  // Browser online/offline events
  useEffect(() => {
    const goOnline = () => setIsOnline(true);
    const goOffline = () => setIsOnline(false);

    window.addEventListener('online', goOnline);
    window.addEventListener('offline', goOffline);
    return () => {
      window.removeEventListener('online', goOnline);
      window.removeEventListener('offline', goOffline);
    };
  }, []);

  // Poll /api/health every 10 seconds
  useEffect(() => {
    let cancelled = false;

    const checkHealth = async () => {
      try {
        const res = await fetch('/api/health');
        const data = await res.json();
        if (!cancelled) setServices(data.services);
      } catch {
        if (!cancelled) setServices(null);
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 10_000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  // Determine what to show
  const backendDown = services === null;
  const dbDown = services !== null && !services.database;
  const cloudDown = services !== null && !services.cloudinary;
  const anyIssue = !isOnline || backendDown || dbDown || cloudDown;

  if (!anyIssue) return null;

  return (
    <div className="fixed top-0 left-0 right-0 z-[100] animate-in slide-in-from-top duration-300">
      <div className="bg-gradient-to-r from-amber-900/95 to-red-900/95 backdrop-blur-md border-b border-amber-500/30 px-4 py-2.5">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
          {/* Left: Main message */}
          <div className="flex items-center gap-3">
            <WifiOff className="w-4 h-4 text-amber-400 shrink-0" />
            <span className="text-amber-100 text-xs font-medium">
              {!isOnline
                ? 'You are offline — cloud features unavailable'
                : backendDown
                  ? 'Backend is not reachable — start AeroMouse.exe'
                  : 'Some cloud services are degraded'}
            </span>
          </div>

          {/* Right: Service status pills */}
          <div className="hidden sm:flex items-center gap-2">
            <StatusPill
              icon={<Monitor className="w-3 h-3" />}
              label="Backend"
              ok={!backendDown}
            />
            <StatusPill
              icon={<Database className="w-3 h-3" />}
              label="Database"
              ok={services?.database ?? false}
            />
            <StatusPill
              icon={<Cloud className="w-3 h-3" />}
              label="Storage"
              ok={services?.cloudinary ?? false}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

function StatusPill({
  icon,
  label,
  ok,
}: {
  icon: React.ReactNode;
  label: string;
  ok: boolean;
}) {
  return (
    <div
      className={`flex items-center gap-1.5 px-2 py-1 rounded-full text-[10px] font-mono uppercase tracking-wider ${
        ok
          ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
          : 'bg-red-500/20 text-red-300 border border-red-500/30'
      }`}
    >
      {icon}
      {label}
      <span className={`w-1.5 h-1.5 rounded-full ${ok ? 'bg-emerald-400' : 'bg-red-400 animate-pulse'}`} />
    </div>
  );
}
