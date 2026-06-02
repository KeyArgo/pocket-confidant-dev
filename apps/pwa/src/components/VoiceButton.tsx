// Mic button that dictates into an entry. Presentational: it owns only its own
// recording state and hands recognized text back to the parent via onText.
// Sits next to the entry textarea on the write screen.

import { useEffect, useRef, useState } from "react";
import { startDictation, isVoiceSupported } from "../lib/ai/voice";

export interface VoiceButtonProps {
  /** Called with each finalized chunk of dictated text, to append to the entry. */
  onText: (text: string) => void;
}

export default function VoiceButton({ onText }: VoiceButtonProps) {
  const supported = isVoiceSupported();
  const [recording, setRecording] = useState(false);
  const [partial, setPartial] = useState("");
  const stopRef = useRef<(() => void) | null>(null);

  // Stop dictation if the component unmounts mid-recording.
  useEffect(() => {
    return () => {
      stopRef.current?.();
    };
  }, []);

  if (!supported) {
    return (
      <button
        type="button"
        className="quiet"
        disabled
        title="Voice input isn't available in this browser"
        aria-label="Voice input unavailable"
      >
        🎙 n/a
      </button>
    );
  }

  function toggle() {
    if (recording) {
      stopRef.current?.();
      stopRef.current = null;
      setRecording(false);
      setPartial("");
      return;
    }
    setRecording(true);
    setPartial("");
    stopRef.current = startDictation(
      (p) => setPartial(p),
      (text) => {
        onText(text);
        setPartial("");
      },
    );
  }

  return (
    <span className="voice">
      <button
        type="button"
        className={recording ? "primary recording" : "quiet"}
        onClick={toggle}
        aria-pressed={recording}
        aria-label={recording ? "Stop dictation" : "Start dictation"}
        title={
          recording
            ? "Stop dictation"
            : "Dictate (may use your browser's cloud speech service)"
        }
      >
        {recording ? "● Listening…" : "🎙 Speak"}
      </button>
      {partial && (
        <span className="hint voice-partial" aria-live="polite">
          {partial}
        </span>
      )}
    </span>
  );
}
