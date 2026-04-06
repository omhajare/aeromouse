import { ArrowDown, Download, MoreHorizontal } from 'lucide-react';

interface HeroProps {
  onDiscoverClick: () => void;
}

// Link to the latest GitHub release — update after first build
// Build download URLs from environment variables
const ZIP_URL = import.meta.env.VITE_DOWNLOAD_ZIP || 'https://github.com/omhajare/aeromouse/releases/latest';

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
            <a
              href={ZIP_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="bg-white hover:bg-gray-100 text-black px-6 py-3 rounded-sm text-sm font-bold transition-colors flex items-center gap-2 group border border-white/20"
            >
              <Download className="w-4 h-4 group-hover:translate-y-0.5 transition-transform" />
              Download Source (.ZIP)
            </a>
            <button
              onClick={onDiscoverClick}
              className="bg-[#a855f7] hover:bg-[#9333ea] text-white px-6 py-3 rounded-sm text-sm font-medium transition-colors flex items-center gap-2 shadow-[4px_4px_0_rgba(168,85,247,0.3)]"
            >
              Explore Platform &rarr;
            </button>
          </div>
          <p className="text-gray-600 text-[10px] font-mono mt-3 tracking-wide">
            Windows 10/11 · Open Source Preview
          </p>
        </div>
      </footer>
    </section>
  );
}

