from __future__ import annotations

from collections import OrderedDict
from typing import Iterable


FOOD_CATEGORIES = (
    "谷薯类", "鱼禽肉蛋类", "奶类", "大豆坚果类", "蔬菜", "水果", "其他", "无法判断",
)

STAPLE_WORDS = (
    "米饭", "白饭", "炒饭", "盖饭", "焖饭", "粥", "面", "粉", "面包", "馒头",
    "包子", "饺子", "油条", "燕麦", "玉米", "土豆", "马铃薯", "红薯", "紫薯",
    "山药", "芋头", "杂粮",
    "河粉", "米线", "卷饼", "烧饼", "年糕",
)
ANIMAL_WORDS = (
    "鸡蛋", "鸭蛋", "鹌鹑蛋", "蛋花", "炒蛋", "蛋炒饭", "鸡肉", "白切鸡", "鸡胸", "鸭肉",
    "鱼", "虾", "蟹", "牛肉", "猪肉", "羊肉", "瘦肉", "肉", "排骨", "海鲜", "贝类",
    "香肠", "腊肠", "火腿",
)
STRONG_ANIMAL_WORDS = tuple(
    word for word in ANIMAL_WORDS if word not in ("海鲜", "鱼", "虾", "蟹")
) + (
    "蟹肉", "虾仁", "大虾", "鱼肉", "鱼片", "鲈鱼", "鲫鱼", "鲤鱼", "鳕鱼",
    "三文鱼", "龙利鱼",
)
DAIRY_WORDS = ("牛奶", "酸奶", "奶酪", "芝士", "乳酪", "奶粉")
SOY_NUT_WORDS = (
    "豆浆", "豆腐", "豆干", "豆皮", "腐竹", "黄豆", "黑豆", "毛豆", "坚果", "花生",
    "核桃", "腰果", "杏仁", "开心果",
)
VEGETABLE_WORDS = (
    "油麦菜", "青菜", "菠菜", "生菜", "白菜", "西兰花", "菜花", "番茄", "西红柿",
    "黄瓜", "冬瓜", "南瓜", "茄子", "胡萝卜", "白萝卜", "芹菜", "蒜薹", "蒜苔",
    "韭菜", "辣椒", "青椒", "彩椒", "豆角", "四季豆", "莴笋", "竹笋", "香菇",
    "蘑菇", "菌菇", "菇", "木耳", "紫菜", "海带", "莲藕", "娃娃菜",
)
FRUIT_WORDS = (
    "苹果", "香蕉", "橙", "橘", "柚子", "梨", "葡萄", "草莓", "蓝莓", "西瓜",
    "哈密瓜", "芒果", "猕猴桃", "桃", "火龙果", "菠萝",
)

HIGH_SALT_WORDS = (
    "咸菜", "榨菜", "酱菜", "泡菜", "酸菜", "腐乳", "咸蛋", "腊肉", "腊肠", "香肠",
    "火腿", "方便面", "泡面", "火锅底料", "卤味", "卤制", "腌制", "烟熏",
)
HIGH_FAT_WORDS = (
    "油条", "炸鸡", "炸串", "薯条", "油炸", "酥皮", "肥肉", "五花肉", "奶油",
    "炸糕", "炸丸子", "炸鱼", "炸虾",
)
HIGH_SUGAR_WORDS = (
    "奶茶", "可乐", "汽水", "含糖饮料", "蛋糕", "甜点", "糖果", "冰淇淋", "曲奇",
    "甜甜圈", "巧克力",
)

LEGACY_CATEGORY_MAP = {
    "主食": ["谷薯类"],
    "蛋白质": ["鱼禽肉蛋类"],
    "蛋白质类": ["鱼禽肉蛋类"],
    "奶豆坚果": ["奶类", "大豆坚果类"],
    "蔬菜": ["蔬菜"],
    "水果": ["水果"],
    "混合菜": [],
    "饮品": [],
    "其他": ["其他"],
}


