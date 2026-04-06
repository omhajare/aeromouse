import React from 'react';

interface BrutalistCardProps {
  title: string;
  description: string;
  icon: React.ReactNode;
  tags: string[];
}

export function BrutalistCard({
  title,
  description,
  icon,
  tags,
}: BrutalistCardProps) {
  return (
    <div
      className="w-full border-4 bg-black/80 backdrop-blur-md p-5 font-sans text-white flex flex-col h-full transition-all duration-200 border-white shadow-[8px_8px_0_rgba(255,255,255,0.2)] hover:-translate-y-1 hover:-translate-x-1 hover:shadow-[10px_10px_0_#a855f7]"
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

      <div className="mt-4 flex items-center justify-between">
        <div className="text-[10px] font-mono text-[#a855f7] tracking-widest uppercase">
          Core Module
        </div>
        <div className="w-2 h-2 rounded-full bg-[#a855f7] animate-pulse"></div>
      </div>
    </div>
  );
}

