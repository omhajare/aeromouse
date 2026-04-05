import { useState, useEffect, useCallback } from 'react';
import { Image, RefreshCw, Calendar, Hash, User, Loader2 } from 'lucide-react';
import { listSignatures } from '../../api';
import type { Signature } from '../../api';

export function SavedSignatures() {
  const [signatures, setSignatures] = useState<Signature[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedSignature, setSelectedSignature] = useState<Signature | null>(null);

  const loadSignatures = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await listSignatures();
      setSignatures(res.signatures);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load signatures');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSignatures();
  }, [loadSignatures]);

  const formatDate = (iso: string | null) => {
    if (!iso) return '—';
    return new Date(iso).toLocaleString('en-IN', {
      dateStyle: 'medium',
      timeStyle: 'short',
    });
  };

  return (
    <div className="flex flex-col gap-8 animate-in fade-in duration-500">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-[10px] font-mono text-[#a855f7] tracking-widest uppercase mb-2">
            Cloud Storage
          </h3>
          <h4 className="text-2xl font-bold">
            Saved Signatures
            {!isLoading && (
              <span className="ml-3 text-sm font-mono text-gray-400 font-normal">
                ({signatures.length} total)
              </span>
            )}
          </h4>
        </div>
        <button
          onClick={loadSignatures}
          disabled={isLoading}
          className="flex items-center gap-2 border-2 border-white px-4 py-2 text-xs font-black uppercase hover:bg-white hover:text-black transition-colors disabled:opacity-40"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-24 border-4 border-dashed border-white/20">
          <div className="flex flex-col items-center gap-4 text-gray-400">
            <Loader2 className="w-8 h-8 animate-spin text-[#a855f7]" />
            <span className="font-mono text-sm">Loading from Cloudinary…</span>
          </div>
        </div>
      )}

      {/* Error State */}
      {!isLoading && error && (
        <div className="border-4 border-red-500 bg-red-500/10 p-8 text-center">
          <p className="text-red-400 font-mono text-sm">{error}</p>
          <p className="text-gray-500 font-mono text-xs mt-2">
            Make sure the backend is running and Cloudinary credentials are configured.
          </p>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !error && signatures.length === 0 && (
        <div className="border-4 border-dashed border-white/20 p-16 text-center">
          <Image className="w-12 h-12 text-gray-600 mx-auto mb-4" />
          <p className="text-gray-400 font-mono text-sm">No signatures saved yet.</p>
          <p className="text-gray-600 font-mono text-xs mt-2">
            Switch to Air Signature mode and draw something to get started.
          </p>
        </div>
      )}

      {/* Signature Grid */}
      {!isLoading && !error && signatures.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {signatures.map(sig => (
            <div
              key={sig.id}
              onClick={() => setSelectedSignature(sig)}
              className="group border-4 border-white bg-black/80 cursor-pointer hover:-translate-y-1 hover:-translate-x-1 hover:border-[#a855f7] hover:shadow-[8px_8px_0_#a855f7] transition-all duration-200"
            >
              {/* Image */}
              <div className="aspect-square bg-gray-900 overflow-hidden">
                {sig.url ? (
                  <img
                    src={sig.url}
                    alt={sig.filename}
                    className="w-full h-full object-contain p-2 group-hover:opacity-90 transition-opacity"
                    loading="lazy"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-gray-700">
                    <Image className="w-8 h-8" />
                  </div>
                )}
              </div>

              {/* Meta */}
              <div className="p-3 border-t-4 border-white group-hover:border-[#a855f7] transition-colors">
                <div className="flex items-center gap-1.5 text-[10px] font-mono text-gray-400 mb-1">
                  <Calendar className="w-3 h-3 shrink-0" />
                  <span>{formatDate(sig.created_at)}</span>
                </div>
                {sig.username && (
                  <div className="flex items-center gap-1.5 text-[10px] font-mono text-[#a855f7]">
                    <User className="w-3 h-3 shrink-0" />
                    <span>{sig.username}</span>
                  </div>
                )}
                {sig.point_count > 0 && (
                  <div className="flex items-center gap-1.5 text-[10px] font-mono text-gray-600 mt-1">
                    <Hash className="w-3 h-3 shrink-0" />
                    <span>{sig.point_count} trajectory points</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Lightbox */}
      {selectedSignature && (
        <div
          className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-8"
          onClick={() => setSelectedSignature(null)}
        >
          <div
            className="bg-black border-4 border-white max-w-2xl w-full shadow-[12px_12px_0_#a855f7]"
            onClick={e => e.stopPropagation()}
          >
            <div className="flex items-center justify-between p-4 border-b-4 border-white">
              <h3 className="font-black uppercase text-sm tracking-widest">
                {selectedSignature.filename}
              </h3>
              <button
                onClick={() => setSelectedSignature(null)}
                className="font-black text-gray-400 hover:text-white transition-colors text-lg leading-none"
              >
                ✕
              </button>
            </div>
            <div className="bg-gray-900 p-4">
              <img
                src={selectedSignature.url}
                alt={selectedSignature.filename}
                className="w-full object-contain max-h-96"
              />
            </div>
            <div className="p-4 grid grid-cols-2 gap-4 text-xs font-mono text-gray-400">
              <div>
                <span className="text-[#a855f7]">Saved: </span>
                {formatDate(selectedSignature.created_at)}
              </div>
              <div>
                <span className="text-[#a855f7]">User: </span>
                {selectedSignature.username ?? 'Anonymous'}
              </div>
              <div>
                <span className="text-[#a855f7]">Points: </span>
                {selectedSignature.point_count}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
