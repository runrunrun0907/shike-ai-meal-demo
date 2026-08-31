from __future__ import annotations

import ast
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "app"))

from coze_client import CozeAPIError, run_recognition  # noqa: E402


CASES = [
    {
        "name": "清晰正例",
        "path": "test-image-portfolio/01-clear-positive/clear-balanced-meal.png",
        "analyzable": True,
        "reason": "",
    },
    {
        "name": "复杂食物",
        "path": "test-image-portfolio/02-ambiguous-foods/ambiguous-mixed-stew.png",
        "analyzable": True,
        "reason": "",
    },
    {
        "name": "严重模糊",
        "path": "test-image-portfolio/03-blurred/severely-blurred-meal.png",
        "analyzable": False,
        "reason": "blurred",
    },
    {
        "name": "主体缺失",
        "path": "test-image-portfolio/04-subject-missing/cropped-missing-meal.png",
        "analyzable": False,
        "reason": "subject_missing",
    },
]


def load_local_settings() -> dict[str, str]:
    settings: dict[str, str] = {}
    secrets_path = PROJECT_ROOT / ".streamlit" / "secrets.toml"
    for raw_line in secrets_path.read_text(encoding="utf-8").splitlines():
        if "=" not in raw_line or raw_line.lstrip().startswith("#"):
            continue
        key, raw_value = raw_line.split("=", 1)
        settings[key.strip()] = str(ast.literal_eval(raw_value.strip()))
    return settings


def main() -> int:
    settings = load_local_settings()
    token = settings["COZE_API_TOKEN"]
    workflow_url = settings["COZE_WORKFLOW_URL"]
    passed = 0

    print("餐食识别核心评测")
    for case in CASES:
        image_path = PROJECT_ROOT / case["path"]
        started = time.perf_counter()
        try:
            result = run_recognition(workflow_url, token, image_path.read_bytes(), "image/png")
            elapsed = time.perf_counter() - started
            actual_analyzable = result.get("analyzable")
            actual_reason = result.get("rejection_reason", "")
            ok = actual_analyzable == case["analyzable"] and (
                case["analyzable"] or actual_reason == case["reason"]
            )
            passed += int(ok)
            print(
                f"{'PASS' if ok else 'FAIL'} | {case['name']} | {elapsed:.1f}s | "
                f"analyzable={actual_analyzable} | reason={actual_reason or '-'} | "
                f"foods={len(result.get('foods') or [])} | "
                f"uncertain={len(result.get('uncertain_items') or [])}"
            )
        except (CozeAPIError, ValueError) as exc:
            elapsed = time.perf_counter() - started
            print(f"ERROR | {case['name']} | {elapsed:.1f}s | {exc}")

    print(f"汇总：{passed}/{len(CASES)} 个核心场景通过")
    return 0 if passed == len(CASES) else 1


if __name__ == "__main__":
    raise SystemExit(main())
