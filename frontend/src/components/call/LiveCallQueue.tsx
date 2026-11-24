import React from 'react';
import { useCallStore } from '../../stores/callStore';

export const LiveCallQueue: React.FC = () => {
  const isCallActive = useCallStore((state) => state.isCallActive);

  return (
    <div className="flex flex-col gap-4">
      {/* Live Call Queue Card from Stitch */}
      <div className="glass-panel rounded-xl p-5 gradient-border-top flex flex-col">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-xs font-semibold text-[#dde2f8] flex items-center gap-2 tracking-wide uppercase font-mono">
            <span className="material-symbols-outlined text-[#00f0ff] text-[18px]">phone_in_talk</span>
            Live Call Queue
          </h3>
          <div className="bg-[#2f3445] px-2.5 py-0.5 rounded-full border border-white/5 flex items-center gap-1.5">
            <div className="w-1.5 h-1.5 rounded-full bg-[#ffb4ab] animate-pulse"></div>
            <span className="font-mono text-[11px] text-[#b9cacb]">4 Waiting</span>
          </div>
        </div>

        <div className="flex flex-col gap-2.5">
          {/* Active Call Item */}
          <div className={`rounded-lg p-3 border transition-all flex justify-between items-center ${
            isCallActive 
              ? 'bg-[#00f0ff]/10 border-[#00f0ff]/40 shadow-[0_0_15px_rgba(0,240,255,0.1)]' 
              : 'bg-[#2f3445]/40 border-white/5'
          }`}>
            <div className="flex items-center gap-3">
              <div className="w-7 h-7 rounded bg-[#151b2b] flex items-center justify-center font-mono text-[11px] text-[#00f0ff] font-bold border border-[#00f0ff]/20">
                01
              </div>
              <div>
                <div className="font-mono text-xs text-[#dde2f8] font-medium">+91 98230 48192</div>
                <div className="text-[10px] text-[#65f2b5] flex items-center gap-1 uppercase tracking-wider font-mono">
                  <span className="material-symbols-outlined text-[12px]">graphic_eq</span> 
                  {isCallActive ? 'Connected (Voice)' : 'On Hold'}
                </div>
              </div>
            </div>
            <div className="font-mono text-xs text-[#00f0ff] font-medium">02:14</div>
          </div>

          {/* Caller Item 2 */}
          <div className="bg-[#2f3445]/30 rounded-lg p-3 border border-white/5 hover:border-[#00f0ff]/30 transition-colors flex justify-between items-center cursor-pointer">
            <div className="flex items-center gap-3">
              <div className="w-7 h-7 rounded bg-[#151b2b] flex items-center justify-center font-mono text-[11px] text-[#b9cacb]">
                02
              </div>
              <div>
                <div className="font-mono text-xs text-[#dde2f8]">+1 (555) 819-283</div>
                <div className="text-[10px] text-[#00f0ff] flex items-center gap-1 uppercase tracking-wider font-mono">
                  <span className="material-symbols-outlined text-[12px]">route</span> Routing
                </div>
              </div>
            </div>
            <div className="font-mono text-xs text-[#b9cacb]">01:45</div>
          </div>

          {/* Caller Item 3 */}
          <div className="bg-[#2f3445]/30 rounded-lg p-3 border border-white/5 hover:border-[#00f0ff]/30 transition-colors flex justify-between items-center cursor-pointer">
            <div className="flex items-center gap-3">
              <div className="w-7 h-7 rounded bg-[#151b2b] flex items-center justify-center font-mono text-[11px] text-[#b9cacb]">
                03
              </div>
              <div>
                <div className="font-mono text-xs text-[#dde2f8]">+44 20 7946 09</div>
                <div className="text-[10px] text-[#849495] flex items-center gap-1 uppercase tracking-wider font-mono">
                  <span className="material-symbols-outlined text-[12px]">hourglass_empty</span> Waiting
                </div>
              </div>
            </div>
            <div className="font-mono text-xs text-[#849495]">00:38</div>
          </div>
        </div>
      </div>

      {/* Active Agents List from Stitch */}
      <div className="glass-panel rounded-xl p-5 gradient-border-top">
        <div className="flex justify-between items-center mb-3 border-b border-white/10 pb-2.5">
          <h3 className="text-xs font-semibold text-[#dde2f8] uppercase font-mono tracking-wide">Active Agents</h3>
          <span className="font-mono text-[11px] text-[#00f0ff] font-medium">12 Online</span>
        </div>
        <div className="flex flex-col gap-3 pt-1">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-[#65f2b5] shadow-[0_0_8px_rgba(101,242,181,0.6)]"></div>
              <span className="font-mono text-xs text-[#dde2f8]">Multilingual Sales Bot</span>
            </div>
            <span className="text-[10px] uppercase tracking-wider text-[#65f2b5] font-mono">Active</span>
          </div>

          <div className="flex justify-between items-center">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-[#00f0ff] shadow-[0_0_8px_rgba(0,240,255,0.6)]"></div>
              <span className="font-mono text-xs text-[#dde2f8]">Support Bot Alpha</span>
            </div>
            <span className="text-[10px] uppercase tracking-wider text-[#00f0ff] font-mono">Active</span>
          </div>

          <div className="flex justify-between items-center">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-[#849495]"></div>
              <span className="font-mono text-xs text-[#b9cacb]">Billing Escalation</span>
            </div>
            <span className="text-[10px] uppercase tracking-wider text-[#849495] font-mono">Idle</span>
          </div>
        </div>
      </div>
    </div>
  );
};
