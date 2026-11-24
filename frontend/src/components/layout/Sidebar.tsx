import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useCallStore } from '../../stores/callStore';
import { useAuthStore } from '../../stores/authStore';

export const Sidebar: React.FC = () => {
  const orbState = useCallStore((state) => state.orbState);
  const { user } = useAuthStore();
  const isAdmin = user?.role === 'admin';
  const navigate = useNavigate();

  const navItems = [
    { to: '/', label: 'Live Monitor', icon: 'monitor_heart', adminOnly: false },
    { to: '/studio', label: 'Agent Studio', icon: 'psychology', adminOnly: true },
    { to: '/profiles', label: 'Profiles', icon: 'domain', adminOnly: true },
    { to: '/onboarding', label: 'Business Setup', icon: 'storefront', adminOnly: true },
    { to: '/escalations', label: 'Escalations', icon: 'warning', adminOnly: false },
    { to: '/integrations', label: 'Integrations', icon: 'hub', adminOnly: true },
    { to: '/analytics', label: 'Analytics', icon: 'insights', adminOnly: false },
  ].filter(item => !item.adminOnly || isAdmin);

  return (
    <nav className="hidden md:flex bg-[#080e1d] border-r border-white/5 fixed left-0 top-0 h-full w-[260px] flex-col py-8 px-4 z-40">
      {/* Header Info: System Status */}
      <div className="px-3 mb-8 flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-[#00f0ff]/15 flex items-center justify-center border border-[#00f0ff]/30 relative">
          <span className="material-symbols-outlined text-[#00f0ff] text-[20px]">
            {orbState === 'human_transfer' ? 'support_agent' : 'graphic_eq'}
          </span>
          <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-[#65f2b5] rounded-full border-2 border-[#080e1d] animate-pulse"></div>
        </div>
        <div>
          <h2 className="text-xs font-semibold text-[#dde2f8] tracking-wider uppercase">System Active</h2>
          <p className="font-mono text-[#b9cacb] text-[11px]">Production Engine</p>
        </div>
      </div>

      {/* Main Navigation Tabs */}
      <div className="flex flex-col gap-1.5 flex-grow">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 ${isActive
                ? 'bg-[#00f0ff]/10 border-r-2 border-[#00f0ff] text-[#00f0ff] font-semibold shadow-[inset_0_0_15px_rgba(0,240,255,0.06)]'
                : 'text-[#b9cacb] hover:text-[#dde2f8] hover:bg-white/5 hover:text-[#7df4ff]'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <span
                  className={`material-symbols-outlined text-[20px] transition-colors ${isActive ? 'fill text-[#00f0ff]' : 'text-[#849495]'
                    }`}
                >
                  {item.icon}
                </span>
                <span>{item.label}</span>
              </>
            )}
          </NavLink>
        ))}
      </div>

      {/* CTA Button: Deploy New Agent from Stitch */}
      <div className="mb-6 px-1">
        <button
          onClick={() => navigate('/onboarding')}
          className="w-full py-2.5 px-4 bg-[#00f0ff] text-[#00363a] font-semibold text-xs rounded-lg shadow-[0_0_15px_rgba(0,240,255,0.3)] hover:shadow-[0_0_25px_rgba(0,240,255,0.6)] hover:bg-[#7df4ff] transition-all flex items-center justify-center gap-2 cursor-pointer active:scale-98"
        >
          <span className="material-symbols-outlined text-[18px]">add_business</span>
          Setup My Business
        </button>
      </div>

      {/* Footer Tabs */}
      <div className="flex flex-col gap-1 border-t border-white/5 pt-4 px-1">
        <a
          href="#support"
          onClick={(e) => { e.preventDefault(); alert("Aura Voice AI Enterprise Support: 24/7 Priority Voice Gateway active."); }}
          className="flex items-center gap-3 px-3 py-2 rounded-lg text-[#b9cacb] hover:text-[#dde2f8] hover:bg-white/5 transition-all text-xs font-mono"
        >
          <span className="material-symbols-outlined text-[18px]">help</span>
          <span>Support</span>
        </a>
      </div>
    </nav>
  );
};
