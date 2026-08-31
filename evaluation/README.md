# 评测说明

`evaluate_recognition.py` 使用固定的四类测试图片检查识别工作流的核心分支：

- 清晰餐食可以分析；
- 复杂餐食可以分析，并观察不确定项；
- 严重模糊图片返回 `blurred`；
- 餐食主体缺失返回 `subject_missing`。

运行方式：

```bash
cd "/Users/run1111/Documents/ChatGPT/New project/ai-food-demo"
.venv/bin/python evaluation/evaluate_recognition.py
```

脚本只输出测试摘要，不打印 API Token，也不保存用户图片。

`evaluate_analysis.py` 使用三组固定食物列表检查分析工作流：结构完整、只有主食、缺少主食。除结构枚举外，还检查问题数量以及在没有份量信息时是否出现不恰当的分量结论。

```bash
.venv/bin/python evaluation/evaluate_analysis.py
```
