import React, { useEffect, useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useCallStore } from '../../stores/callStore';
import { useConfigStore } from '../../stores/configStore';
import { useAuthStore } from '../../stores/authStore';

interface HeaderProps {
  onOpenMobileMenu?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onOpenMobileMenu }) => {
  const navigate = useNavigate();
  const currentLanguage = useCallStore((state) => state.currentLanguage);
  const profiles = useConfigStore((state) => state.profiles);
  const selectedProfileId = useConfigStore((state) => state.selectedProfileId);
  const loadProfiles = useConfigStore((state) => state.loadProfiles);
  const selectAndActivateProfile = useConfigStore((state) => state.selectAndActivateProfile);
  const isActivating = useConfigStore((state) => state.isActivating);
  const { user, logout } = useAuthStore();
  const [showUserMenu, setShowUserMenu] = useState(false);

  const handleLogout = async () => {
    setShowUserMenu(false);
    await logout();
    navigate('/login');
  };

  useEffect(() => {
    loadProfiles();
  }, [loadProfiles]);

  const getLanguageLabel = (lang: string) => {
    switch (lang) {
      case 'hi': return 'Hindi (हिंदी)';
      case 'mr': return 'Marathi (मराठी)';
      case 'hinglish': return 'Hinglish (हिंग्लिश)';
      case 'en': 
      default: return 'English (Global)';
    }
  };

  return (
    <header className="bg-[#0d1322]/80 backdrop-blur-xl border-b border-white/10 shadow-[0_4px_30px_rgba(0,240,255,0.05)] flex justify-between items-center w-full px-6 py-3 sticky top-0 z-30 h-16">
      <div className="flex items-center gap-8 h-full">
        {/* Mobile Menu Button */}
        <button 
          onClick={onOpenMobileMenu}
          className="md:hidden text-[#b9cacb] hover:text-[#00f0ff] transition-colors p-1"
        >
          <span className="material-symbols-outlined text-[24px]">menu</span>
        </button>

        {/* Brand Logo */}
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#00f0ff] to-[#571bc1] flex items-center justify-center shadow-[0_0_15px_rgba(0,240,255,0.4)]">
            <span className="material-symbols-outlined text-[#080e1d] text-[20px] font-bold">graphic_eq</span>
          </div>
          <div>
            <div className="font-['Sora'] font-bold text-lg text-[#00f0ff] tracking-tight flex items-center gap-2">
              <span>Aura AI</span>
              <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-[#00f0ff]/10 text-[#7df4ff] border border-[#00f0ff]/20">
                PROD
              </span>
            </div>
          </div>
        </div>

        {/* Navigation Links (Hidden on Mobile) */}
        <nav className="hidden lg:flex gap-6 h-full items-center pl-4 border-l border-white/5">
          <NavLink
            to="/"
            className={({ isActive }) =>
              `text-xs font-semibold tracking-wide transition-colors duration-200 py-1 ${
                isActive ? 'text-[#00f0ff] border-b-2 border-[#00f0ff]' : 'text-[#b9cacb] hover:text-[#dde2f8]'
              }`
            }
          >
            Dashboard
          </NavLink>
          <NavLink
            to="/studio"
            className={({ isActive }) =>
              `text-xs font-semibold tracking-wide transition-colors duration-200 py-1 ${
                isActive ? 'text-[#00f0ff] border-b-2 border-[#00f0ff]' : 'text-[#b9cacb] hover:text-[#dde2f8]'
              }`
            }
          >
            Studio
          </NavLink>
          <NavLink
            to="/profiles"
            className={({ isActive }) =>
              `text-xs font-semibold tracking-wide transition-colors duration-200 py-1 ${
                isActive ? 'text-[#00f0ff] border-b-2 border-[#00f0ff]' : 'text-[#b9cacb] hover:text-[#dde2f8]'
              }`
            }
          >
            Profiles
          </NavLink>
          <NavLink
            to="/analytics"
            className={({ isActive }) =>
              `text-xs font-semibold tracking-wide transition-colors duration-200 py-1 ${
                isActive ? 'text-[#00f0ff] border-b-2 border-[#00f0ff]' : 'text-[#b9cacb] hover:text-[#dde2f8]'
              }`
            }
          >
            Analytics
          </NavLink>
        </nav>
      </div>

      {/* Trailing Status & Profile Selector */}
      <div className="flex items-center gap-3 md:gap-4">
        {/* Business Profile Selector */}
        {profiles.length > 0 && (
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#191f2f] border border-[#00f0ff]/30 text-xs font-mono text-[#00f0ff] shadow-[0_0_10px_rgba(0,240,255,0.1)]">
            <span className="material-symbols-outlined text-[15px] text-[#00f0ff]">business</span>
            <select
              value={selectedProfileId || ''}
              onChange={(e) => {
                if (e.target.value) {
                  selectAndActivateProfile(e.target.value);
                }
              }}
              disabled={isActivating}
              className="bg-transparent text-[#dde2f8] text-xs font-mono focus:outline-none cursor-pointer pr-1"
              title="Switch Active Business Profile"
            >
              {profiles.map((p) => (
                <option key={p.id} value={p.id} className="bg-[#080e1d] text-[#dde2f8]">
                  {p.name}
                </option>
              ))}
            </select>
            {isActivating && (
              <span className="material-symbols-outlined text-[13px] animate-spin text-[#00f0ff]">sync</span>
            )}
          </div>
        )}

        {/* Real-time Language Detection Badge */}
        <div className="hidden sm:flex items-center gap-2 px-3 py-1 rounded-full bg-[#191f2f] border border-white/10 text-xs font-mono text-[#b9cacb]">
          <span className="material-symbols-outlined text-[15px] text-[#65f2b5] animate-pulse">translate</span>
          <span>{getLanguageLabel(currentLanguage)}</span>
        </div>

        {/* Global Search Bar from Stitch */}
        <div className="relative hidden md:block">
          <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-[#849495] text-[16px]">
            search
          </span>
          <input
            className="bg-[#2f3445]/50 border border-white/10 rounded-full pl-9 pr-4 py-1.5 font-mono text-xs text-[#dde2f8] placeholder:text-[#849495] focus:outline-none focus:border-[#00f0ff] focus:ring-1 focus:ring-[#00f0ff] transition-all w-40 lg:w-56"
            placeholder="Search telemetry & logs..."
            type="text"
          />
        </div>

        {/* Notifications Icon with active badge */}
        <button 
          onClick={() => alert("Notification: Live multi-language code-switch detected on stream #234.")}
          className="text-[#b9cacb] hover:text-[#00f0ff] transition-colors relative p-1.5 rounded-lg hover:bg-white/5 cursor-pointer"
        >
          <span className="material-symbols-outlined text-[20px]">notifications</span>
          <span className="absolute top-1 right-1 w-2 h-2 bg-[#ffb4ab] rounded-full shadow-[0_0_8px_#ffb4ab]"></span>
        </button>

        {/* Settings Icon */}
        <NavLink 
          to="/studio"
          className="text-[#b9cacb] hover:text-[#00f0ff] transition-colors p-1.5 rounded-lg hover:bg-white/5"
        >
          <span className="material-symbols-outlined text-[20px]">settings</span>
        </NavLink>

        {/* User Menu */}
        <div className="relative">
          <button
            id="user-menu-btn"
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="flex items-center gap-2 p-1 rounded-lg hover:bg-white/5 transition-all cursor-pointer"
          >
            <div
              className="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-all"
              style={{
                background: user?.role === 'admin'
                  ? 'linear-gradient(135deg, rgba(0,240,255,0.3), rgba(87,27,193,0.4))'
                  : 'linear-gradient(135deg, rgba(87,27,193,0.3), rgba(101,242,181,0.2))',
                border: user?.role === 'admin' ? '1px solid rgba(0,240,255,0.5)' : '1px solid rgba(87,27,193,0.5)',
                boxShadow: user?.role === 'admin' ? '0 0 10px rgba(0,240,255,0.2)' : '0 0 10px rgba(87,27,193,0.2)',
                color: user?.role === 'admin' ? '#00f0ff' : '#d0bcff',
              }}
            >
              {user?.full_name?.[0]?.toUpperCase() || user?.email?.[0]?.toUpperCase() || '?'}
            </div>
            <div className="hidden md:block text-left">
              <div className="text-xs font-semibold text-[#dde2f8] leading-none truncate max-w-[100px]">
                {user?.full_name || user?.email?.split('@')[0] || 'User'}
              </div>
              <div className="text-[10px] font-mono mt-0.5" style={{ color: user?.role === 'admin' ? '#00f0ff' : '#d0bcff' }}>
                {user?.role === 'admin' ? '⬡ Admin' : '○ Customer'}
              </div>
            </div>
            <span className="material-symbols-outlined text-[16px] text-[#849495] hidden md:block">expand_more</span>
          </button>

          {/* Dropdown menu */}
          {showUserMenu && (
            <>
              <div className="fixed inset-0 z-40" onClick={() => setShowUserMenu(false)} />
              <div
                className="absolute right-0 top-full mt-2 z-50 w-56 rounded-xl p-2 glass-panel"
                style={{ border: '1px solid rgba(255,255,255,0.08)' }}
              >
                <div className="px-3 py-2 mb-1 border-b border-white/5">
                  <div className="text-sm font-semibold text-[#dde2f8] truncate">{user?.full_name || 'User'}</div>
                  <div className="text-xs text-[#849495] truncate">{user?.email}</div>
                  <div
                    className="mt-1 inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono"
                    style={{
                      background: user?.role === 'admin' ? 'rgba(0,240,255,0.08)' : 'rgba(87,27,193,0.10)',
                      color: user?.role === 'admin' ? '#00f0ff' : '#d0bcff',
                      border: user?.role === 'admin' ? '1px solid rgba(0,240,255,0.2)' : '1px solid rgba(87,27,193,0.25)',
                    }}
                  >
                    <span className="material-symbols-outlined text-[11px]">{user?.role === 'admin' ? 'shield' : 'person'}</span>
                    {user?.role === 'admin' ? 'Business Admin' : 'Customer'}
                  </div>
                </div>

                <button
                  id="logout-btn"
                  onClick={handleLogout}
                  className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-[#ff8080] hover:bg-red-500/10 transition-colors"
                >
                  <span className="material-symbols-outlined text-[16px]">logout</span>
                  Sign Out
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
};
