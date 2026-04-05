import { ArrowDown, MoreHorizontal } from 'lucide-react';

interface HeroProps {
  onDiscoverClick: () => void;
}

export function Hero({ onDiscoverClick }: HeroProps) {
  return (
    <section className="w-full h-[calc(100vh-220px)] flex flex-col justify-between p-8 md:p-12 pointer-events-none">
      {/* Top Header */}
      <header className="flex justify-between items-start">
        <div className="text-sm font-mono tracking-widest text-gray-400">
          001/005
        </div>

        <h1 className="text-3xl md:text-5xl lg:text-6xl font-bold tracking-tighter max-w-2xl leading-tight text-center">
          THE FUTURE OF <br />
          TOUCHLESS CONTROL
        </h1>

        <div className="pointer-events-auto cursor-pointer">
          <MoreHorizontal className="w-8 h-8" />
        </div>
      </header>

      {/* Bottom Section */}
      <footer className="flex flex-col md:flex-row justify-end items-end gap-8">
        {/* Right Content Box */}
        <div className="max-w-sm pointer-events-auto">
          <h2 className="text-xl font-medium mb-4">Aero-mouse Systems</h2>
          <p className="text-gray-400 text-sm leading-relaxed mb-6">
            Control your cursor with a gesture, navigate with your
            gaze, and authenticate with your unique air signature
            — all in real time. No hardware. No touch. Just you.
          </p>
          <div className="flex flex-wrap gap-3">
            <button
              onClick={onDiscoverClick}
              className="bg-[#a855f7] hover:bg-[#9333ea] text-white px-6 py-3 rounded-sm text-sm font-medium transition-colors flex items-center gap-2"
            >
              Explore Platform &rarr;
            </button>
          </div>
        </div>
      </footer>
    </section>
  );
}
