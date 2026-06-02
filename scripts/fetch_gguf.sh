#!/usr/bin/env bash
#
# fetch_gguf.sh — download a small GGUF model into ./models/ for the
# Pocket Confidant Hugging Face Space (the 🦙 Llama Champion path).
#
# We run llama.cpp on the Space via llama-cpp-python (which IS llama.cpp under
# the hood). That needs the model as a local .gguf file. This script fetches it.
#
# It is IDEMPOTENT: already-present, correctly-sized files are skipped, so you
# can re-run it safely. It does NOT download anything unless you ask for a
# specific target (see usage) — no surprise multi-gigabyte pulls.
#
# ---------------------------------------------------------------------------
# USAGE
# ---------------------------------------------------------------------------
#   scripts/fetch_gguf.sh text       # (a) Qwen2.5-7B-Instruct Q4_K_M  (~4.7 GB)
#                                     #     -> the journal companion's chat model
#   scripts/fetch_gguf.sh text-small  # Qwen2.5-3B-Instruct Q4_K_M    (~2.0 GB)
#                                     #     -> phone/low-RAM friendly fallback
#   scripts/fetch_gguf.sh minicpm     # (b) MiniCPM-V-2_6 GGUF + mmproj (~5.5 GB)
#                                     #     -> OpenBMB sponsor / 🎯 special cat;
#                                     #        multimodal, matches LlamaCppBackend
#   scripts/fetch_gguf.sh all         # text + minicpm
#
# The journal companion (engine/confidant.py) only needs a TEXT chat model, so
# `text` is the default pick. `minicpm` is the multimodal model that the
# LlamaCppBackend class in engine/backends.py is wired for (MiniCPMv26ChatHandler
# + mmproj), and it is the play for the OpenBMB sponsor badge.
#
set -euo pipefail

# --- paths -----------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
MODELS_DIR="${REPO_DIR}/models"
mkdir -p "${MODELS_DIR}"

# --- model definitions -----------------------------------------------------
# Format: HF repo id | filename in repo | local filename
#
# Qwen2.5-7B (single-file Q4_K_M from bartowski; the official Qwen GGUF repo
# ships Q4_K_M as a 2-shard split which is awkward for llama-cpp-python, so we
# use bartowski's single, undivided file).
QWEN7B_REPO="bartowski/Qwen2.5-7B-Instruct-GGUF"
QWEN7B_FILE="Qwen2.5-7B-Instruct-Q4_K_M.gguf"

# Qwen2.5-3B — smaller, for phones / <8 GB RAM. Same single-file convention.
QWEN3B_REPO="bartowski/Qwen2.5-3B-Instruct-GGUF"
QWEN3B_FILE="Qwen2.5-3B-Instruct-Q4_K_M.gguf"

# MiniCPM-V-2_6 (OpenBMB) — multimodal. Needs BOTH the model GGUF and its
# mmproj (CLIP vision projector). Filenames are the repo's own conventions.
MINICPM_REPO="openbmb/MiniCPM-V-2_6-gguf"
MINICPM_MODEL_FILE="ggml-model-Q4_K_M.gguf"
MINICPM_MMPROJ_FILE="mmproj-model-f16.gguf"

# --- helpers ---------------------------------------------------------------
have() { command -v "$1" >/dev/null 2>&1; }

# Download one file from a HF repo into MODELS_DIR under a chosen local name.
# Idempotent: if the destination already exists and is non-trivially sized
# (>1 MB, i.e. not a stub/error page), it is skipped.
fetch_one() {
    local repo="$1" remote="$2" local_name="$3"
    local dest="${MODELS_DIR}/${local_name}"

    if [[ -f "${dest}" ]]; then
        local sz
        sz=$(stat -c%s "${dest}" 2>/dev/null || stat -f%z "${dest}" 2>/dev/null || echo 0)
        if [[ "${sz}" -gt 1048576 ]]; then
            echo "  ✓ already present: ${local_name} ($((sz / 1024 / 1024)) MB) — skipping"
            return 0
        fi
        echo "  ! ${local_name} exists but looks truncated (${sz} bytes) — re-downloading"
        rm -f "${dest}"
    fi

    echo "  ↓ fetching ${repo} :: ${remote}"
    echo "      -> ${dest}"

    # Prefer the HF CLI (handles xet-backed repos, resume, auth). It may be the
    # new `hf` binary or the legacy `huggingface-cli`. Fall back to curl.
    if have hf; then
        hf download "${repo}" "${remote}" \
            --local-dir "${MODELS_DIR}" >/dev/null
        # hf download keeps the remote path/name; normalise to local_name.
        [[ -f "${MODELS_DIR}/${remote}" && "${remote}" != "${local_name}" ]] \
            && mv -f "${MODELS_DIR}/${remote}" "${dest}"
    elif have huggingface-cli; then
        huggingface-cli download "${repo}" "${remote}" \
            --local-dir "${MODELS_DIR}" --local-dir-use-symlinks False >/dev/null
        [[ -f "${MODELS_DIR}/${remote}" && "${remote}" != "${local_name}" ]] \
            && mv -f "${MODELS_DIR}/${remote}" "${dest}"
    elif have curl; then
        # -L follow redirects (HF -> xet/CDN), -C - resume partial downloads,
        # -f fail loudly on HTTP errors instead of saving an error page.
        curl -fL -C - \
            "https://huggingface.co/${repo}/resolve/main/${remote}?download=true" \
            -o "${dest}"
    else
        echo "ERROR: need one of: hf, huggingface-cli, or curl" >&2
        exit 1
    fi

    echo "  ✓ done: ${local_name}"
}

