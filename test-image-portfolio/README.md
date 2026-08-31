# 餐食识别测试图片集

用于验证 `meal_recognition_v2` 的图片质量判断、食物识别、不确定性表达和失败分支。

## 分类与预期结果

| 分类 | 文件 | 测试目的 | 主要预期 |
|---|---|---|---|
| 清晰正例 | `01-clear-positive/clear-balanced-meal.png` | 验证多菜品识别和分类 | `analyzable=true`；识别米饭、绿叶菜、鸡肉、番茄鸡蛋汤等清晰主体 |
| 复杂食物 | `02-ambiguous-foods/ambiguous-mixed-stew.png` | 验证明确食材与不确定食材能否分开 | 可确认项进入 `foods`；无法确认的小块食材进入 `uncertain_items` |
| 严重模糊 | `03-blurred/severely-blurred-meal.png` | 验证图片质量拒绝分支 | `analyzable=false`；`rejection_reason=blurred`；两个列表为空 |
| 主体缺失 | `04-subject-missing/cropped-missing-meal.png` | 验证餐食主体严重被裁切 | `analyzable=false`；`rejection_reason=subject_missing`；两个列表为空 |

## 建议测试顺序

1. 清晰正例：确认基本识别能力。
2. 严重模糊：确认模型不会强行猜测。
3. 主体缺失：确认失败原因分类正确。
4. 复杂食物：重点观察 `foods` 与 `uncertain_items` 是否重复，以及模型是否猜测烹饪方式。

## 结果记录建议

每次测试记录模型版本、运行日期、耗时、原始输出、是否通过和问题说明。所有图片均为项目测试用途生成，不代表真实用户拍摄数据。
