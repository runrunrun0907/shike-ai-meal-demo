from __future__ import annotations

import os
from html import escape

import pandas as pd
import streamlit as st

try:
    from app.coze_client import CozeAPIError, run_analysis, run_recognition
except ModuleNotFoundError:
    from coze_client import CozeAPIError, run_analysis, run_recognition


st.set_page_config(
    page_title="食刻｜AI 餐食结构小助手",
    page_icon="🥗",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    [data-testid="stToolbar"], #MainMenu, footer {display: none !important;}
    .stApp {background: linear-gradient(180deg, #f5faf6 0, #ffffff 300px);}
    .block-container {max-width: 860px; padding-top: 2.4rem; padding-bottom: 4rem;}
    .hero {padding: 1.65rem 1.75rem; border: 1px solid #dceadf; border-radius: 24px;
      background: rgba(255,255,255,.92); box-shadow: 0 12px 36px rgba(38,84,55,.08);}
    .hero-kicker {color: #2e8b57; font-size: .84rem; font-weight: 700; letter-spacing: .12em;}
    .hero h1 {font-size: 2.15rem; margin: .35rem 0 .55rem; color: #1f2d25;}
    .hero p {margin: 0; color: #617067; font-size: 1rem; line-height: 1.75;}
    .steps {display: grid; grid-template-columns: repeat(3, 1fr); gap: .75rem; margin: 1rem 0 1.6rem;}
    .step {background: #edf6ef; color: #365342; border-radius: 14px; padding: .78rem .9rem;
      font-size: .9rem; text-align: center; font-weight: 600;}
    .step span {display: inline-grid; place-items: center; width: 1.45rem; height: 1.45rem;
      margin-right: .32rem; border-radius: 50%; background: #2e8b57; color: white;}
    .section-title {margin-top: 1.2rem; color: #24302a; font-size: 1.3rem; font-weight: 750;}
    .privacy-note {margin: -.25rem 0 1rem; color: #718078; font-size: .82rem;}
    .structure-card {border: 1px solid #dce9df; border-radius: 16px; padding: 1rem;
      background: #fff; text-align: center; box-shadow: 0 5px 16px rgba(42,88,57,.05);}
    .structure-label {color: #6d7a72; font-size: .86rem; margin-bottom: .28rem;}
    .structure-value {color: #267c4d; font-size: 1.18rem; font-weight: 750;}
    .result-summary {margin: .35rem 0 1.35rem; color: #34453b; font-size: 1.04rem; line-height: 1.85;}
    .result-block-title {margin: 1.7rem 0 .7rem; color: #24302a; font-size: 1.22rem; font-weight: 750;}
    .praise-card, .issue-card, .suggestion-card, .report-card {border-radius: 16px; padding: 1rem 1.15rem;
      line-height: 1.8; margin: .65rem 0;}
    .praise-card {background: #edf8f0; border: 1px solid #cfe7d5; color: #246b43;}
    .issue-card {background: #fffbeb; border: 1px solid #f0e2ad; color: #80620a;}
    .suggestion-card {background: #fff; border: 1px solid #dce9df; color: #34453b;
      box-shadow: 0 5px 16px rgba(42,88,57,.05);}
    .report-card {background: linear-gradient(135deg, #edf8f0, #f5fbf6); border: 1px solid #d2ead8; color: #237145;}
    .card-title {font-weight: 750; margin-bottom: .22rem; color: inherit;}
    [data-testid="stMarkdownContainer"] p {line-height: 1.75;}
    [data-testid="stCaptionContainer"] {line-height: 1.7;}
    div.stButton > button[kind="primary"] {border-radius: 12px; min-height: 3rem; font-weight: 700;}
    div[data-testid="stFileUploader"] {border: 1px dashed #9fc7aa; border-radius: 16px; padding: .35rem;}
    @media (max-width: 640px) {
      .block-container {padding: 1rem .85rem 3rem;}
      .hero {padding: 1.25rem; border-radius: 18px;}
      .hero h1 {font-size: 1.72rem;}
      .steps {grid-template-columns: 1fr; gap: .45rem;}
      .step {text-align: left;}
    }
    </style>
    <div class="hero">
      <div class="hero-kicker">AI MEAL COMPANION</div>
      <h1>🥗 食刻</h1>
      <p>上传一张餐食照片，确认 AI 识别结果，再获得清晰、亲切、可执行的餐食结构建议。</p>
    </div>
    <div class="steps">
      <div class="step"><span>1</span>上传餐食</div>
      <div class="step"><span>2</span>确认食物</div>
      <div class="step"><span>3</span>查看建议</div>
    </div>
    """,
    unsafe_allow_html=True,
)

MAX_FILE_SIZE = 10 * 1024 * 1024

def setting(name: str, default: str = "") -> str:
    return os.getenv(name) or str(st.secrets.get(name, default))


token = setting("COZE_API_TOKEN")
workflow_url = setting("COZE_WORKFLOW_URL", "https://nwgs6rtrn3.coze.site/run")
analysis_url = setting("COZE_ANALYSIS_URL", "https://f567znb64x.coze.site/run")

if "uploader_key" not in st.session_state:
    st.session_state["uploader_key"] = 0

if st.session_state.get("recognition"):
    if st.button("↻ 分析另一餐"):
        for key in ("recognition", "analysis", "confirmed_foods", "foods_editor"):
            st.session_state.pop(key, None)
        st.session_state["uploader_key"] += 1
        st.rerun()

uploaded = st.file_uploader(
    "上传一张餐食图片",
    type=["jpg", "jpeg", "png", "webp"],
    key=f"meal_uploader_{st.session_state['uploader_key']}",
)
st.markdown('<div class="privacy-note">🔒 图片仅用于本次 AI 分析，当前版本不会保存用户上传的图片。</div>', unsafe_allow_html=True)

file_too_large = uploaded is not None and uploaded.size > MAX_FILE_SIZE
if file_too_large:
    st.error("图片超过 10 MB，请压缩后重新上传。")

if uploaded and not file_too_large:
    st.image(uploaded, caption="待识别图片", width="stretch")

if st.button("开始识别", type="primary", disabled=uploaded is None or file_too_large):
    if not token:
        st.error("尚未配置 COZE_API_TOKEN。请在本机环境变量或 Streamlit Secrets 中配置，勿写入代码。")
    else:
        try:
            with st.status("正在识别图片……", expanded=True) as status:
                st.write("调用 meal_recognition_v2")
                result = run_recognition(workflow_url, token, uploaded.getvalue(), uploaded.type)
                st.session_state["recognition"] = result
                st.session_state.pop("analysis", None)
                st.session_state.pop("confirmed_foods", None)
                status.update(label="识别完成", state="complete", expanded=False)
        except (CozeAPIError, ValueError) as exc:
            st.error(str(exc))

result = st.session_state.get("recognition")
if result:
    if not result.get("analyzable"):
        reason_text = {
            "blurred": "图片过于模糊，请重新拍摄清晰的餐食照片。",
            "not_food": "没有识别到餐食，请上传包含餐食主体的图片。",
            "subject_missing": "餐食主体不完整，请让整份餐食出现在画面中。",
            "other": "这张图片暂时无法分析，请重新上传。",
        }.get(result.get("rejection_reason"), "这张图片暂时无法分析，请重新上传。")
        st.warning(reason_text)
    else:
        st.markdown('<div class="section-title">确认识别结果</div>', unsafe_allow_html=True)
        st.caption("AI 可能会把菜品分得过细。请修改、删除或补充后再确认。")

        foods = result.get("foods") or []
        table = pd.DataFrame(foods, columns=["name", "category"])
        table.index = range(1, len(table) + 1)
        edited = st.data_editor(
            table,
            hide_index=False,
            num_rows="dynamic",
            column_config={
                "_index": st.column_config.NumberColumn("编号", disabled=True),
                "name": st.column_config.TextColumn("食物名称", required=True),
                "category": st.column_config.SelectboxColumn(
                    "类别",
                    options=["主食", "蛋白质", "蔬菜", "水果", "奶豆坚果", "饮品", "其他"],
                    required=True,
                ),
            },
            width="stretch",
            key="foods_editor",
        )

        uncertain = result.get("uncertain_items") or []
        if uncertain:
            with st.expander(f"有 {len(uncertain)} 项暂时无法确认", expanded=True):
                for item in uncertain:
                    st.write(f"- {item.get('description', '不确定食材')}：{item.get('reason', '无法确认具体种类')}")

        st.info("请确认识别结果，如有遗漏或错误可以直接修改。")
        analysis_exists = bool(st.session_state.get("analysis"))
        action_label = "保存修改并重新分析" if analysis_exists else "确认食物列表，进入分析"
        if st.button(action_label, type="primary"):
            confirmed = [
                {"name": str(row["name"]).strip(), "category": str(row["category"]).strip()}
                for row in edited.fillna("").to_dict("records")
                if str(row["name"]).strip() and str(row["category"]).strip()
            ]
            if not confirmed:
                st.warning("请至少保留或添加一项食物后再分析。")
            else:
                try:
                    with st.status("正在分析餐食结构……", expanded=True) as status:
                        st.write("调用 meal_analysis_v2")
                        analysis = run_analysis(analysis_url, token, confirmed)
                        st.session_state["confirmed_foods"] = confirmed
                        st.session_state["analysis"] = analysis
                        status.update(label="分析完成", state="complete", expanded=False)
                except (CozeAPIError, ValueError) as exc:
                    st.error(str(exc))

analysis = st.session_state.get("analysis")
if analysis:
    st.divider()
    st.markdown('<div class="section-title">餐食结构分析</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="result-summary">{escape(analysis.get("meal_summary", ""))}</div>',
        unsafe_allow_html=True,
    )

    structure = analysis.get("meal_structure") or {}
    state_labels = {
        "present": "已包含",
        "not_obvious": "未明显出现",
        "uncertain": "暂无法判断",
    }
    category_labels = (("主食", "staple"), ("蛋白质", "protein"), ("蔬菜", "vegetables"))
    columns = st.columns(3)
    for column, (label, key) in zip(columns, category_labels):
        value = state_labels.get(structure.get(key), "暂无法判断")
        column.markdown(
            f'<div class="structure-card"><div class="structure-label">{escape(label)}</div>'
            f'<div class="structure-value">{escape(value)}</div></div>',
            unsafe_allow_html=True,
        )

    issues = analysis.get("main_issues") or []
    if issues:
        st.markdown('<div class="result-block-title">主要问题</div>', unsafe_allow_html=True)
        for issue in issues:
            st.markdown(
                '<div class="issue-card">'
                f'<div class="card-title">{escape(issue.get("dimension", "餐食结构"))}</div>'
                f'{escape(issue.get("message", ""))}</div>',
                unsafe_allow_html=True,
            )
    else:
        st.markdown('<div class="result-block-title">本餐亮点</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="praise-card"><div class="card-title">搭配得很不错</div>'
            '主食、蛋白质和蔬菜都已包含，基础结构完整，值得继续保持。</div>',
            unsafe_allow_html=True,
        )

    suggestions = analysis.get("suggestions") or []
    if suggestions:
        heading = "一个小建议" if len(suggestions) == 1 else "可以这样调整"
        st.markdown(f'<div class="result-block-title">{heading}</div>', unsafe_allow_html=True)
        for index, suggestion in enumerate(suggestions, start=1):
            prefix = f"{index}. " if len(suggestions) > 1 else ""
            st.markdown(
                '<div class="suggestion-card">'
                f'<div class="card-title">{prefix}{escape(suggestion.get("title", "调整建议"))}</div>'
                f'{escape(suggestion.get("action", ""))}</div>',
                unsafe_allow_html=True,
            )

    friendly_report = analysis.get("friendly_report")
    if friendly_report:
        st.markdown(
            f'<div class="report-card">{escape(friendly_report)}</div>',
            unsafe_allow_html=True,
        )

    if analysis.get("limitations"):
        st.caption(f"分析说明：{analysis['limitations']}")
    if analysis.get("safety_note"):
        st.caption(analysis["safety_note"])

    st.caption("识别或建议不准确？可以在上方修改食物列表，再点击“保存修改并重新分析”。")
