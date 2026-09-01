from __future__ import annotations

from collections import OrderedDict
from typing import Iterable


FOOD_CATEGORIES = ("主食", "蛋白质类", "蔬菜", "水果", "混合菜", "其他")

STAPLE_WORDS = (
    "米饭", "白饭", "粥", "面条", "面包", "馒头", "包子", "饺子", "油条", "燕麦",
    "玉米", "红薯", "紫薯", "土豆", "山药", "杂粮", "粉条", "米粉", "河粉",
)
PROTEIN_WORDS = (
    "牛奶", "酸奶", "豆浆", "豆腐", "豆干", "豆皮", "鸡蛋", "鸭蛋", "鹌鹑蛋",
    "鸡肉", "白切鸡", "鸡胸", "鸭肉", "鱼", "虾", "蟹", "牛肉", "猪肉", "羊肉",
    "瘦肉", "肉", "排骨", "海鲜", "贝类",
)
VEGETABLE_WORDS = (
    "油麦菜", "青菜", "菠菜", "生菜", "白菜", "西兰花", "菜花", "番茄", "西红柿",
    "黄瓜", "冬瓜", "南瓜", "茄子", "胡萝卜", "白萝卜", "芹菜", "蒜薹", "蒜苔",
    "韭菜", "辣椒", "青椒", "彩椒", "豆角", "四季豆", "莴笋", "竹笋", "香菇", "蘑菇", "菌菇", "木耳",
)
FRUIT_WORDS = (
    "苹果", "香蕉", "橙", "橘", "柚子", "梨", "葡萄", "草莓", "蓝莓", "西瓜",
    "哈密瓜", "芒果", "猕猴桃", "桃", "火龙果", "菠萝",
)
MIXED_DISH_PATTERNS = (
    ("番茄", "蛋"), ("西红柿", "蛋"), ("肉", "菜"), ("牛肉", "面"), ("鸡蛋", "面"),
)


def _contains_any(name: str, words: Iterable[str]) -> bool:
    return any(word in name for word in words)


def infer_food_category(name: str, current_category: str = "") -> str:
    """Return a simple, user-facing primary food category.

    This is intentionally deterministic for common foods. The user can always
    override the result in the confirmation table.
    """
    clean_name = str(name).strip()
    if not clean_name:
        return "其他"

    if any(all(part in clean_name for part in pattern) for pattern in MIXED_DISH_PATTERNS):
        return "混合菜"

    matched = []
    for category, words in (
        ("主食", STAPLE_WORDS),
        ("蛋白质类", PROTEIN_WORDS),
        ("蔬菜", VEGETABLE_WORDS),
        ("水果", FRUIT_WORDS),
    ):
        if _contains_any(clean_name, words):
            matched.append(category)
    if len(matched) > 1:
        return "混合菜"
    if matched:
        return matched[0]

    legacy_map = {
        "蛋白质": "蛋白质类",
        "奶豆坚果": "蛋白质类" if _contains_any(clean_name, PROTEIN_WORDS) else "其他",
        "饮品": "蛋白质类" if _contains_any(clean_name, ("牛奶", "酸奶", "豆浆")) else "其他",
        "主食": "主食",
        "蔬菜": "蔬菜",
        "水果": "水果",
        "混合菜": "混合菜",
        "其他": "其他",
    }
    return legacy_map.get(str(current_category).strip(), "其他")


def normalize_foods(foods: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    normalized = []
    for food in foods:
        name = str(food.get("name", "")).strip()
        if not name:
            continue
        normalized.append(
            {
                "name": name,
                "category": infer_food_category(name, str(food.get("category", ""))),
                "delete": False,
            }
        )
    return normalized


def group_foods(foods: Iterable[dict[str, str]]) -> OrderedDict[str, list[str]]:
    grouped: OrderedDict[str, list[str]] = OrderedDict((category, []) for category in FOOD_CATEGORIES)
    for food in foods:
        name = str(food.get("name", "")).strip()
        category = infer_food_category(name, str(food.get("category", "")))
        if name and name not in grouped[category]:
            grouped[category].append(name)
    return grouped


def category_evidence(foods: Iterable[dict[str, str]]) -> dict[str, list[str]]:
    """Map the three structure cards to concrete confirmed foods."""
    evidence = {"staple": [], "protein": [], "vegetables": []}
    for food in foods:
        name = str(food.get("name", "")).strip()
        category = infer_food_category(name, str(food.get("category", "")))
        if category == "主食":
            evidence["staple"].append(name)
        elif category == "蛋白质类":
            evidence["protein"].append(name)
        elif category == "蔬菜":
            evidence["vegetables"].append(name)
        elif category == "混合菜":
            if _contains_any(name, STAPLE_WORDS):
                evidence["staple"].append(name)
            if _contains_any(name, PROTEIN_WORDS) or "蛋" in name:
                evidence["protein"].append(name)
            if _contains_any(name, VEGETABLE_WORDS):
                evidence["vegetables"].append(name)
    return evidence


def build_meal_composition(foods: Iterable[dict[str, str]]) -> str:
    grouped = group_foods(foods)
    parts = []
    for category, names in grouped.items():
        if names:
            parts.append(f"{category}：{'、'.join(names)}。")
    return "\n".join(parts) if parts else "暂时没有可分析的食物。"


def ensure_sentence(text: str) -> str:
    """Normalize user-facing prose to one consistently punctuated sentence."""
    clean_text = str(text or "").strip().rstrip("~～")
    if not clean_text:
        return ""
    if clean_text.endswith(("。", "！", "？")):
        return clean_text
    return f"{clean_text.rstrip('.!?')}。"


def build_knowledge_tips(foods: Iterable[dict[str, str]]) -> list[str]:
    names = [str(food.get("name", "")).strip() for food in foods]
    tips = []
    if any("蒜薹" in name or "蒜苔" in name for name in names):
        tips.append("蒜薹通常归入蔬菜。它含有碳水化合物，但“含有碳水”不等于“属于主食”。")
    if any("牛奶" in name for name in names):
        tips.append("牛奶虽然是饮品形态，但在餐食结构中更适合作为蛋白质来源理解，同时也可能提供乳糖和脂肪。")
    if any(("番茄" in name or "西红柿" in name) and "蛋" in name for name in names):
        tips.append("番茄炒蛋是混合菜：番茄主要贡献蔬菜，鸡蛋主要贡献蛋白质。")
    if any("坚果" in name or name in ("花生", "核桃", "腰果", "杏仁") for name in names):
        tips.append("坚果通常以脂肪贡献为主，也能提供部分蛋白质，因此不必强行归入单一营养素。")
    return tips[:2]


def analysis_payload(foods: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    """Translate UI categories to the analysis workflow's compatible labels."""
    compatibility = {"蛋白质类": "蛋白质", "混合菜": "其他"}
    return [
        {
            "name": str(food.get("name", "")).strip(),
            "category": compatibility.get(str(food.get("category", "")).strip(), str(food.get("category", "")).strip()),
        }
        for food in foods
        if str(food.get("name", "")).strip()
    ]