def _contains_any(name: str, words: Iterable[str]) -> bool:
    return any(word in name for word in words)


def _coerce_categories(value: object) -> list[str]:
    if isinstance(value, (list, tuple, set)):
        values = [str(item).strip() for item in value]
    else:
        raw = str(value or "").strip()
        values = [part.strip() for part in raw.replace("，", ",").split(",") if part.strip()]
    return [category for category in FOOD_CATEGORIES if category in values]


def infer_food_categories(name: str, current_categories: object = None) -> list[str]:
    """Return deterministic, multi-label food groups for the confirmation UI."""
    clean_name = str(name).strip()
    if not clean_name:
        return ["无法判断"]

    # 菌菇名称可能带有“海鲜”“蟹味”等风味词，不能据此判断含有海鲜。
    mushroom_name = _contains_any(clean_name, ("菇", "菌"))
    has_strong_animal = _contains_any(clean_name, STRONG_ANIMAL_WORDS)

    matched = []
    for category, words in (
        ("谷薯类", STAPLE_WORDS),
        ("鱼禽肉蛋类", ANIMAL_WORDS),
        ("奶类", DAIRY_WORDS),
        ("大豆坚果类", SOY_NUT_WORDS),
        ("蔬菜", VEGETABLE_WORDS),
        ("水果", FRUIT_WORDS),
    ):
        if category == "鱼禽肉蛋类" and mushroom_name and not has_strong_animal:
            continue
        if _contains_any(clean_name, words):
            matched.append(category)
    if matched:
        return matched

    current = _coerce_categories(current_categories)
    if current:
        return current
    legacy = LEGACY_CATEGORY_MAP.get(str(current_categories or "").strip(), [])
    return legacy or ["无法判断"]


def normalize_foods(foods: Iterable[dict[str, object]]) -> list[dict[str, object]]:
    normalized = []
    for food in foods:
        name = str(food.get("name", "")).strip()
        if not name:
            continue
        normalized.append(
            {
                "name": name,
                "categories": infer_food_categories(name, food.get("categories", food.get("category", ""))),
                "delete": False,
            }
        )
    return normalized


FOOD_NAME_ALIASES = {
    "米饭": "白米饭",
    "白饭": "白米饭",
    "白米饭": "白米饭",
    "西红柿炒鸡蛋": "番茄炒蛋",
    "番茄炒鸡蛋": "番茄炒蛋",
    "番茄炒蛋": "番茄炒蛋",
}


def _food_identity_key(name: str) -> str:
    """Return a conservative identity key for deduplicating multiple views."""
    compact_name = "".join(str(name).strip().casefold().split())
    return FOOD_NAME_ALIASES.get(compact_name, compact_name)


def merge_recognition_results(results: list[dict[str, object]]) -> dict[str, object]:
    """Merge several views of one meal without inventing new food records."""
    analyzable_results = [result for result in results if result.get("analyzable")]
    if not analyzable_results:
        fallback = dict(results[0]) if results else {
            "analyzable": False,
            "rejection_reason": "other",
            "foods": [],
        }
        fallback["source_count"] = len(results)
        fallback["analyzable_count"] = 0
        return fallback

    foods_by_name: dict[str, dict[str, object]] = {}
    uncertain_items: list[dict[str, object]] = []
    uncertain_keys: set[tuple[str, str]] = set()
    for result in analyzable_results:
        for food in result.get("foods") or []:
            name = str(food.get("name", "")).strip()
            if not name:
                continue
            key = _food_identity_key(name)
            if key not in foods_by_name:
                foods_by_name[key] = dict(food)
                continue
            existing = foods_by_name[key]
            categories: list[str] = []
            for source in (existing, food):
                values = source.get("categories", source.get("category", []))
                if isinstance(values, str):
                    values = [values]
                for value in values or []:
                    if value and value not in categories:
                        categories.append(str(value))
            if categories:
                existing["categories"] = categories

        for item in result.get("uncertain_items") or []:
            item_key = (
                str(item.get("description", "")).strip(),
                str(item.get("reason", "")).strip(),
            )
            if item_key not in uncertain_keys:
                uncertain_keys.add(item_key)
                uncertain_items.append(dict(item))

    return {
        **analyzable_results[0],
        "analyzable": True,
        "foods": list(foods_by_name.values()),
        "uncertain_items": uncertain_items,
        "source_count": len(results),
        "analyzable_count": len(analyzable_results),
        "rejected_reasons": [
            str(result.get("rejection_reason") or "other")
            for result in results
            if not result.get("analyzable")
        ],
    }


