import { useState, useEffect, useCallback } from 'react';
import { Lock, User, PenTool, Search, ArrowRight, Trash2, Loader2, CheckCircle, XCircle, RefreshCw } from 'lucide-react';
import {
  listUsers,
  enrollUser,
  verifyUser,
  cancelAuth,
  deleteUser,
  getAuthStatus,
} from '../../api';
import type { User as UserType, AuthStatus } from '../../api';

interface LogEntry {
  id: number;
  timestamp: string;
  type: 'success' | 'error' | 'info';
  message: string;
}

export function SignatureAuth() {
  const [username, setUsername] = useState('');
  const [users, setUsers] = useState<UserType[]>([]);
  const [authLog, setAuthLog] = useState<LogEntry[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentOperation, setCurrentOperation] = useState<'none' | 'enroll' | 'verify'>('none');
  const [pollingInterval, setPollingInterval] = useState<ReturnType<typeof setInterval> | null>(null);
  let logIdCounter = 0;

  const addLog = useCallback((type: LogEntry['type'], message: string) => {
    const now = new Date();
    const timestamp = now.toLocaleTimeString('en-US', { hour12: false });
    setAuthLog(prev => [
      { id: ++logIdCounter, timestamp, type, message },
      ...prev.slice(0, 49), // Keep last 50 entries
    ]);
  }, []);

  // Load enrolled users
  const loadUsers = useCallback(async () => {
    try {
      const res = await listUsers();
      setUsers(res.users);
    } catch {
      // Silently fail — system may not be running
    }
  }, []);

  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  // Stop polling helper
  const stopPolling = useCallback(() => {
    setPollingInterval(prev => {
      if (prev) clearInterval(prev);
      return null;
    });
  }, []);

  // Poll auth status during enrollment / verification
  const startPolling = useCallback((operation: 'enroll' | 'verify') => {
    const interval = setInterval(async () => {
      try {
        const res = await getAuthStatus();
        const status: AuthStatus = res.auth_status;

        if (status.has_result && status.result) {
          stopPolling();
          setIsProcessing(false);
          setCurrentOperation('none');

          if (operation === 'enroll') {
            const result = status.result as { success?: boolean; message?: string };
            if (result.success) {
              addLog('success', result.message ?? 'Enrollment successful!');
              loadUsers(); // Refresh the user list
            } else {
              addLog('error', result.message ?? 'Enrollment failed');
            }
          } else {
            const result = status.result as { authenticated?: boolean; message?: string; confidence?: number };
            if (result.authenticated) {
              addLog('success', result.message ?? `Verified! Confidence: ${result.confidence?.toFixed(1)}%`);
            } else {
              addLog('error', result.message ?? 'Verification failed');
            }
          }
        }
      } catch {
        // API not reachable — stop gracefully
        stopPolling();
        setIsProcessing(false);
        setCurrentOperation('none');
        addLog('error', 'Lost connection to backend during operation');
      }
    }, 1500);

    setPollingInterval(interval);
  }, [stopPolling, addLog, loadUsers]);

  // Cleanup on unmount
  useEffect(() => {
    return () => stopPolling();
  }, [stopPolling]);

  const handleEnroll = async () => {
    if (!username.trim()) {
      addLog('error', 'Please enter a username before enrolling');
      return;
    }
    setIsProcessing(true);
    setCurrentOperation('enroll');
    try {
      await enrollUser(username.trim());
      addLog('info', `Enrollment started for "${username}". Draw your signature in the camera window, then show two fingers to confirm.`);
      startPolling('enroll');
    } catch (err) {
      setIsProcessing(false);
      setCurrentOperation('none');
      addLog('error', err instanceof Error ? err.message : 'Failed to start enrollment');
    }
  };

  const handleVerify = async () => {
    if (!username.trim()) {
      addLog('error', 'Please enter a username before verifying');
      return;
    }
    setIsProcessing(true);
    setCurrentOperation('verify');
    try {
      await verifyUser(username.trim());
      addLog('info', `Verification started for "${username}". Draw your signature in the camera window, then show two fingers to confirm.`);
      startPolling('verify');
    } catch (err) {
      setIsProcessing(false);
      setCurrentOperation('none');
      addLog('error', err instanceof Error ? err.message : 'Failed to start verification');
    }
  };

  const handleCancel = async () => {
    stopPolling();
    try {
      await cancelAuth();
      addLog('info', 'Operation cancelled');
    } catch {
      addLog('error', 'Failed to cancel — please try again');
    }
    setIsProcessing(false);
    setCurrentOperation('none');
  };

  const handleDeleteUser = async (uname: string) => {
    try {
      await deleteUser(uname);
      addLog('success', `User "${uname}" deleted`);
      loadUsers();
    } catch (err) {
      addLog('error', err instanceof Error ? err.message : `Failed to delete "${uname}"`);
    }
  };

  return (
    <div className="w-full flex flex-col gap-8 animate-in fade-in duration-500">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">

        {/* Left Panel — Info */}
        <div className="bg-black/50 p-8 border-4 border-white shadow-[8px_8px_0_rgba(255,255,255,0.1)] flex flex-col gap-6">
          <div className="w-16 h-16 bg-white flex items-center justify-center shadow-[4px_4px_0_#a855f7]">
            <Lock className="w-8 h-8 text-black" />
          </div>

          <h2 className="text-3xl font-black uppercase tracking-tight">Signature Authentication</h2>

          <p className="text-gray-400 font-medium leading-relaxed">
            Register your air-drawn signature as a biometric passkey, then verify your identity at any time using FastDTW pattern matching.
          </p>

          {/* Enrolled Users List */}
          <div className="mt-auto pt-4 border-t-2 border-white/20">
            <div className="flex items-center justify-between mb-3">
              <span className="text-[10px] font-mono text-[#a855f7] tracking-widest uppercase">
                Enrolled Users ({users.length})
              </span>
              <button
                onClick={loadUsers}
                className="text-gray-400 hover:text-white transition-colors"
                title="Refresh"
              >
                <RefreshCw className="w-3.5 h-3.5" />
              </button>
            </div>
            {users.length === 0 ? (
              <p className="text-gray-600 text-xs font-mono italic">No users enrolled yet</p>
            ) : (
              <div className="flex flex-col gap-2 max-h-40 overflow-y-auto">
                {users.map(u => (
                  <div
                    key={u.user_id}
                    className="flex items-center justify-between bg-white/5 border border-white/10 px-3 py-2"
                  >
                    <div>
                      <div className="text-sm font-bold text-white">{u.username}</div>
                      <div className="text-[10px] font-mono text-gray-500">{u.enrolled_date}</div>
                    </div>
                    <button
                      onClick={() => handleDeleteUser(u.username)}
                      className="text-gray-600 hover:text-red-400 transition-colors ml-3"
                      title={`Delete ${u.username}`}
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="flex flex-wrap gap-3">
            <span className="border-2 border-white bg-white/10 px-3 py-1.5 text-xs font-bold uppercase tracking-wider text-white">
              FastDTW Algorithm
            </span>
            <span className="border-2 border-white bg-white/10 px-3 py-1.5 text-xs font-bold uppercase tracking-wider text-white">
              MediaPipe Tracking
            </span>
            <span className="border-2 border-white bg-white/10 px-3 py-1.5 text-xs font-bold uppercase tracking-wider text-white">
              Biometric Auth
            </span>
          </div>
        </div>

        {/* Right Panel — Actions */}
        <div className="bg-black/50 p-8 border-4 border-white shadow-[8px_8px_0_rgba(255,255,255,0.1)] flex flex-col gap-8">

          {/* Username Input */}
          <div>
            <label className="text-[10px] font-mono text-[#a855f7] tracking-widest uppercase mb-2 block">
              Username
            </label>
            <div className="flex items-center border-4 border-white bg-black p-3 focus-within:border-[#a855f7] transition-colors shadow-[4px_4px_0_rgba(255,255,255,0.2)]">
              <User className="w-5 h-5 text-gray-500 mr-3 shrink-0" />
              <input
                type="text"
                placeholder="Enter username..."
                value={username}
                onChange={e => setUsername(e.target.value)}
                disabled={isProcessing}
                className="bg-transparent outline-none w-full text-white placeholder-gray-600 font-mono disabled:opacity-50"
              />
            </div>
          </div>

          {/* Active operation status */}
          {isProcessing && (
            <div className="flex items-center gap-3 border-2 border-yellow-400 bg-yellow-400/10 px-4 py-3">
              <Loader2 className="w-5 h-5 text-yellow-400 animate-spin shrink-0" />
              <div className="flex-1">
                <div className="text-sm font-bold text-yellow-400 uppercase">
                  {currentOperation === 'enroll' ? 'Enrolling...' : 'Verifying...'}
                </div>
                <div className="text-xs text-gray-400 font-mono mt-0.5">
                  Draw signature in camera window, then show two fingers
                </div>
              </div>
              <button
                onClick={handleCancel}
                className="text-xs font-bold text-gray-400 hover:text-white border border-gray-600 hover:border-white px-2 py-1 transition-colors"
              >
                Cancel
              </button>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex flex-col gap-4">
            <button
              onClick={handleEnroll}
              disabled={isProcessing}
              className="flex items-center justify-between border-4 border-white p-4 bg-black hover:-translate-y-1 hover:-translate-x-1 hover:shadow-[6px_6px_0_#a855f7] hover:border-[#a855f7] transition-all group disabled:opacity-40 disabled:cursor-not-allowed disabled:transform-none disabled:shadow-none"
            >
              <div className="flex items-center gap-4">
                <div className="bg-white/10 p-2">
                  <PenTool className="w-6 h-6 text-[#a855f7]" />
                </div>
                <div className="text-left">
                  <div className="font-black uppercase text-lg">Register Signature</div>
                  <div className="text-xs text-gray-400 font-mono mt-1">Draw your air signature to enroll</div>
                </div>
              </div>
              <ArrowRight className="w-6 h-6 text-white group-hover:text-[#a855f7] transition-colors" />
            </button>

            <button
              onClick={handleVerify}
              disabled={isProcessing}
              className="flex items-center justify-between border-4 border-white p-4 bg-black hover:-translate-y-1 hover:-translate-x-1 hover:shadow-[6px_6px_0_#a855f7] hover:border-[#a855f7] transition-all group disabled:opacity-40 disabled:cursor-not-allowed disabled:transform-none disabled:shadow-none"
            >
              <div className="flex items-center gap-4">
                <div className="bg-white/10 p-2">
                  <Search className="w-6 h-6 text-[#a855f7]" />
                </div>
                <div className="text-left">
                  <div className="font-black uppercase text-lg">Verify Identity</div>
                  <div className="text-xs text-gray-400 font-mono mt-1">Match against stored signature</div>
                </div>
              </div>
              <ArrowRight className="w-6 h-6 text-white group-hover:text-[#a855f7] transition-colors" />
            </button>
          </div>
        </div>
      </div>

      {/* Auth Log Panel */}
      <div className="bg-black/50 p-6 border-4 border-white shadow-[8px_8px_0_rgba(255,255,255,0.1)]">
        <div className="flex justify-between items-center border-b-4 border-white pb-4 mb-6">
          <h3 className="text-sm font-black text-[#a855f7] tracking-widest uppercase">Auth Log</h3>
          <button
            onClick={() => setAuthLog([])}
            className="border-2 border-white px-6 py-2 text-xs font-black uppercase hover:bg-white hover:text-black transition-colors shadow-[2px_2px_0_rgba(255,255,255,0.5)] active:shadow-none active:translate-y-[2px] active:translate-x-[2px]"
          >
            Clear
          </button>
        </div>

        {authLog.length === 0 ? (
          <div className="text-gray-500 italic text-sm font-mono py-4">
            No authentication events yet.
          </div>
        ) : (
          <div className="flex flex-col gap-2 max-h-64 overflow-y-auto">
            {authLog.map(entry => (
              <div key={entry.id} className="flex items-start gap-3 font-mono text-xs py-2 border-b border-white/10">
                <span className="text-gray-600 shrink-0">{entry.timestamp}</span>
                {entry.type === 'success' && <CheckCircle className="w-4 h-4 text-green-400 shrink-0 mt-0.5" />}
                {entry.type === 'error' && <XCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />}
                {entry.type === 'info' && <span className="w-4 h-4 shrink-0 mt-0.5 text-center text-blue-400">ℹ</span>}
                <span
                  className={
                    entry.type === 'success'
                      ? 'text-green-400'
                      : entry.type === 'error'
                      ? 'text-red-400'
                      : 'text-gray-300'
                  }
                >
                  {entry.message}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
