/**
 * Audio Manager for Aura Voice AI.
 * Handles Web Audio API microphone volume analysis and simulated AI speech waves.
 */

let audioCtx: AudioContext | null = null;
let micStream: MediaStream | null = null;
let micSource: MediaStreamAudioSourceNode | null = null;
let micAnalyser: AnalyserNode | null = null;
let micAnimationFrame: number | null = null;

let ttsInterval: any = null;

export const startMicAnalysis = async (onAudioLevel: (level: number) => void, stream?: MediaStream) => {
  try {
    // 1. Request microphone permission with echo cancellation, noise suppression, and AGC
    micStream = stream || await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      },
      video: false,
    });

    // 2. Initialize AudioContext and Analyser
    audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
    micSource = audioCtx.createMediaStreamSource(micStream);
    micAnalyser = audioCtx.createAnalyser();
    micAnalyser.fftSize = 256;
    
    micSource.connect(micAnalyser);

    const bufferLength = micAnalyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    // 3. Animation loop to check volume level
    const analyze = () => {
      if (!micAnalyser) return;
      
      micAnalyser.getByteTimeDomainData(dataArray);

      // Compute Root Mean Square (RMS) for volume level
      let total = 0;
      for (let i = 0; i < bufferLength; i++) {
        const value = (dataArray[i] - 128) / 128; // Normalize to -1..1
        total += value * value;
      }
      
      const rms = Math.sqrt(total / bufferLength);
      // Amplify and clamp between 0 and 1
      const normalizedLevel = Math.min(1, Math.max(0, rms * 5.0));
      
      onAudioLevel(normalizedLevel);
      micAnimationFrame = requestAnimationFrame(analyze);
    };

    analyze();
  } catch (err) {
    console.error("Failed to initialize microphone analysis:", err);
    onAudioLevel(0);
  }
};

export const stopMicAnalysis = () => {
  // Cancel animation frame
  if (micAnimationFrame !== null) {
    cancelAnimationFrame(micAnimationFrame);
    micAnimationFrame = null;
  }

  // Stop media tracks
  if (micStream) {
    micStream.getTracks().forEach((track) => track.stop());
    micStream = null;
  }

  // Disconnect audio nodes
  if (micSource) {
    micSource.disconnect();
    micSource = null;
  }

  if (micAnalyser) {
    micAnalyser = null;
  }

  if (audioCtx && audioCtx.state !== "closed") {
    audioCtx.close();
    audioCtx = null;
  }
};

export const startSpeechAnalysis = (onAudioLevel: (level: number) => void) => {
  // Clear any existing TTS visualizer simulation
  if (ttsInterval) clearInterval(ttsInterval);

  let time = 0;
  
  // Generate a dynamic, audio-reactive waveform for TTS feedback
  ttsInterval = setInterval(() => {
    time += 0.2;
    // Layered sines to look like natural human voice envelope
    const baseWave = Math.sin(time) * 0.4 + Math.sin(time * 2.3) * 0.25;
    const noise = Math.random() * 0.15;
    // Add syllable peaks (envelope simulation)
    const envelope = Math.max(0, Math.sin(time * 0.4) * 0.8 + 0.2);
    
    const level = Math.min(1, Math.max(0, (Math.abs(baseWave) + noise) * envelope));
    onAudioLevel(level * 0.85); // Moderate volume scaling for aesthetics
  }, 50);
};

export const stopSpeechAnalysis = () => {
  if (ttsInterval) {
    clearInterval(ttsInterval);
    ttsInterval = null;
  }
};

// ─── Server-side voice pipeline: recording + real audio playback ──────────
//
// The functions above (startMicAnalysis/startSpeechAnalysis) power the
// browser-native pipeline (SpeechRecognition + SpeechSynthesis + a simulated
// waveform for the orb). The functions below are for the newer server-side
// pipeline: they record real mic audio to stream to the backend for
// faster-whisper transcription, and play back the real MP3 bytes the
// backend sends from edge-tts — with the orb driven by the *actual* audio
// levels of that playback, not a simulated sine wave.

// ─── Server-side voice pipeline: recording + real audio playback ──────────
//
// The functions above (startMicAnalysis/startSpeechAnalysis) power the
// browser-native pipeline (SpeechRecognition + SpeechSynthesis + a simulated
// waveform for the orb). The functions below are for the newer server-side
// pipeline: they record real mic audio to stream to the backend for
// faster-whisper transcription, and play back the real MP3 bytes the
// backend sends from edge-tts — with the orb driven by the *actual* audio
// levels of that playback, not a simulated sine wave.