def group_foods(foods: Iterable[dict[str, object]]) -> OrderedDict[str, list[str]]:
    grouped: OrderedDict[str, list[str]] = OrderedDict((category, []) for category in FOOD_CATEGORIES)
    for food in foods:
        name = str(food.get("name", "")).strip()
        categories = _coerce_categories(food.get("categories")) or infer_food_categories(
            name, food.get("category", "")
        )
        for category in categories:
            if name and name not in grouped[category]:
                grouped[category].append(name)
    return grouped


def category_evidence(foods: Iterable[dict[str, object]]) -> dict[str, list[str]]:
    """Map structure cards to concrete confirmed foods without model guessing."""
    grouped = group_foods(foods)
    protein_names = []
    for category in ("鱼禽肉蛋类", "奶类", "大豆坚果类"):
        for name in grouped[category]:
            if name not in protein_names:
                protein_names.append(name)
    return {
        "staple": grouped["谷薯类"],
        "protein": protein_names,
        "vegetables": grouped["蔬菜"],
    }


def build_meal_composition(foods: Iterable[dict[str, object]]) -> str:
    grouped = group_foods(foods)
    parts = []
    for category, names in grouped.items():
        if names:
            parts.append(f"{category}：{'、'.join(names)}")
    return "\n".join(parts) if parts else "暂时没有可分析的食物。"


def build_structure_summary(foods: Iterable[dict[str, object]]) -> str:
    """Build a deterministic headline from the user's confirmed food groups."""
    evidence = category_evidence(foods)
    labels = {"staple": "主食", "protein": "蛋白质来源", "vegetables": "蔬菜"}
    present = [labels[key] for key in labels if evidence[key]]
    missing = [labels[key] for key in labels if not evidence[key]]
    if not present:
        return "暂时无法从确认的食物中判断主食、蛋白质来源和蔬菜结构。"
    if not missing:
        return "这一餐已经包含主食、蛋白质来源和蔬菜，基础结构比较完整。"
    return f"这一餐已经包含{'、'.join(present)}，暂未明显看到{'、'.join(missing)}。"


def build_meal_report(foods: Iterable[dict[str, object]]) -> str:
    """Create a concrete closing report without reclassifying confirmed foods."""
    evidence = category_evidence(foods)
    clauses = []
    if evidence["staple"]:
        clauses.append(f"{'、'.join(evidence['staple'])}提供了主食")
    if evidence["protein"]:
        clauses.append(f"{'、'.join(evidence['protein'])}提供了蛋白质来源")
    if evidence["vegetables"]:
        clauses.append(f"{'、'.join(evidence['vegetables'])}补充了蔬菜")
    missing = [
        label for key, label in (("staple", "主食"), ("protein", "蛋白质来源"), ("vegetables", "蔬菜"))
        if not evidence[key]
    ]
    if not clauses:
        return "目前确认的食物信息还不足以判断这餐的基础结构，可以继续补充或修改食物类别。"
    detail = "；".join(clauses)
    if missing:
        return f"这餐中，{detail}。目前暂未明显看到{'、'.join(missing)}，可以按自己的食量适量补充。"
    return f"这餐中，{detail}。三类基础食物都有覆盖，整体搭配值得继续保持。"


def ensure_sentence(text: str) -> str:
    clean_text = str(text or "").strip().rstrip("~～")
    if not clean_text:
        return ""
    if clean_text.endswith(("。", "！", "？")):
        return clean_text
    return f"{clean_text.rstrip('.!?')}。"


