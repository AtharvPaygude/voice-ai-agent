import React, { useRef, useEffect, useState } from 'react';
import { useCallStore } from '../../stores/callStore';
import type { SupportedLanguage } from '../../types';
import { getLanguageMeta } from '../../utils/languages';

export const LiveTranscript: React.FC = () => {
  const transcript = useCallStore((state) => state.transcript);
  const interimTranscript = useCallStore((state) => state.interimTranscript);
  const isCallActive = useCallStore((state) => state.isCallActive);
  const startCall = useCallStore((state) => state.startCall);
  const sendMessage = useCallStore((state) => state.sendMessage);

  const [inputVal, setInputVal] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [transcript, interimTranscript]);

  const getLanguageTag = (lang: SupportedLanguage) => {
    const meta = getLanguageMeta(lang);
    let color = 'text-[#7df4ff] bg-[#00363a]/30 border-[#00f0ff]/20';
    if (meta.code === 'hi') color = 'text-[#6ffbbe] bg-[#006d4a]/20 border-[#65f2b5]/30';
    else if (meta.code === 'mr') color = 'text-[#d0bcff] bg-[#571bc1]/20 border-[#8b5cf6]/30';
    else if (meta.code === 'hinglish') color = 'text-[#00f0ff] bg-[#00f0ff]/10 border-[#00f0ff]/30';
    else if (meta.status === 'supported') color = 'text-[#65f2b5] bg-[#65f2b5]/10 border-[#65f2b5]/30';

    return {
      name: meta.name.toUpperCase(),
      flag: meta.flag,
      status: meta.status,
      color,
    };
  };

  const handleSendCustomMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputVal.trim()) return;

    const text = inputVal.trim();
    setInputVal('');

    if (!isCallActive) {
      startCall();
      setTimeout(() => {
        sendMessage(text);
      }, 1000);
    } else {
      sendMessage(text);
    }
  };

  return (
    <div className="glass-panel rounded-xl flex flex-col gradient-border-top h-full min-h-[460px] overflow-hidden">
      {/* Header from Stitch */}
      <div className="p-4 border-b border-white/5 flex justify-between items-center bg-[#191f2f]/60">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 bg-[#00f0ff]/10 px-2 py-0.5 rounded text-[10px] text-[#00f0ff] border border-[#00f0ff]/20 font-mono tracking-wider">
            <span className="material-symbols-outlined text-[12px] animate-spin">sync</span>
            AUTO-SYNC ACTIVE
          </div>
          <h3 className="text-xs font-semibold text-[#dde2f8] font-mono tracking-wide uppercase">Live Transcript</h3>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-mono text-[#65f2b5]">Barge-In: Enabled</span>
        </div>
      </div>

      {/* Chat Messages Stream */}
      <div ref={scrollRef} className="flex-1 p-4 overflow-y-auto flex flex-col gap-4 max-h-[380px]">
        {transcript.map((msg, idx) => {
          const isUser = msg.speaker === 'user';
          const isSystem = msg.speaker === 'system';
          const isBargeIn = Boolean(msg.isInterrupted || msg.text.includes('BARGE-IN'));
          const langTag = getLanguageTag(msg.language);

          if (isBargeIn) {
            return (
              <div key={msg.id || idx} className="w-full flex justify-center my-1">
                <div className="flex items-center gap-2 bg-[#f43f5e]/15 border border-[#f43f5e]/40 px-3 py-1.5 rounded-full text-[11px] font-mono text-[#fda4af] shadow-[0_0_12px_rgba(244,63,94,0.2)]">
                  <span className="material-symbols-outlined text-[14px] text-[#f43f5e] animate-pulse">flash_on</span>
                  <span>{msg.text}</span>
                </div>
              </div>
            );
          }

          if (isSystem) {
            return (
              <div key={msg.id || idx} className="w-full flex justify-center my-0.5">
                <div className="text-[10px] font-mono text-[#849495] bg-[#080e1d]/80 px-2.5 py-0.5 rounded-md border border-white/5">
                  {msg.text}
                </div>
              </div>
            );
          }

          return (
            <div
              key={msg.id || idx}
              className={`flex flex-col gap-1 w-5/6 ${isUser ? 'items-start' : 'items-end self-end'}`}
            >
              {/* Speaker & Language Pill */}
              <div className={`flex items-center gap-2 font-mono text-[10px] uppercase tracking-wider ${
                isUser ? 'text-[#b9cacb] ml-1' : 'text-[#00f0ff] mr-1'
              }`}>
                <span>{isUser ? 'CALLER' : 'AURA AI'}</span>
                <span className={`px-1.5 py-0.2 rounded border ${langTag.color}`}>
                  {langTag.flag} {langTag.name} ({(msg.confidence * 100).toFixed(0)}%)
                </span>
                <span className="text-[#849495]">{msg.timestamp}</span>
              </div>

              {/* Message Bubble */}
              <div
                className={`p-3 rounded-2xl text-xs md:text-sm leading-relaxed border ${
                  isUser
                    ? 'bg-[#2f3445]/70 rounded-tl-sm border-white/5 text-[#dde2f8]'
                    : 'bg-[#00f0ff]/10 rounded-tr-sm border-[#00f0ff]/25 text-[#dbfcff] shadow-[0_0_15px_rgba(0,240,255,0.06)]'
                }`}
              >
                {msg.text}
              </div>
            </div>
          );
        })}

        {/* Real-time Interim Transcription Bubble */}
        {interimTranscript && (
          <div className="flex flex-col gap-1 w-5/6 items-start">
            <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-wider text-[#b9cacb] ml-1">
              <span className="text-[#65f2b5] animate-pulse">LISTENING...</span>
            </div>
            <div className="p-3 rounded-2xl text-xs md:text-sm leading-relaxed border bg-[#2f3445]/40 border-dashed border-[#65f2b5]/40 text-[#dde2f8] italic opacity-85">
              {interimTranscript}
            </div>
          </div>
        )}
      </div>

      {/* Interactive Utterance Input Bar */}
      <form onSubmit={handleSendCustomMessage} className="p-3 bg-[#080e1d]/80 border-t border-white/5 flex gap-2">
        <input
          type="text"
          value={inputVal}
          onChange={(e) => setInputVal(e.target.value)}
          placeholder="Type or simulate speech in English, Hindi, Marathi, or Hinglish..."
          className="flex-1 bg-[#191f2f] border border-white/10 rounded-lg px-3.5 py-2 text-xs font-mono text-[#dde2f8] placeholder:text-[#849495] focus:outline-none focus:border-[#00f0ff]"
        />
        <button
          type="submit"
          className="bg-[#00f0ff] hover:bg-[#7df4ff] text-[#00363a] font-semibold text-xs px-4 py-2 rounded-lg flex items-center gap-1.5 transition-all shadow-[0_0_10px_rgba(0,240,255,0.3)] cursor-pointer"
        >
          <span className="material-symbols-outlined text-[16px]">send</span>
          <span>Send</span>
        </button>
      </form>
    </div>
  );
};
