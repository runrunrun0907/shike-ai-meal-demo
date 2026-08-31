# 食刻｜AI 餐食结构小助手

一个基于多模态大模型、Coze 双工作流和 Streamlit 搭建的餐食结构分析 Web Demo。

用户上传餐食图片后，系统先返回结构化识别结果，由用户修改或确认，再根据最终食物列表生成亲切、可执行且不过度推断的餐食结构建议。

## 核心流程

`上传图片 → 餐食识别 → 用户确认/修正 → 餐食结构分析 → 行动建议`

## 产品亮点

- 两阶段 AI 工作流：将视觉识别与餐食分析解耦。
- 人机协同：用户可以修改、删除或补充 AI 识别结果。
- 不确定性表达：模糊配料进入不确定项，不强行猜测具体食材。
- 安全边界：不估算缺乏依据的克重、热量和营养素，不提供医疗诊断。
- 可复现评测：覆盖清晰餐食、复杂餐食、模糊图片、主体缺失及三类结构分析场景。

本目录用于存放 Streamlit 应用、Coze API 接入代码、产品文档、评测数据与开发记录，与简历修改材料分开管理。

## 项目目录

- `app/`：Streamlit 应用代码
- `docs/`：产品方案、技术决策与开发日志
- `evaluation/`：测试用例、Bad Case 与评测结果
- `tests/`：自动化测试

当前开发优先级与阶段进度见 [`docs/roadmap.md`](docs/roadmap.md)。

> Coze API Token 等密钥不得提交到代码仓库，后续通过本地环境变量或部署平台 Secrets 配置。

## 本地运行 Streamlit

```bash
cd "/Users/run1111/Documents/ChatGPT/New project/ai-food-demo"
python -m pip install -r requirements.txt
export COZE_API_TOKEN="在本机填写你的 Token"
streamlit run streamlit_app.py
```

页面目前支持图片上传、Base64 Data URL 调用 `meal_recognition_v2`、失败提示、可编辑食物列表和不确定项展示；确认食物后会调用 `meal_analysis_v2`，展示餐食结构、主要问题、行动建议与安全说明。真实 Token 不得写入 `.env.example` 或提交到版本库。

## 自动评测

```bash
.venv/bin/python evaluation/evaluate_recognition.py
.venv/bin/python evaluation/evaluate_analysis.py
```

首轮评测结果：识别核心分支 `4/4` 通过，分析核心场景 `3/3` 通过。详细结果保存在 `evaluation/`。

公网部署所需配置与安全检查见 [`docs/deployment.md`](docs/deployment.md)。
