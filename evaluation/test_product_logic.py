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
    category_evidence,
    ensure_sentence,
    infer_food_category,
    normalize_foods,
)


class ProductLogicTests(unittest.TestCase):
    def test_common_food_auto_classification(self) -> None:
        self.assertEqual(infer_food_category("牛奶", "其他"), "蛋白质类")
        self.assertEqual(infer_food_category("蒜薹炒肉", "其他"), "混合菜")
        self.assertEqual(infer_food_category("番茄炒蛋", "其他"), "混合菜")
        self.assertEqual(infer_food_category("辣椒炒鸡蛋", "蛋白质类"), "混合菜")
        self.assertEqual(infer_food_category("辣椒炒肉", "蛋白质类"), "混合菜")
        self.assertEqual(infer_food_category("杂粮饭", "其他"), "主食")

    def test_legacy_categories_are_simplified(self) -> None:
        foods = normalize_foods(
            [
                {"name": "豆浆", "category": "饮品"},
                {"name": "牛奶", "category": "奶豆坚果"},
                {"name": "白切鸡", "category": "蛋白质"},
            ]
        )
        self.assertEqual([food["category"] for food in foods], ["蛋白质类"] * 3)

    def test_composition_uses_exact_food_names(self) -> None:
        foods = [
            {"name": "牛奶", "category": "蛋白质类"},
            {"name": "清炒油麦菜", "category": "蔬菜"},
            {"name": "番茄炒蛋", "category": "混合菜"},
        ]
        summary = build_meal_composition(foods)
        self.assertIn("蛋白质类：牛奶", summary)
        self.assertIn("蔬菜：清炒油麦菜", summary)
        self.assertIn("混合菜：番茄炒蛋", summary)
        self.assertEqual(summary.count("\n"), 2)

    def test_mixed_dish_contributes_to_structure(self) -> None:
        evidence = category_evidence([{"name": "番茄炒蛋", "category": "混合菜"}])
        self.assertEqual(evidence["protein"], ["番茄炒蛋"])
        self.assertEqual(evidence["vegetables"], ["番茄炒蛋"])

        pepper_evidence = category_evidence([{"name": "辣椒炒鸡蛋", "category": "混合菜"}])
        self.assertEqual(pepper_evidence["protein"], ["辣椒炒鸡蛋"])
        self.assertEqual(pepper_evidence["vegetables"], ["辣椒炒鸡蛋"])

    def test_user_facing_sentences_have_consistent_punctuation(self) -> None:
        self.assertEqual(ensure_sentence("结构比较清晰"), "结构比较清晰。")
        self.assertEqual(ensure_sentence("搭配得不错哦~"), "搭配得不错哦。")
        self.assertEqual(ensure_sentence("请稍候。"), "请稍候。")

    def test_confusion_tips_are_conditional(self) -> None:
        tips = build_knowledge_tips(
            [
                {"name": "蒜薹", "category": "蔬菜"},
                {"name": "牛奶", "category": "蛋白质类"},
            ]
        )
        self.assertEqual(len(tips), 2)
        self.assertIn("属于主食", tips[0])
        self.assertIn("蛋白质来源", tips[1])
        self.assertEqual(build_knowledge_tips([{"name": "米饭", "category": "主食"}]), [])

    def test_analysis_payload_keeps_workflow_compatibility(self) -> None:
        payload = analysis_payload(
            [
                {"name": "牛奶", "category": "蛋白质类"},
                {"name": "番茄炒蛋", "category": "混合菜"},
            ]
        )
        self.assertEqual(payload[0]["category"], "蛋白质")
        self.assertEqual(payload[1]["category"], "其他")


if __name__ == "__main__":
    unittest.main()
