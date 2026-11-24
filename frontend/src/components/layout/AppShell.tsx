import React, { useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';

export const AppShell: React.FC = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="bg-[#0d1322] text-[#dde2f8] min-h-screen overflow-x-hidden flex selection:bg-[#00f0ff] selection:text-[#00363a]">
      {/* Desktop Sidebar (260px fixed) */}
      <Sidebar />

      {/* Mobile Drawer Overlay */}
      {mobileMenuOpen && (
        <div 
          className="fixed inset-0 bg-black/70 backdrop-blur-md z-50 md:hidden flex"
          onClick={() => setMobileMenuOpen(false)}
        >
          <div 
            className="w-64 bg-[#080e1d] h-full p-6 flex flex-col justify-between border-r border-white/10"
            onClick={(e) => e.stopPropagation()}
          >
            <div>
              <div className="flex items-center justify-between mb-8">
                <div className="font-['Sora'] font-bold text-lg text-[#00f0ff]">Aura Voice AI</div>
                <button onClick={() => setMobileMenuOpen(false)} className="text-[#b9cacb]">
                  <span className="material-symbols-outlined">close</span>
                </button>
              </div>

              <div className="flex flex-col gap-2">
                <NavLink
                  to="/"
                  onClick={() => setMobileMenuOpen(false)}
                  className="flex items-center gap-3 px-4 py-3 rounded-lg text-sm text-[#b9cacb] hover:bg-white/5"
                >
                  <span className="material-symbols-outlined">monitor_heart</span>
                  <span>Live Monitor</span>
                </NavLink>
                <NavLink
                  to="/studio"
                  onClick={() => setMobileMenuOpen(false)}
                  className="flex items-center gap-3 px-4 py-3 rounded-lg text-sm text-[#b9cacb] hover:bg-white/5"
                >
                  <span className="material-symbols-outlined">psychology</span>
                  <span>Agent Studio</span>
                </NavLink>
                <NavLink
                  to="/profiles"
                  onClick={() => setMobileMenuOpen(false)}
                  className="flex items-center gap-3 px-4 py-3 rounded-lg text-sm text-[#b9cacb] hover:bg-white/5"
                >
                  <span className="material-symbols-outlined">domain</span>
                  <span>Profiles</span>
                </NavLink>
                <NavLink
                  to="/analytics"
                  onClick={() => setMobileMenuOpen(false)}
                  className="flex items-center gap-3 px-4 py-3 rounded-lg text-sm text-[#b9cacb] hover:bg-white/5"
                >
                  <span className="material-symbols-outlined">insights</span>
                  <span>Analytics</span>
                </NavLink>
              </div>
            </div>

            <div className="text-xs font-mono text-[#849495] pt-4 border-t border-white/5">
              Aura Voice AI — v4.2 Neural Link
            </div>
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col md:pl-[260px] min-h-screen pb-16 md:pb-0">
        <Header onOpenMobileMenu={() => setMobileMenuOpen(true)} />
        <main className="flex-1 p-4 md:p-6 lg:p-8 max-w-[1700px] w-full mx-auto">
          <Outlet />
        </main>
      </div>

      {/* Mobile Bottom Navigation from Stitch */}
      <nav className="md:hidden fixed bottom-0 left-0 w-full bg-[#080e1d]/90 backdrop-blur-lg border-t border-white/5 z-40 px-2 py-1.5 flex justify-around">
        <NavLink
          to="/"
          className={({ isActive }) =>
            `flex flex-col items-center p-1.5 rounded-lg transition-colors ${
              isActive ? 'text-[#00f0ff] bg-[#00f0ff]/10' : 'text-[#849495]'
            }`
          }
        >
          <span className="material-symbols-outlined text-[20px]">monitor_heart</span>
          <span className="text-[10px] font-semibold mt-0.5">Monitor</span>
        </NavLink>
        <NavLink
          to="/studio"
          className={({ isActive }) =>
            `flex flex-col items-center p-1.5 rounded-lg transition-colors ${
              isActive ? 'text-[#00f0ff] bg-[#00f0ff]/10' : 'text-[#849495]'
            }`
          }
        >
          <span className="material-symbols-outlined text-[20px]">psychology</span>
          <span className="text-[10px] font-semibold mt-0.5">Studio</span>
        </NavLink>
        <NavLink
          to="/profiles"
          className={({ isActive }) =>
            `flex flex-col items-center p-1.5 rounded-lg transition-colors ${
              isActive ? 'text-[#00f0ff] bg-[#00f0ff]/10' : 'text-[#849495]'
            }`
          }
        >
          <span className="material-symbols-outlined text-[20px]">domain</span>
          <span className="text-[10px] font-semibold mt-0.5">Profiles</span>
        </NavLink>
        <NavLink
          to="/analytics"
          className={({ isActive }) =>
            `flex flex-col items-center p-1.5 rounded-lg transition-colors ${
              isActive ? 'text-[#00f0ff] bg-[#00f0ff]/10' : 'text-[#849495]'
            }`
          }
        >
          <span className="material-symbols-outlined text-[20px]">insights</span>
          <span className="text-[10px] font-semibold mt-0.5">Analytics</span>
        </NavLink>
      </nav>
    </div>
  );
};
