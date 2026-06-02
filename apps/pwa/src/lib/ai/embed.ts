// On-device embeddings via Transformers.js. Small (~90MB) all-MiniLM-L6-v2, 384-dim,
// runs on WebGPU where available and falls back to WASM — so semantic recall and
// "ask your journal" work even on browsers without WebGPU (where chat is disabled).

import { pipeline, env } from "@huggingface/transformers";
import type { Embedder } from "../core/types";

// Cache models in the browser; never hit a server after first load.
env.allowLocalModels = false;

const EMBED_MODEL = "Xenova/all-MiniLM-L6-v2";

type FeatureExtractor = (
  text: string,
  opts: { pooling: "mean"; normalize: boolean },
) => Promise<{ data: Float32Array | number[] }>;

let extractorPromise: Promise<FeatureExtractor> | null = null;

async function getExtractor(
  onProgress?: (p: { progress?: number; status?: string }) => void,
): Promise<FeatureExtractor> {
  if (!extractorPromise) {
    extractorPromise = (async () => {
      const device =
        typeof navigator !== "undefined" && "gpu" in navigator
          ? "webgpu"
          : "wasm";
      const pipe = await pipeline("feature-extraction", EMBED_MODEL, {
        device: device as "webgpu" | "wasm",
        progress_callback: onProgress as never,
      });
      return pipe as unknown as FeatureExtractor;
    })();
  }
  return extractorPromise;
}

/** Warm up the embedder (call during onboarding). */
export async function initEmbedder(
  onProgress?: (p: { progress?: number; status?: string }) => void,
): Promise<void> {
  await getExtractor(onProgress);
}

/** Embed text to a normalized 384-dim vector, fully on-device. */
export const embed: Embedder = async (text: string): Promise<number[]> => {
  const extractor = await getExtractor();
  const out = await extractor(text, { pooling: "mean", normalize: true });
  return Array.from(out.data as ArrayLike<number>);
};
