import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import type { UserRole } from '../stores/authStore';

export const RegisterPage: React.FC = () => {
  const navigate = useNavigate();
  const { register, loading, error, clearError, user } = useAuthStore();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [role, setRole] = useState<UserRole>('customer');
  const [showPass, setShowPass] = useState(false);
  const [localError, setLocalError] = useState('');

  useEffect(() => {
    if (user) navigate('/', { replace: true });
    clearError();
  }, [user]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError('');
    if (password !== confirmPassword) {
      setLocalError('Passwords do not match');
      return;
    }
    if (password.length < 6) {
      setLocalError('Password must be at least 6 characters');
      return;
    }
    try {
      await register(email, password, fullName, role);
      navigate('/', { replace: true });
    } catch {
      // error is in store
    }
  };

  const displayError = localError || error;

  return (
    <div
      className="min-h-screen flex items-center justify-center px-4 py-10 relative overflow-hidden"
      style={{
        background: 'radial-gradient(ellipse at 50% 0%, rgba(87,27,193,0.12) 0%, transparent 60%), #0d1322',
      }}
    >
      {/* Grid */}
      <div className="absolute inset-0 pointer-events-none"
        style={{
          backgroundImage: 'linear-gradient(rgba(255,255,255,0.013) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.013) 1px, transparent 1px)',
          backgroundSize: '32px 32px',
        }}
      />
      {/* Glow orbs */}
      <div className="absolute top-[-100px] right-[-60px] w-[420px] h-[420px] rounded-full pointer-events-none"
        style={{ background: 'radial-gradient(circle, rgba(0,240,255,0.07) 0%, transparent 70%)' }}
      />
      <div className="absolute bottom-[-80px] left-[-60px] w-[360px] h-[360px] rounded-full pointer-events-none"
        style={{ background: 'radial-gradient(circle, rgba(87,27,193,0.10) 0%, transparent 70%)' }}
      />

      <div className="relative z-10 w-full max-w-md">
        {/* Brand */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center"
              style={{ background: 'linear-gradient(135deg, #00f0ff22, #571bc122)', border: '1px solid rgba(0,240,255,0.3)' }}
            >
              <span className="material-symbols-outlined text-[#00f0ff] text-[22px]">hub</span>
            </div>
            <span className="font-['Sora'] text-2xl font-bold text-[#dde2f8]">Aura Voice <span className="text-[#00f0ff]">AI</span></span>
          </div>
          <p className="text-[#849495] text-sm">Create your account to get started</p>
        </div>

        {/* Card */}
        <div className="rounded-2xl p-8 glass-panel" style={{ border: '1px solid rgba(87,27,193,0.2)' }}>
          {displayError && (
            <div className="mb-5 p-3 rounded-lg text-sm flex items-center gap-2"
              style={{ background: 'rgba(255,100,100,0.08)', border: '1px solid rgba(255,100,100,0.2)', color: '#ff8080' }}
            >
              <span className="material-symbols-outlined text-[16px]">error</span>
              {displayError}
            </div>
          )}

          {/* Role Selector */}
          <div className="mb-6">
            <label className="block text-xs font-semibold text-[#849495] uppercase tracking-wider mb-3">
              Account Type
            </label>
            <div className="grid grid-cols-2 gap-3">
              {([
                { value: 'admin', label: 'Business Owner', icon: 'domain', desc: 'Manage your AI agent' },
                { value: 'customer', label: 'Customer', icon: 'person', desc: 'Access AI services' },
              ] as { value: UserRole; label: string; icon: string; desc: string }[]).map(opt => (
                <button
                  key={opt.value}
                  type="button"
                  id={`role-${opt.value}`}
                  onClick={() => setRole(opt.value)}
                  className="p-4 rounded-xl text-left transition-all duration-200 flex flex-col gap-1"
                  style={{
                    border: role === opt.value
                      ? `1px solid ${opt.value === 'admin' ? 'rgba(0,240,255,0.5)' : 'rgba(87,27,193,0.6)'}`
                      : '1px solid rgba(255,255,255,0.06)',
                    background: role === opt.value
                      ? opt.value === 'admin' ? 'rgba(0,240,255,0.07)' : 'rgba(87,27,193,0.10)'
                      : 'rgba(8,14,29,0.4)',
                  }}
                >
                  <span className={`material-symbols-outlined text-[20px] ${role === opt.value ? (opt.value === 'admin' ? 'text-[#00f0ff]' : 'text-[#d0bcff]') : 'text-[#849495]'}`}>
                    {opt.icon}
                  </span>
                  <span className={`text-sm font-semibold ${role === opt.value ? 'text-[#dde2f8]' : 'text-[#849495]'}`}>{opt.label}</span>
                  <span className="text-[11px] text-[#849495]">{opt.desc}</span>
                </button>
              ))}
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Full name */}
            <div>
              <label className="block text-xs font-semibold text-[#849495] uppercase tracking-wider mb-2">
                Full Name
              </label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 material-symbols-outlined text-[18px] text-[#849495]">badge</span>
                <input
                  id="register-name"
                  type="text"
                  required
                  value={fullName}
                  onChange={e => setFullName(e.target.value)}
                  placeholder={role === 'admin' ? 'Business / Owner name' : 'Your full name'}
                  className="w-full pl-10 pr-4 py-3 rounded-lg text-sm text-[#dde2f8] outline-none transition-all"
                  style={{ background: 'rgba(8,14,29,0.6)', border: '1px solid rgba(255,255,255,0.08)', caretColor: '#00f0ff' }}
                  onFocus={e => e.currentTarget.style.borderColor = 'rgba(0,240,255,0.4)'}
                  onBlur={e => e.currentTarget.style.borderColor = 'rgba(255,255,255,0.08)'}
                />
              </div>
            </div>

            {/* Email */}
            <div>
              <label className="block text-xs font-semibold text-[#849495] uppercase tracking-wider mb-2">Email</label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 material-symbols-outlined text-[18px] text-[#849495]">mail</span>
                <input
                  id="register-email"
                  type="email"
                  required
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="w-full pl-10 pr-4 py-3 rounded-lg text-sm text-[#dde2f8] outline-none transition-all"
                  style={{ background: 'rgba(8,14,29,0.6)', border: '1px solid rgba(255,255,255,0.08)', caretColor: '#00f0ff' }}
                  onFocus={e => e.currentTarget.style.borderColor = 'rgba(0,240,255,0.4)'}
                  onBlur={e => e.currentTarget.style.borderColor = 'rgba(255,255,255,0.08)'}
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label className="block text-xs font-semibold text-[#849495] uppercase tracking-wider mb-2">Password</label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 material-symbols-outlined text-[18px] text-[#849495]">lock</span>
                <input
                  id="register-password"
                  type={showPass ? 'text' : 'password'}
                  required
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="Min 6 characters"
                  className="w-full pl-10 pr-10 py-3 rounded-lg text-sm text-[#dde2f8] outline-none transition-all"
                  style={{ background: 'rgba(8,14,29,0.6)', border: '1px solid rgba(255,255,255,0.08)', caretColor: '#00f0ff' }}
                  onFocus={e => e.currentTarget.style.borderColor = 'rgba(0,240,255,0.4)'}
                  onBlur={e => e.currentTarget.style.borderColor = 'rgba(255,255,255,0.08)'}
                />
                <button type="button" onClick={() => setShowPass(!showPass)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[#849495] hover:text-[#dde2f8]" tabIndex={-1}>
                  <span className="material-symbols-outlined text-[18px]">{showPass ? 'visibility_off' : 'visibility'}</span>
                </button>
              </div>
            </div>

            {/* Confirm Password */}
            <div>
              <label className="block text-xs font-semibold text-[#849495] uppercase tracking-wider mb-2">Confirm Password</label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 material-symbols-outlined text-[18px] text-[#849495]">lock_reset</span>
                <input
                  id="register-confirm"
                  type={showPass ? 'text' : 'password'}
                  required
                  value={confirmPassword}
                  onChange={e => setConfirmPassword(e.target.value)}
                  placeholder="Re-enter password"
                  className="w-full pl-10 pr-4 py-3 rounded-lg text-sm text-[#dde2f8] outline-none transition-all"
                  style={{
                    background: 'rgba(8,14,29,0.6)',
                    border: `1px solid ${confirmPassword && confirmPassword !== password ? 'rgba(255,100,100,0.4)' : 'rgba(255,255,255,0.08)'}`,
                    caretColor: '#00f0ff',
                  }}
                  onFocus={e => e.currentTarget.style.borderColor = 'rgba(0,240,255,0.4)'}
                  onBlur={e => e.currentTarget.style.borderColor = confirmPassword !== password ? 'rgba(255,100,100,0.4)' : 'rgba(255,255,255,0.08)'}
                />
              </div>
            </div>

            {/* Submit */}
            <button
              id="register-submit"
              type="submit"
              disabled={loading}
              className="w-full py-3 rounded-lg font-semibold text-sm transition-all duration-200 mt-2"
              style={{
                background: loading ? 'rgba(87,27,193,0.15)' : 'linear-gradient(135deg, #571bc1, #7c3aed)',
                color: '#e9ddff',
                boxShadow: loading ? 'none' : '0 0 24px rgba(87,27,193,0.35)',
              }}
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-[#d0bcff]/40 border-t-[#d0bcff] rounded-full animate-spin" />
                  Creating accountâ€¦
                </span>
              ) : 'Create Account'}
            </button>
          </form>

          {/* Divider */}
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-white/5" />
            </div>
            <div className="relative text-center">
              <span className="px-3 text-xs text-[#849495]" style={{ background: 'rgba(25,31,47,0.9)' }}>
                Already have an account?
              </span>
            </div>
          </div>

          <Link
            to="/login"
            id="goto-login"
            className="block w-full py-3 rounded-lg text-sm font-medium text-center transition-all duration-200"
            style={{ border: '1px solid rgba(0,240,255,0.25)', color: '#7df4ff', background: 'rgba(0,240,255,0.04)' }}
            onMouseEnter={e => {
              (e.currentTarget as HTMLElement).style.background = 'rgba(0,240,255,0.09)';
              (e.currentTarget as HTMLElement).style.borderColor = 'rgba(0,240,255,0.45)';
            }}
            onMouseLeave={e => {
              (e.currentTarget as HTMLElement).style.background = 'rgba(0,240,255,0.04)';
              (e.currentTarget as HTMLElement).style.borderColor = 'rgba(0,240,255,0.25)';
            }}
          >
            Sign in instead
          </Link>
        </div>
      </div>
    </div>
  );
};
