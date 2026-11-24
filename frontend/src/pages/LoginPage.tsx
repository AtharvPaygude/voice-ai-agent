import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login, loading, error, clearError, user } = useAuthStore();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPass, setShowPass] = useState(false);

  useEffect(() => {
    if (user) navigate('/', { replace: true });
    clearError();
  }, [user]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await login(email, password);
      navigate('/', { replace: true });
    } catch {
      // error is set in the store
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 relative overflow-hidden"
      style={{
        background: 'radial-gradient(ellipse at 50% 0%, rgba(0,240,255,0.10) 0%, transparent 60%), #0d1322',
      }}
    >
      {/* Decorative grid */}
      <div className="absolute inset-0 pointer-events-none"
        style={{
          backgroundImage: 'linear-gradient(rgba(255,255,255,0.013) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.013) 1px, transparent 1px)',
          backgroundSize: '32px 32px',
        }}
      />

      {/* Glow orb */}
      <div className="absolute top-[-120px] left-1/2 -translate-x-1/2 w-[500px] h-[500px] rounded-full pointer-events-none"
        style={{ background: 'radial-gradient(circle, rgba(0,240,255,0.08) 0%, transparent 70%)' }}
      />
      <div className="absolute bottom-[-100px] right-[-80px] w-[400px] h-[400px] rounded-full pointer-events-none"
        style={{ background: 'radial-gradient(circle, rgba(87,27,193,0.10) 0%, transparent 70%)' }}
      />

      <div className="relative z-10 w-full max-w-md">
        {/* Logo / brand */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center"
              style={{ background: 'linear-gradient(135deg, #00f0ff22, #571bc122)', border: '1px solid rgba(0,240,255,0.3)' }}
            >
              <span className="material-symbols-outlined text-[#00f0ff] text-[22px]">hub</span>
            </div>
            <span className="font-['Sora'] text-2xl font-bold text-[#dde2f8]">Aura Voice <span className="text-[#00f0ff]">AI</span></span>
          </div>
          <p className="text-[#849495] text-sm">Sign in to your account</p>
        </div>

        {/* Card */}
        <div className="rounded-2xl p-8 glass-panel" style={{ border: '1px solid rgba(0,240,255,0.12)' }}>
          {error && (
            <div className="mb-5 p-3 rounded-lg text-sm flex items-center gap-2"
              style={{ background: 'rgba(255,100,100,0.08)', border: '1px solid rgba(255,100,100,0.2)', color: '#ff8080' }}
            >
              <span className="material-symbols-outlined text-[16px]">error</span>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Email */}
            <div>
              <label className="block text-xs font-semibold text-[#849495] uppercase tracking-wider mb-2">
                Email
              </label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 material-symbols-outlined text-[18px] text-[#849495]">
                  mail
                </span>
                <input
                  id="login-email"
                  type="email"
                  required
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="w-full pl-10 pr-4 py-3 rounded-lg text-sm text-[#dde2f8] outline-none transition-all"
                  style={{
                    background: 'rgba(8,14,29,0.6)',
                    border: '1px solid rgba(255,255,255,0.08)',
                    caretColor: '#00f0ff',
                  }}
                  onFocus={e => e.currentTarget.style.borderColor = 'rgba(0,240,255,0.4)'}
                  onBlur={e => e.currentTarget.style.borderColor = 'rgba(255,255,255,0.08)'}
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label className="block text-xs font-semibold text-[#849495] uppercase tracking-wider mb-2">
                Password
              </label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 material-symbols-outlined text-[18px] text-[#849495]">
                  lock
                </span>
                <input
                  id="login-password"
                  type={showPass ? 'text' : 'password'}
                  required
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-10 pr-10 py-3 rounded-lg text-sm text-[#dde2f8] outline-none transition-all"
                  style={{
                    background: 'rgba(8,14,29,0.6)',
                    border: '1px solid rgba(255,255,255,0.08)',
                    caretColor: '#00f0ff',
                  }}
                  onFocus={e => e.currentTarget.style.borderColor = 'rgba(0,240,255,0.4)'}
                  onBlur={e => e.currentTarget.style.borderColor = 'rgba(255,255,255,0.08)'}
                />
                <button
                  type="button"
                  onClick={() => setShowPass(!showPass)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[#849495] hover:text-[#dde2f8] transition-colors"
                  tabIndex={-1}
                >
                  <span className="material-symbols-outlined text-[18px]">{showPass ? 'visibility_off' : 'visibility'}</span>
                </button>
              </div>
            </div>

            {/* Submit */}
            <button
              id="login-submit"
              type="submit"
              disabled={loading}
              className="w-full py-3 rounded-lg font-semibold text-sm transition-all duration-200 relative overflow-hidden"
              style={{
                background: loading ? 'rgba(0,240,255,0.1)' : 'linear-gradient(135deg, #00f0ff, #00b8c4)',
                color: '#00363a',
                boxShadow: loading ? 'none' : '0 0 24px rgba(0,240,255,0.25)',
              }}
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-[#00f0ff]/40 border-t-[#00f0ff] rounded-full animate-spin" />
                  Signing in…
                </span>
              ) : 'Sign In'}
            </button>
          </form>

          {/* Divider */}
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-white/5" />
            </div>
            <div className="relative text-center">
              <span className="px-3 text-xs text-[#849495]" style={{ background: 'rgba(25,31,47,0.9)' }}>
                New to Aura?
              </span>
            </div>
          </div>

          <Link
            to="/register"
            id="goto-register"
            className="block w-full py-3 rounded-lg text-sm font-medium text-center transition-all duration-200"
            style={{
              border: '1px solid rgba(87,27,193,0.4)',
              color: '#d0bcff',
              background: 'rgba(87,27,193,0.06)',
            }}
            onMouseEnter={e => {
              (e.currentTarget as HTMLElement).style.background = 'rgba(87,27,193,0.14)';
              (e.currentTarget as HTMLElement).style.borderColor = 'rgba(87,27,193,0.6)';
            }}
            onMouseLeave={e => {
              (e.currentTarget as HTMLElement).style.background = 'rgba(87,27,193,0.06)';
              (e.currentTarget as HTMLElement).style.borderColor = 'rgba(87,27,193,0.4)';
            }}
          >
            Create an account
          </Link>
        </div>

        <p className="text-center text-[#849495] text-xs mt-6">
          Universal Multilingual Voice AI Platform
        </p>
      </div>
    </div>
  );
};
