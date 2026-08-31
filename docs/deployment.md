# 公网部署准备

## Streamlit 入口

- 应用入口：`app/main.py`
- Python 依赖：`requirements.txt`
- 单张图片上限：10 MB

## 部署平台 Secrets

在部署平台的 Secrets 管理页面配置以下字段，不要写入代码或提交到 Git：

```toml
COZE_API_TOKEN = "部署环境使用的 Token"
COZE_WORKFLOW_URL = "https://nwgs6rtrn3.coze.site/run"
COZE_ANALYSIS_URL = "https://f567znb64x.coze.site/run"
```

建议为公开 Demo 单独创建一个权限最小化、可随时撤销的 Token，不要复用个人开发 Token。

## 上线前检查

1. 确认 `.streamlit/secrets.toml` 和 `.env` 均被 `.gitignore` 排除。
2. 运行两套评测脚本并保留结果。
3. 检查非餐食、模糊图片和主体缺失提示。
4. 检查用户修改食物后重新分析是否生效。
5. 部署后使用公开地址完整执行一次识别和分析。
6. 分别检查桌面端与约 390 px 宽度的手机端布局。

## 当前状态

代码和配置已具备部署条件；尚未创建公开站点，也未向任何远程仓库上传密钥。