let mediaRecorder: MediaRecorder | null = null;
let recordingStream: MediaStream | null = null;
let pendingChunkPromises: Promise<void>[] = [];

/**
 * Get or initialize persistent MediaStream for the microphone.
 * Avoids repeated teardown and re-acquisition of mic hardware between turns.
 */
export const getOrCreateMicStream = async (): Promise<MediaStream> => {
  if (
    recordingStream &&
    recordingStream.active &&
    recordingStream.getAudioTracks().some((t) => t.readyState === 'live')
  ) {
    return recordingStream;
  }

  console.log('[AUDIO CAPTURE] Requesting microphone permission and initializing stream...');
  recordingStream = await navigator.mediaDevices.getUserMedia({
    audio: {
      echoCancellation: true,
      noiseSuppression: true,
      autoGainControl: true,
      channelCount: 1,
    },
    video: false,
  });
  console.log('[AUDIO CAPTURE] Microphone stream acquired successfully.');
  return recordingStream;
};

/** Release persistent microphone stream tracks on call end. */
export const releaseMicStream = (): void => {
  if (recordingStream) {
    console.log('[AUDIO CAPTURE] Releasing microphone tracks.');
    recordingStream.getTracks().forEach((track) => track.stop());
    recordingStream = null;
  }
};

/**
 * Start recording microphone audio and stream it out in chunks via
 * onChunk (each chunk is raw bytes ready to send as a WebSocket binary
 * frame). Call stopVoiceRecording() to finish the utterance.
 */
export const startVoiceRecording = async (onChunk: (chunk: ArrayBuffer) => void): Promise<MediaStream> => {
  // Ensure previous recorder is stopped first
  await stopVoiceRecording();

  const stream = await getOrCreateMicStream();

  const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
    ? 'audio/webm;codecs=opus'
    : MediaRecorder.isTypeSupported('audio/webm')
    ? 'audio/webm'
    : 'audio/mp4';

  console.log(`[AUDIO CAPTURE] Initializing MediaRecorder with mimeType='${mimeType}'`);
  mediaRecorder = new MediaRecorder(stream, { mimeType });
  pendingChunkPromises = [];

  mediaRecorder.ondataavailable = (event: BlobEvent) => {
    if (event.data && event.data.size > 0) {
      console.log(`[AUDIO CAPTURE] Audio chunk available: ${event.data.size} bytes`);
      const p = event.data.arrayBuffer().then((buffer) => {
        onChunk(buffer);
      }).catch((e) => {
        console.error('[AUDIO CAPTURE] Error converting chunk to arrayBuffer:', e);
      });
      pendingChunkPromises.push(p);
    }
  };

  // Emit a chunk every 250ms so the backend buffer fills progressively
  mediaRecorder.start(250);
  console.log('[AUDIO CAPTURE] MediaRecorder started listening.');
  return stream;
};

/** Stop recording and ensure all pending audio chunks have been dispatched. */
export const stopVoiceRecording = async (): Promise<void> => {
  const recorder = mediaRecorder;
  if (!recorder || recorder.state === 'inactive') {
    mediaRecorder = null;
    return;
  }

  console.log('[AUDIO CAPTURE] Stopping MediaRecorder...');
  await new Promise<void>((resolve) => {
    recorder.addEventListener('stop', () => resolve(), { once: true });
    try {
      recorder.stop();
    } catch (_) {
      resolve();
    }
  });

  // Await all in-flight arrayBuffer conversions so final audio is sent before voice_input
  if (pendingChunkPromises.length > 0) {
    await Promise.all(pendingChunkPromises);
    pendingChunkPromises = [];
    console.log('[AUDIO CAPTURE] All audio chunks flushed.');
  }

  mediaRecorder = null;
};

// ─── Synthesized audio sequential queue with shared AudioContext ──────────

let sharedAudioCtx: AudioContext | null = null;
let sharedAnalyser: AnalyserNode | null = null;

const getSharedAudioContext = (): { ctx: AudioContext; analyser: AnalyserNode } => {
  if (!sharedAudioCtx || sharedAudioCtx.state === 'closed') {
    sharedAudioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
    sharedAnalyser = sharedAudioCtx.createAnalyser();
    sharedAnalyser.fftSize = 256;
  }
  if (sharedAudioCtx.state === 'suspended') {
    sharedAudioCtx.resume().catch(() => {});
  }
  return { ctx: sharedAudioCtx, analyser: sharedAnalyser! };
};

interface QueuedAudio {
  bytes: ArrayBuffer;
  onLevel?: (level: number) => void;
  onDrained?: () => void;
}

