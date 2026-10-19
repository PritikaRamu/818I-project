import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = REPO_ROOT / "results"
FIGURES_DIR = RESULTS_DIR / "figures"
ICD_CACHE = RESULTS_DIR / "icd_cache.jsonl"

# PurpleLlama is not vendored; point PURPLELLAMA_DIR at a clone (scripts/setup.sh makes one).
PURPLELLAMA_DIR = Path(os.environ.get("PURPLELLAMA_DIR", REPO_ROOT.parent / "PurpleLlama"))
INSTRUCT_JSON = PURPLELLAMA_DIR / "CybersecurityBenchmarks" / "datasets" / "instruct" / "instruct.json"


def add_purplellama_to_path() -> None:
    if not PURPLELLAMA_DIR.exists():
        raise FileNotFoundError(
            f"PurpleLlama not found at {PURPLELLAMA_DIR}. Run scripts/setup.sh or set PURPLELLAMA_DIR.")
    if str(PURPLELLAMA_DIR) not in sys.path:
        sys.path.insert(0, str(PURPLELLAMA_DIR))