def build_risk_alerts(foods: Iterable[dict[str, object]]) -> list[dict[str, str]]:
    """Create cautious, non-quantitative alerts only from strong name evidence."""
    names = [str(food.get("name", "")).strip() for food in foods if str(food.get("name", "")).strip()]
    alerts = []

    salty = [name for name in names if _contains_any(name, HIGH_SALT_WORDS)]
    if salty:
        alerts.append({
            "title": "盐可能偏多",
            "message": f"{'、'.join(salty)}通常比较咸，盐里的钠也会相应增加。"
            "这餐可以少吃一点腌制或加工配菜，汤汁和酱汁也不用全部吃完。",
        })

    fatty = [name for name in names if _contains_any(name, HIGH_FAT_WORDS) and "炸酱" not in name]
    if fatty:
        alerts.append({
            "title": "油脂可能偏多",
            "message": f"{'、'.join(fatty)}通常会带来较多油脂。"
            "可以适当少吃油炸外皮、肥肉或奶油部分，再搭配一份清淡蔬菜。",
        })

    sugary = [name for name in names if _contains_any(name, HIGH_SUGAR_WORDS)]
    if sugary:
        alerts.append({
            "title": "添加糖可能偏多",
            "message": f"{'、'.join(sugary)}通常会加入较多糖。"
            "今天其他饮料可以优先选择白水或无糖茶，也不用再额外搭配甜点。",
        })
    return alerts


def build_knowledge_tips(foods: Iterable[dict[str, object]]) -> list[dict[str, str]]:
    """Return only genuinely non-obvious, food-specific classification notes."""
    names = [str(food.get("name", "")).strip() for food in foods]
    tips = []
    if any("蒜薹" in name or "蒜苔" in name for name in names):
        tips.append({
            "title": "蒜薹含碳水，为什么仍算蔬菜？",
            "message": "蒜薹确实含有碳水化合物，但“含有碳水”不等于“属于主食”。"
            "按食物类别，它属于葱蒜类蔬菜，因此本餐仍计入蔬菜。",
        })
    if any(_contains_any(name, ("土豆", "马铃薯", "红薯", "紫薯", "山药", "芋头")) for name in names):
        tips.append({
            "title": "薯类为什么计入主食？",
            "message": "土豆、红薯、山药等薯类常被当作配菜，但它们通常能提供较多淀粉。"
            "本项目把薯类计入谷薯类；如果一餐已经吃了较多薯类，可以相应调整米饭或面食。",
        })
    if any("牛奶" in name for name in names):
        tips.append({
            "title": "牛奶是饮品，为什么不归入普通饮料？",
            "message": "“饮品”描述的是食用形态，“奶类”描述的是食物类别。"
            "牛奶在餐食结构中计入奶类，也可以作为蛋白质来源之一。",
        })
    if any("坚果" in name or name in ("花生", "核桃", "腰果", "杏仁") for name in names):
        tips.append({
            "title": "坚果含脂肪，为什么仍单独归类？",
            "message": "坚果通常含有较多脂肪，也能提供部分蛋白质。"
            "“脂肪”是营养素，不是食物类别，因此本项目仍把它归入大豆坚果类。",
        })
    return tips[:2]


def analysis_payload(foods: Iterable[dict[str, object]]) -> list[dict[str, str]]:
    """Expand food groups into labels understood by the existing Coze workflow."""
    compatibility = {
        "谷薯类": "主食", "鱼禽肉蛋类": "蛋白质", "奶类": "蛋白质",
        "大豆坚果类": "蛋白质", "蔬菜": "蔬菜", "水果": "水果",
        "其他": "其他", "无法判断": "其他",
    }
    payload = []
    for food in foods:
        name = str(food.get("name", "")).strip()
        if not name:
            continue
        categories = _coerce_categories(food.get("categories")) or infer_food_categories(
            name, food.get("category", "")
        )
        for category in categories:
            payload.append({"name": name, "category": compatibility[category]})
    return payload
