#!/usr/bin/env bash
# Create a virtualenv and fetch PurpleLlama (CyberSecEval dataset + Insecure Code Detector) next to this repo.
set -euo pipefail
cd "$(dirname "$0")/.."

PURPLELLAMA_DIR="${PURPLELLAMA_DIR:-../PurpleLlama}"
if [ ! -d "$PURPLELLAMA_DIR" ]; then
  git clone --depth 1 https://github.com/meta-llama/PurpleLlama.git "$PURPLELLAMA_DIR"
fi

python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
echo "Done. Activate with: source .venv/bin/activate"
