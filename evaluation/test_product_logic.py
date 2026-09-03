from __future__ import annotations

import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "app"))

from product_logic import (  # noqa: E402
    analysis_payload,
    build_knowledge_tips,
    build_meal_composition,
    build_meal_report,
    build_risk_alerts,
    build_structure_summary,
    category_evidence,
    ensure_sentence,
    infer_food_categories,
    merge_recognition_results,
    normalize_foods,
)


class ProductLogicTests(unittest.TestCase):
    def test_multiple_recognition_results_are_merged_without_duplicate_foods(self) -> None:
        merged = merge_recognition_results(
            [
                {
                    "analyzable": True,
                    "foods": [
                        {"name": "白米饭", "categories": ["谷薯类"]},
                        {"name": "番茄鸡蛋汤", "categories": ["蔬菜"]},
                    ],
                    "uncertain_items": [],
                },
                {
                    "analyzable": True,
                    "foods": [
                        {"name": "番茄鸡蛋汤", "categories": ["鱼禽肉蛋类", "蔬菜"]},
                        {"name": "清炒油麦菜", "categories": ["蔬菜"]},
                    ],
                    "uncertain_items": [],
                },
            ]
        )
        self.assertTrue(merged["analyzable"])
        self.assertEqual([food["name"] for food in merged["foods"]], ["白米饭", "番茄鸡蛋汤", "清炒油麦菜"])
        self.assertEqual(merged["foods"][1]["categories"], ["蔬菜", "鱼禽肉蛋类"])
        self.assertEqual(merged["source_count"], 2)
        self.assertEqual(merged["analyzable_count"], 2)

    def test_multiple_views_merge_only_conservative_food_aliases(self) -> None:
        merged = merge_recognition_results(
            [
                {
                    "analyzable": True,
                    "foods": [{"name": "米饭", "category": "主食"}],
                },
                {
                    "analyzable": True,
                    "foods": [
                        {"name": "白米饭", "category": "主食"},
                        {"name": "番茄鸡蛋汤", "category": "其他"},
                    ],
                },
            ]
        )
        self.assertEqual([food["name"] for food in merged["foods"]], ["米饭", "番茄鸡蛋汤"])

    def test_partial_multi_image_failure_is_reported_without_losing_valid_foods(self) -> None:
        merged = merge_recognition_results(
            [
                {
                    "analyzable": False,
                    "rejection_reason": "blurred",
                    "foods": [],
                },
                {
                    "analyzable": True,
                    "foods": [{"name": "白粥", "category": "主食"}],
                },
            ]
        )
        self.assertTrue(merged["analyzable"])
        self.assertEqual([food["name"] for food in merged["foods"]], ["白粥"])
        self.assertEqual(merged["source_count"], 2)
        self.assertEqual(merged["analyzable_count"], 1)
        self.assertEqual(merged["rejected_reasons"], ["blurred"])

    def test_all_failed_multi_image_results_keep_failure_metadata(self) -> None:
        merged = merge_recognition_results(
            [
                {"analyzable": False, "rejection_reason": "blurred", "foods": []},
                {"analyzable": False, "rejection_reason": "subject_missing", "foods": []},
            ]
        )
        self.assertFalse(merged["analyzable"])
        self.assertEqual(merged["source_count"], 2)
        self.assertEqual(merged["analyzable_count"], 0)

    def test_single_food_groups(self) -> None:
        self.assertEqual(infer_food_categories("白米饭"), ["谷薯类"])
        self.assertEqual(infer_food_categories("白切鸡"), ["鱼禽肉蛋类"])
        self.assertEqual(infer_food_categories("牛奶"), ["奶类"])
        self.assertEqual(infer_food_categories("豆腐"), ["大豆坚果类"])
        self.assertEqual(infer_food_categories("清炒油麦菜"), ["蔬菜"])
        self.assertEqual(infer_food_categories("蒸土豆"), ["谷薯类"])

    def test_composite_foods_keep_multiple_groups(self) -> None:
        self.assertEqual(infer_food_categories("番茄炒蛋"), ["鱼禽肉蛋类", "蔬菜"])
        self.assertEqual(infer_food_categories("辣椒炒鸡蛋"), ["鱼禽肉蛋类", "蔬菜"])
        self.assertEqual(infer_food_categories("青椒炒肉"), ["鱼禽肉蛋类", "蔬菜"])
        self.assertEqual(infer_food_categories("牛肉面"), ["谷薯类", "鱼禽肉蛋类"])
        self.assertEqual(infer_food_categories("蛋炒饭"), ["谷薯类", "鱼禽肉蛋类"])
        self.assertEqual(infer_food_categories("豆腐青菜"), ["大豆坚果类", "蔬菜"])

    def test_mushroom_flavor_names_do_not_become_animal_foods(self) -> None:
        self.assertEqual(infer_food_categories("海鲜菇"), ["蔬菜"])
        self.assertEqual(infer_food_categories("蟹味菇"), ["蔬菜"])
        self.assertEqual(
            infer_food_categories("牛肉炒蘑菇"),
            ["鱼禽肉蛋类", "蔬菜"],
        )
        self.assertEqual(
            infer_food_categories("海鲜菇炒虾仁"),
            ["鱼禽肉蛋类", "蔬菜"],
        )

    def test_unknown_food_is_not_forced_into_a_group(self) -> None:
        self.assertEqual(infer_food_categories("深色碎末"), ["无法判断"])

    def test_legacy_categories_are_migrated(self) -> None:
        foods = normalize_foods(
            [
                {"name": "豆浆", "category": "饮品"},
                {"name": "牛奶", "category": "奶豆坚果"},
                {"name": "白切鸡", "category": "蛋白质"},
            ]
        )
        self.assertEqual(foods[0]["categories"], ["大豆坚果类"])
        self.assertEqual(foods[1]["categories"], ["奶类"])
        self.assertEqual(foods[2]["categories"], ["鱼禽肉蛋类"])

    def test_composition_lists_each_group_on_its_own_line(self) -> None:
        foods = [
            {"name": "牛肉面", "categories": ["谷薯类", "鱼禽肉蛋类"]},
            {"name": "清炒油麦菜", "categories": ["蔬菜"]},
        ]
        summary = build_meal_composition(foods)
        self.assertIn("谷薯类：牛肉面", summary)
        self.assertIn("鱼禽肉蛋类：牛肉面", summary)
        self.assertIn("蔬菜：清炒油麦菜", summary)
        self.assertNotIn("。", summary)
        self.assertEqual(summary.count("\n"), 2)

    def test_multi_label_foods_contribute_to_structure(self) -> None:
        evidence = category_evidence(
            [{"name": "辣椒炒鸡蛋", "categories": ["鱼禽肉蛋类", "蔬菜"]}]
        )
        self.assertEqual(evidence["protein"], ["辣椒炒鸡蛋"])
        self.assertEqual(evidence["vegetables"], ["辣椒炒鸡蛋"])

    def test_local_summary_and_report_follow_confirmed_groups(self) -> None:
        complete = [
            {"name": "牛肉面", "categories": ["谷薯类", "鱼禽肉蛋类"]},
            {"name": "清炒青菜", "categories": ["蔬菜"]},
        ]
        self.assertIn("基础结构比较完整", build_structure_summary(complete))
        report = build_meal_report(complete)
        self.assertIn("牛肉面提供了主食", report)
        self.assertIn("牛肉面提供了蛋白质来源", report)
        self.assertIn("清炒青菜补充了蔬菜", report)

        incomplete = [{"name": "蛋炒饭", "categories": ["谷薯类", "鱼禽肉蛋类"]}]
        self.assertIn("暂未明显识别膳食纤维相关食物", build_structure_summary(incomplete))
        self.assertIn("暂未明显看到蔬菜", build_meal_report(incomplete))

    def test_risk_alerts_require_strong_name_evidence(self) -> None:
        alerts = build_risk_alerts(
            [
                {"name": "腊肉", "categories": ["鱼禽肉蛋类"]},
                {"name": "油条", "categories": ["谷薯类"]},
                {"name": "奶茶", "categories": ["其他"]},
            ]
        )
        self.assertEqual([alert["title"] for alert in alerts], ["盐可能偏多", "油脂可能偏多", "添加糖可能偏多"])
        self.assertIn("钠", alerts[0]["message"])
        self.assertEqual(build_risk_alerts([{"name": "清炒青菜", "categories": ["蔬菜"]}]), [])
        self.assertEqual(build_risk_alerts([{"name": "炸酱面", "categories": ["谷薯类"]}]), [])

    def test_user_facing_sentences_have_consistent_punctuation(self) -> None:
        self.assertEqual(ensure_sentence("结构比较清晰"), "结构比较清晰。")
        self.assertEqual(ensure_sentence("搭配得不错哦~"), "搭配得不错哦。")
        self.assertEqual(ensure_sentence("请稍候。"), "请稍候。")

    def test_confusion_tips_are_conditional(self) -> None:
        tips = build_knowledge_tips(
            [
                {"name": "蒜薹", "categories": ["蔬菜"]},
                {"name": "牛奶", "categories": ["奶类"]},
            ]
        )
        self.assertEqual(len(tips), 2)
        self.assertIn("为什么仍算蔬菜", tips[0]["title"])
        self.assertIn("含有碳水", tips[0]["message"])
        self.assertIn("为什么不归入普通饮料", tips[1]["title"])
        self.assertIn("食用形态", tips[1]["message"])

    def test_obvious_composite_food_does_not_trigger_knowledge_tip(self) -> None:
        tips = build_knowledge_tips(
            [{"name": "番茄炒蛋", "categories": ["鱼禽肉蛋类", "蔬菜"]}]
        )
        self.assertEqual(tips, [])

    def test_potato_triggers_non_obvious_group_tip(self) -> None:
        tips = build_knowledge_tips([{"name": "蒸红薯", "categories": ["谷薯类"]}])
        self.assertEqual(len(tips), 1)
        self.assertIn("薯类为什么计入主食", tips[0]["title"])
        self.assertIn("淀粉", tips[0]["message"])

    def test_analysis_payload_expands_multi_label_foods(self) -> None:
        payload = analysis_payload(
            [{"name": "牛肉面", "categories": ["谷薯类", "鱼禽肉蛋类"]}]
        )
        self.assertEqual(
            payload,
            [
                {"name": "牛肉面", "category": "主食"},
                {"name": "牛肉面", "category": "蛋白质"},
            ],
        )


if __name__ == "__main__":
    unittest.main()
