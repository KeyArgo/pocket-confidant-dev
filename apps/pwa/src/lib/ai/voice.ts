// On-device speech-to-text for low-friction journaling.
//
// PRIVACY NOTE: this uses the browser's Web Speech API (SpeechRecognition).
// IMPORTANT — this is NOT guaranteed to be fully on-device. Several browsers
// (notably Chrome/Chromium) route SpeechRecognition audio to a *cloud* speech
// engine. Only some platforms (e.g. certain Safari/WebKit + on-device dictation
// configurations) keep it local. For a privacy-first product we surface voice as
// a convenience but should label it honestly in the UI as "may use your
// browser's cloud speech service".
//
// TODO(privacy): add a fully-private fallback path that runs Whisper locally via
// transformers.js (@huggingface/transformers, already a dependency) so dictation
// can stay 100% on-device regardless of browser. That path would capture audio
// via getUserMedia + an AudioWorklet and transcribe in a Web Worker. Until then,
// startDictation() relies on the Web Speech API only.

// The Web Speech API is not in the standard TS DOM lib in a portable way, so we
// declare the minimal surface we use.
interface SpeechRecognitionResultLike {
  readonly isFinal: boolean;
  readonly length: number;
  readonly [index: number]: { readonly transcript: string };
}
interface SpeechRecognitionEventLike {
  readonly resultIndex: number;
  readonly results: {
    readonly length: number;
    readonly [index: number]: SpeechRecognitionResultLike;
  };
}
interface SpeechRecognitionLike {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  start(): void;
  stop(): void;
  abort(): void;
  onresult: ((event: SpeechRecognitionEventLike) => void) | null;
  onerror: ((event: { error: string }) => void) | null;
  onend: (() => void) | null;
}
type SpeechRecognitionCtor = new () => SpeechRecognitionLike;

function getRecognitionCtor(): SpeechRecognitionCtor | null {
  const w = globalThis as unknown as {
    SpeechRecognition?: SpeechRecognitionCtor;
    webkitSpeechRecognition?: SpeechRecognitionCtor;
  };
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null;
}

/** True if the current browser exposes the Web Speech API at all. */
export function isVoiceSupported(): boolean {
  return getRecognitionCtor() !== null;
}

/**
 * Start dictation.
 *  - onText: fires with the best-guess partial transcript as the user speaks
 *    (interim results) — use it for a live "listening…" preview.
 *  - onFinal: fires with each finalized chunk of recognized text — append this
 *    to the entry.
 * Returns a stop() function. Call it to end dictation (also safe to call after
 * recognition has already ended). If voice is unsupported, returns a no-op stop
 * and never calls the callbacks.
 */
export function startDictation(
  onText: (partial: string) => void,
  onFinal: (text: string) => void,
): () => void {
  const Ctor = getRecognitionCtor();
  if (!Ctor) {
    return () => {};
  }

  const recognition = new Ctor();
  recognition.lang =
    (globalThis.navigator?.language as string | undefined) ?? "en-US";
  recognition.continuous = true;
  recognition.interimResults = true;

  let stopped = false;

  recognition.onresult = (event: SpeechRecognitionEventLike) => {
    let interim = "";
    for (let i = event.resultIndex; i < event.results.length; i++) {
      const result = event.results[i];
      const transcript = result[0]?.transcript ?? "";
      if (result.isFinal) {
        const finalText = transcript.trim();
        if (finalText) onFinal(finalText);
      } else {
        interim += transcript;
      }
    }
    if (interim.trim()) onText(interim.trim());
  };

  recognition.onend = () => {
    // Auto-restart while the user hasn't pressed stop: continuous mode still
    // ends on its own after pauses in some engines.
    if (!stopped) {
      try {
        recognition.start();
      } catch {
        // already started / not restartable — ignore
      }
    }
  };

  try {
    recognition.start();
  } catch {
    // start() can throw if called twice; treat as already running
  }

  return () => {
    stopped = true;
    try {
      recognition.stop();
    } catch {
      // ignore
    }
  };
}
