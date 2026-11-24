import React from 'react';
import { useCallStore } from '../../stores/callStore';

export const SentimentPanel: React.FC = () => {
  const currentLanguage = useCallStore((state) => state.currentLanguage);
  const metrics = useCallStore((state) => state.metrics);

  return (
    <div className="glass-panel rounded-xl p-5 gradient-border-top flex flex-col gap-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-[#571bc1]/20 flex items-center justify-center border border-[#8b5cf6]/30">
            <span className="material-symbols-outlined text-[#d0bcff] text-[18px]">sentiment_satisfied</span>
          </div>
          <div>
            <h3 className="text-xs font-semibold text-[#dde2f8] font-mono tracking-wide uppercase">Real-time Sentiment</h3>
            <p className="text-[10px] font-mono text-[#b9cacb]">Lead Score: <span className="text-[#00f0ff] font-bold">{metrics.leadScore}/100</span></p>
          </div>
        </div>
        <span className="px-2 py-0.5 rounded bg-[#65f2b5]/10 border border-[#65f2b5]/30 text-[#65f2b5] font-mono text-[10px] uppercase font-bold">
          {metrics.sentiment} ({(metrics.sentimentScore * 100).toFixed(0)}%)
        </span>
      </div>

      {/* Language Dialect Distribution Bars from Stitch */}
      <div className="flex flex-col gap-3 pt-1">
        {/* Hinglish Bar */}
        <div>
          <div className="flex justify-between font-mono text-[11px] mb-1">
            <span className={currentLanguage === 'hinglish' ? 'text-[#00f0ff] font-bold' : 'text-[#dde2f8]'}>
              Hinglish {currentLanguage === 'hinglish' && '• (Active)'}
            </span>
            <span className="text-[#00f0ff] font-semibold">45%</span>
          </div>
          <div className="w-full bg-[#2f3445] rounded-full h-1.5 overflow-hidden">
            <div className="bg-[#00f0ff] h-1.5 rounded-full shadow-[0_0_10px_rgba(0,240,255,0.5)] transition-all duration-500" style={{ width: '45%' }}></div>
          </div>
        </div>

        {/* English Bar */}
        <div>
          <div className="flex justify-between font-mono text-[11px] mb-1">
            <span className={currentLanguage === 'en' ? 'text-[#7df4ff] font-bold' : 'text-[#b9cacb]'}>
              English {currentLanguage === 'en' && '• (Active)'}
            </span>
            <span className="text-[#7df4ff] font-semibold">38%</span>
          </div>
          <div className="w-full bg-[#2f3445] rounded-full h-1.5 overflow-hidden">
            <div className="bg-[#7df4ff] h-1.5 rounded-full transition-all duration-500" style={{ width: '38%' }}></div>
          </div>
        </div>

        {/* Hindi Bar */}
        <div>
          <div className="flex justify-between font-mono text-[11px] mb-1">
            <span className={currentLanguage === 'hi' ? 'text-[#6ffbbe] font-bold' : 'text-[#b9cacb]'}>
              Hindi {currentLanguage === 'hi' && '• (Active)'}
            </span>
            <span className="text-[#6ffbbe] font-semibold">15%</span>
          </div>
          <div className="w-full bg-[#2f3445] rounded-full h-1.5 overflow-hidden">
            <div className="bg-[#65f2b5] h-1.5 rounded-full transition-all duration-500" style={{ width: '15%' }}></div>
          </div>
        </div>

        {/* Marathi Bar */}
        <div>
          <div className="flex justify-between font-mono text-[11px] mb-1">
            <span className={currentLanguage === 'mr' ? 'text-[#d0bcff] font-bold' : 'text-[#b9cacb]'}>
              Marathi {currentLanguage === 'mr' && '• (Active)'}
            </span>
            <span className="text-[#d0bcff] font-semibold">10%</span>
          </div>
          <div className="w-full bg-[#2f3445] rounded-full h-1.5 overflow-hidden">
            <div className="bg-[#8b5cf6] h-1.5 rounded-full transition-all duration-500" style={{ width: '10%' }}></div>
          </div>
        </div>
      </div>
    </div>
  );
};
