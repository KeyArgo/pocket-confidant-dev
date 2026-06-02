// On-device chat via WebLLM (MLC) over WebGPU. Models are cached in the browser's
// Cache Storage after first download — nothing leaves the device, works offline.

import {
  CreateMLCEngine,
  type MLCEngine,
  type InitProgressReport,
} from "@mlc-ai/web-llm";
import type { Chat } from "../core/types";

// Default = a warm ~1.5B model; fallback = a tiny ~0.5B for low-VRAM/low-bandwidth.
export const DEFAULT_MODEL = "Qwen2.5-1.5B-Instruct-q4f16_1-MLC";
export const SMALL_MODEL = "Qwen2.5-0.5B-Instruct-q4f16_1-MLC";
export const LARGER_MODEL = "gemma-2-2b-it-q4f16_1-MLC";

export const MODELS = [DEFAULT_MODEL, LARGER_MODEL, SMALL_MODEL];

export function hasWebGPU(): boolean {
  return typeof navigator !== "undefined" && "gpu" in navigator;
}

let engine: MLCEngine | null = null;
let loadedModel: string | null = null;

/** Load (or switch) the chat model, reporting download progress for onboarding UX. */
export async function loadModel(
  model: string = DEFAULT_MODEL,
  onProgress?: (report: InitProgressReport) => void,
): Promise<void> {
  if (engine && loadedModel === model) return;
  if (!hasWebGPU()) {
    throw new Error(
      "This browser has no WebGPU, so on-device reflections aren't available. Journaling and ‘ask your journal’ still work.",
    );
  }
  engine = await CreateMLCEngine(model, {
    initProgressCallback: onProgress,
  });
  loadedModel = model;
}

export function currentModel(): string | null {
  return loadedModel;
}

/** Chat transport matching the core's `Chat` type. */
export const chat: Chat = async (system, user, opts = {}) => {
  if (!engine) throw new Error("Model not loaded yet.");
  const reply = await engine.chat.completions.create({
    messages: [
      { role: "system", content: system },
      { role: "user", content: user },
    ],
    temperature: opts.temperature ?? 0.7,
  });
  return reply.choices[0]?.message?.content ?? "";
};
