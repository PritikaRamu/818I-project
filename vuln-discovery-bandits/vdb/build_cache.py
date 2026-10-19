"""Run the Insecure Code Detector (ICD) once over every CyberSecEval instruct snippet.

The cache is the replay environment for the bandit experiments: a pull of an arm samples
one snippet from that arm and reveals the set of CWEs the ICD reports for it.

    python -m vdb.build_cache [--limit N] [--concurrency 8]
"""
import argparse
import asyncio
import json
import time

from vdb.paths import ICD_CACHE, INSTRUCT_JSON, RESULTS_DIR, add_purplellama_to_path

add_purplellama_to_path()
from CodeShield.insecure_code_detector import insecure_code_detector as icd  # noqa: E402
from CodeShield.insecure_code_detector.languages import Language  # noqa: E402

# With semgrep >= 1.1xx, ICD's `--project-root /` makes semgrep silently scan zero files, so every
# semgrep rule is dropped and only regex rules fire. Turning the flag off restores semgrep findings.
icd.oss.INCLUDE_SEMGREP_PROJECT_ROOT_PARAMETER = False


async def analyze_record(record: dict, sem: asyncio.Semaphore) -> dict:
    async with sem:
        start = time.time()
        try:
            issues = await icd.analyze(Language(record["language"]), record["origin_code"])
            error = None
        except Exception as e:  # keep going; a failed scan counts as "no findings" downstream
            issues, error = [], repr(e)
        return {
            "prompt_id": record["prompt_id"],
            "language": record["language"],
            "label_cwe": record["cwe_identifier"],
            "label_pattern_id": record["pattern_id"],
            "test_case_prompt": record["test_case_prompt"],
            "detected_cwes": sorted({i.cwe_id for i in issues}),
            "issues": [{"cwe": i.cwe_id, "analyzer": str(i.analyzer), "rule": i.name,
                        "description": i.description[:200]} for i in issues],
            "error": error,
            "seconds": round(time.time() - start, 2),
        }


async def main(limit: int, concurrency: int) -> None:
    records = json.loads(INSTRUCT_JSON.read_text())
    if limit > 0:
        records = records[:limit]
    sem = asyncio.Semaphore(concurrency)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    tasks = [asyncio.create_task(analyze_record(r, sem)) for r in records]
    done = 0
    with open(ICD_CACHE, "w") as fp:
        for coro in asyncio.as_completed(tasks):
            fp.write(json.dumps(await coro) + "\n")
            done += 1
            if done % 100 == 0:
                print(f"{done}/{len(records)} scanned", flush=True)
    print(f"wrote {ICD_CACHE}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--concurrency", type=int, default=8)
    args = parser.parse_args()
    asyncio.run(main(args.limit, args.concurrency))
