from __future__ import annotations

import ast
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "app"))

from coze_client import CozeAPIError, run_analysis  # noqa: E402


CASES = [
    {
        "name": "结构完整",
        "foods": [
            {"name": "米饭", "category": "主食"},
            {"name": "白切鸡", "category": "蛋白质"},
            {"name": "清炒时蔬", "category": "蔬菜"},
        ],
        "expected": {"staple": "present", "protein": "present", "vegetables": "present"},
        "issues": 0,
    },
    {
        "name": "只有主食",
        "foods": [
            {"name": "白粥", "category": "主食"},
            {"name": "油条", "category": "主食"},
        ],
        "expected": {
            "staple": "present",
            "protein": "not_obvious",
            "vegetables": "not_obvious",
        },
        "issues": 2,
    },
    {
        "name": "缺少主食",
        "foods": [
            {"name": "煮鸡蛋", "category": "蛋白质"},
            {"name": "凉拌黄瓜", "category": "蔬菜"},
        ],
        "expected": {
            "staple": "not_obvious",
            "protein": "present",
            "vegetables": "present",
        },
        "issues": 1,
    },
]

FORBIDDEN_WITHOUT_PORTIONS = ("吃得太多", "摄入过量", "分量合适", "分量不足")


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
    passed = 0

    print("餐食结构分析核心评测")
    for case in CASES:
        started = time.perf_counter()
        try:
            result = run_analysis(
                settings["COZE_ANALYSIS_URL"],
                settings["COZE_API_TOKEN"],
                case["foods"],
            )
            elapsed = time.perf_counter() - started
            structure_ok = result.get("meal_structure") == case["expected"]
            issue_count = len(result.get("main_issues") or [])
            issue_ok = issue_count == case["issues"]
            combined_text = " ".join(
                str(result.get(key, ""))
                for key in ("meal_summary", "main_issues", "suggestions", "friendly_report")
            )
            safety_ok = not any(phrase in combined_text for phrase in FORBIDDEN_WITHOUT_PORTIONS)
            ok = structure_ok and issue_ok and safety_ok
            passed += int(ok)
            print(
                f"{'PASS' if ok else 'FAIL'} | {case['name']} | {elapsed:.1f}s | "
                f"structure={result.get('meal_structure')} | issues={issue_count} | "
                f"suggestions={len(result.get('suggestions') or [])} | safety={safety_ok}"
            )
        except (CozeAPIError, ValueError) as exc:
            elapsed = time.perf_counter() - started
            print(f"ERROR | {case['name']} | {elapsed:.1f}s | {exc}")

    print(f"汇总：{passed}/{len(CASES)} 个分析场景通过")
    return 0 if passed == len(CASES) else 1


if __name__ == "__main__":
    raise SystemExit(main())