const audioQueue: QueuedAudio[] = [];
let isPlaying = false;
let currentPlaybackAudio: HTMLAudioElement | null = null;
let currentObjectUrl: string | null = null;
let playbackAnimationFrame: number | null = null;
let lastOnDrained: (() => void) | null = null;

const playNextInQueue = () => {
  if (audioQueue.length === 0) {
    isPlaying = false;
    if (playbackAnimationFrame !== null) {
      cancelAnimationFrame(playbackAnimationFrame);
      playbackAnimationFrame = null;
    }
    const drained = lastOnDrained;
    lastOnDrained = null;
    console.log('[AUDIO PLAYBACK] All queued audio clips completed.');
    if (drained) drained();
    return;
  }

  isPlaying = true;
  const item = audioQueue.shift()!;
  if (item.onDrained) {
    lastOnDrained = item.onDrained;
  }

  console.log(`[AUDIO PLAYBACK] Playing audio chunk (${item.bytes.byteLength} bytes). Remaining in queue: ${audioQueue.length}`);
  const blob = new Blob([item.bytes], { type: 'audio/mpeg' });
  const url = URL.createObjectURL(blob);
  currentObjectUrl = url;
  const audioEl = new Audio(url);
  currentPlaybackAudio = audioEl;

  const { ctx, analyser } = getSharedAudioContext();
  if (ctx.state === 'suspended') {
    ctx.resume().catch((err) => console.warn('[AUDIO PLAYBACK] AudioContext resume failed:', err));
  }

  let source: MediaElementAudioSourceNode | null = null;
  try {
    source = ctx.createMediaElementSource(audioEl);
    source.connect(analyser);
    analyser.connect(ctx.destination);
  } catch (_) {
    // Reuse existing connection if already attached
  }

  const bufferLength = analyser.frequencyBinCount;
  const dataArray = new Uint8Array(bufferLength);

  const analyze = () => {
    if (!isPlaying) return;
    analyser.getByteTimeDomainData(dataArray);
    let total = 0;
    for (let i = 0; i < bufferLength; i++) {
      const value = (dataArray[i] - 128) / 128;
      total += value * value;
    }
    const rms = Math.sqrt(total / bufferLength);
    if (item.onLevel) {
      item.onLevel(Math.min(1, Math.max(0, rms * 5.0)));
    }
    playbackAnimationFrame = requestAnimationFrame(analyze);
  };

  const cleanup = () => {
    if (playbackAnimationFrame !== null) {
      cancelAnimationFrame(playbackAnimationFrame);
      playbackAnimationFrame = null;
    }
    if (currentObjectUrl) {
      URL.revokeObjectURL(currentObjectUrl);
      currentObjectUrl = null;
    }
    try {
      source?.disconnect();
    } catch (_) {}
    if (item.onLevel) item.onLevel(0);
    currentPlaybackAudio = null;
    playNextInQueue();
  };

  audioEl.onended = cleanup;
  audioEl.onerror = cleanup;

  audioEl.play().then(() => {
    if (playbackAnimationFrame !== null) cancelAnimationFrame(playbackAnimationFrame);
    playbackAnimationFrame = requestAnimationFrame(analyze);
  }).catch((err) => {
    console.error('Failed to play synthesized audio:', err);
    cleanup();
  });
};

/**
 * Enqueue synthesized audio clip (MP3 bytes) for sequential playback.
 * Triggers onDrained when all queued clips finish playing.
 */
export const enqueueSynthesizedAudio = (
  bytes: ArrayBuffer,
  onLevel?: (level: number) => void,
  onDrained?: () => void
): void => {
  audioQueue.push({ bytes, onLevel, onDrained });
  if (!isPlaying) {
    playNextInQueue();
  }
};

/**
 * Play back synthesized speech audio with audio level reaction.
 * Wrapper around enqueueSynthesizedAudio for backward compatibility.
 */
export const playSynthesizedAudio = (
  audioBytes: ArrayBuffer,
  onAudioLevel: (level: number) => void,
  onEnd: () => void
): void => {
  enqueueSynthesizedAudio(audioBytes, onAudioLevel, onEnd);
};

/** Stop any in-progress synthesized audio playback and clear queue. */
export const stopSynthesizedAudioPlayback = (): void => {
  audioQueue.length = 0;
  lastOnDrained = null;
  isPlaying = false;
  if (currentPlaybackAudio) {
    currentPlaybackAudio.pause();
    currentPlaybackAudio = null;
  }
  if (currentObjectUrl) {
    URL.revokeObjectURL(currentObjectUrl);
    currentObjectUrl = null;
  }
  if (playbackAnimationFrame !== null) {
    cancelAnimationFrame(playbackAnimationFrame);
    playbackAnimationFrame = null;
  }
};