# --- targets ---------------------------------------------------------------
fetch_text()       { echo "[text] Qwen2.5-7B-Instruct (journal companion chat model)";  fetch_one "${QWEN7B_REPO}"  "${QWEN7B_FILE}"  "${QWEN7B_FILE}"; }
fetch_text_small() { echo "[text-small] Qwen2.5-3B-Instruct (phone/low-RAM fallback)";  fetch_one "${QWEN3B_REPO}"  "${QWEN3B_FILE}"  "${QWEN3B_FILE}"; }
fetch_minicpm()    {
    echo "[minicpm] MiniCPM-V-2_6 GGUF + mmproj (OpenBMB sponsor / multimodal)"
    fetch_one "${MINICPM_REPO}" "${MINICPM_MODEL_FILE}"  "minicpm-v-2_6-Q4_K_M.gguf"
    fetch_one "${MINICPM_REPO}" "${MINICPM_MMPROJ_FILE}" "minicpm-v-2_6-mmproj-f16.gguf"
}

# --- next-steps banner -----------------------------------------------------
print_next_steps() {
    cat <<EOF

--------------------------------------------------------------------------
Done. Models are in: ${MODELS_DIR}
$(ls -lh "${MODELS_DIR}"/*.gguf 2>/dev/null | awk '{print "  " $9 "  (" $5 ")"}' || echo "  (no .gguf yet)")

Next steps:
  1) Install the Space runtime (llama.cpp via llama-cpp-python):
         pip install "llama-cpp-python>=0.3.2"      # CPU
       or with CUDA (RTX 4070 Ti):
         CMAKE_ARGS="-DGGML_CUDA=on" pip install "llama-cpp-python>=0.3.2"
     See apps/confidant/LLAMACPP.md for the full guide.

  2) Point the companion at the GGUF. For the TEXT journal model that is the
     simplest path — load Qwen2.5-7B-Instruct-Q4_K_M.gguf and use it as the
     chat model behind confidant.reflect (details in LLAMACPP.md).

  3) For the MULTIMODAL MiniCPM path, engine/backends.py LlamaCppBackend takes
     model_path + mmproj_path:
         LlamaCppBackend(
             model_path="${MODELS_DIR}/minicpm-v-2_6-Q4_K_M.gguf",
             mmproj_path="${MODELS_DIR}/minicpm-v-2_6-mmproj-f16.gguf",
         )

Note: .gguf files are gitignored — they are NOT committed. On the HF Space,
either run this script in the build, or attach the GGUF as a Space file/LFS.
--------------------------------------------------------------------------
EOF
}

# --- dispatch --------------------------------------------------------------
TARGET="${1:-text}"

case "${TARGET}" in
    -h|--help|help)
        sed -n '2,30p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
        exit 0
        ;;
esac

echo "fetch_gguf.sh — target: ${TARGET}"
echo "models dir:    ${MODELS_DIR}"
echo

case "${TARGET}" in
    text)        fetch_text ;;
    text-small)  fetch_text_small ;;
    minicpm)     fetch_minicpm ;;
    all)         fetch_text; echo; fetch_minicpm ;;
    *)
        echo "Unknown target: ${TARGET}" >&2
        echo "Use one of: text | text-small | minicpm | all   (or --help)" >&2
        exit 1
        ;;
esac

print_next_steps
