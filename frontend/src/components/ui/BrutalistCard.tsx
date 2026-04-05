import React from 'react';
import { Loader2 } from 'lucide-react';

interface BrutalistCardProps {
  title: string;
  description: string;
  icon: React.ReactNode;
  tags: string[];
  isActive: boolean;
  isLoading?: boolean;
  disabled?: boolean;
  onClick?: () => void;
}

export function BrutalistCard({
  title,
  description,
  icon,
  tags,
  isActive,
  isLoading = false,
  disabled = false,
  onClick,
}: BrutalistCardProps) {
  return (
    <div
      className={`w-full border-4 bg-black/80 backdrop-blur-md p-5 font-sans text-white flex flex-col h-full transition-all duration-200
        ${isActive
          ? 'border-[#a855f7] shadow-[8px_8px_0_#a855f7]'
          : 'border-white shadow-[8px_8px_0_rgba(255,255,255,0.2)] hover:-translate-y-1 hover:-translate-x-1 hover:shadow-[10px_10px_0_#a855f7]'
        }`}
    >
      <div className="flex items-center gap-3 mb-4 border-b-2 border-white pb-4">
        <div className="shrink-0 flex items-center justify-center bg-white p-2 text-black">
          {icon}
        </div>
        <div className="font-black text-white text-lg uppercase leading-tight">{title}</div>
      </div>

      <div className="mt-2 text-gray-300 text-sm leading-relaxed border-b-2 border-white pb-4 font-semibold flex-grow">
        {description}
        <div className="flex flex-wrap gap-2 mt-4">
          {tags.map(tag => (
            <span
              key={tag}
              className="text-[10px] font-bold border-2 border-white px-2 py-1 bg-white/10 uppercase"
            >
              {tag}
            </span>
          ))}
        </div>
      </div>

      <div className="mt-4 flex flex-col gap-3">
        <div
          className={`text-xs font-black uppercase px-3 py-1.5 border-2 border-white self-start ${
            isActive ? 'bg-[#a855f7] text-white border-[#a855f7]' : 'bg-white/20 text-gray-300'
          }`}
        >
          {isActive ? 'ACTIVE' : 'INACTIVE'}
        </div>

        <button
          onClick={onClick}
          disabled={disabled || isLoading}
          className={`block w-full px-4 py-3 text-center text-sm font-bold uppercase border-[3px] border-white relative transition-all duration-200 shadow-[4px_4px_0_#fff] hover:-translate-y-[2px] hover:-translate-x-[2px] hover:shadow-[6px_6px_0_#fff] active:translate-y-[2px] active:translate-x-[2px] active:shadow-none disabled:opacity-40 disabled:cursor-not-allowed disabled:transform-none disabled:shadow-none ${
            isActive
              ? 'bg-red-600 text-white hover:bg-red-500 hover:border-red-500'
              : 'bg-black text-white hover:bg-[#a855f7] hover:border-[#a855f7]'
          }`}
        >
          {isLoading ? (
            <span className="flex items-center justify-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin" />
              {isActive ? 'Deactivating...' : 'Activating...'}
            </span>
          ) : isActive ? (
            'Deactivate'
          ) : (
            'Activate'
          )}
        </button>
      </div>
    </div>
  );
}
