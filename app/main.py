from __future__ import annotations

import os
from html import escape

import pandas as pd
import streamlit as st

try:
    from app.coze_client import CozeAPIError, run_analysis, run_recognition
    from app.product_logic import (
        FOOD_CATEGORIES,
        analysis_payload,
        build_knowledge_tips,
        build_meal_composition,
        category_evidence,
        infer_food_category,
        normalize_foods,
    )
except ModuleNotFoundError:
    from coze_client import CozeAPIError, run_analysis, run_recognition
    from product_logic import (
        FOOD_CATEGORIES,
        analysis_payload,
        build_knowledge_tips,
        build_meal_composition,
        category_evidence,
        infer_food_category,
        normalize_foods,
    )


st.set_page_config(
    page_title="食刻｜AI 餐食结构小助手",
    page_icon="🥗",
    layout="centered",
    initial_sidebar_state="collapsed",
)

if "uploader_key" not in st.session_state:
    st.session_state["uploader_key"] = 0
if "editor_version" not in st.session_state:
    st.session_state["editor_version"] = 0

current_step = 3 if st.session_state.get("analysis") else 2 if st.session_state.get("recognition") else 1

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
    .step {background: #f5f7f5; color: #738078; border: 1px solid #e5ebe6; border-radius: 14px;
      padding: .78rem .9rem; font-size: .9rem; text-align: center; font-weight: 600;}
    .step span {display: inline-grid; place-items: center; width: 1.45rem; height: 1.45rem;
      margin-right: .32rem; border-radius: 50%; background: #c9d2cc; color: white;}
    .section-title {margin-top: 1.2rem; color: #24302a; font-size: 1.3rem; font-weight: 750;}
    .privacy-note {margin: -.25rem 0 1rem; color: #718078; font-size: .82rem;}
    .edit-guide {margin: .5rem 0 1rem; padding: .9rem 1rem; border-radius: 14px;
      background: #eef7f1; border: 1px solid #d2e8d8; color: #315c40; line-height: 1.65;}
    .composition-card {margin: .55rem 0 1.1rem; padding: 1rem 1.1rem; border-radius: 16px;
      background: #f8fbf8; border: 1px solid #dce9df; color: #34453b; line-height: 1.75;}
    .structure-card {border: 1px solid #dce9df; border-radius: 16px; padding: 1rem;
      background: #fff; text-align: center; box-shadow: 0 5px 16px rgba(42,88,57,.05);}
    .structure-label {color: #6d7a72; font-size: .86rem; margin-bottom: .28rem;}
    .structure-value {color: #267c4d; font-size: 1.18rem; font-weight: 750;}
    .structure-evidence {color: #718078; font-size: .76rem; line-height: 1.45; margin-top: .35rem;}
    .result-summary {margin: .25rem 0 1.05rem; color: #34453b; font-size: 1.04rem; line-height: 1.72;}
    .result-block-title {margin: 1.35rem 0 .55rem; color: #24302a; font-size: 1.18rem; font-weight: 750;}
    .praise-card, .issue-card, .suggestion-card {border-radius: 16px; padding: .9rem 1.1rem;
      line-height: 1.72; margin: .55rem 0;}
    .praise-card {background: #edf8f0; border: 1px solid #cfe7d5; color: #246b43;}
    .issue-card {background: #fffbeb; border: 1px solid #f0e2ad; color: #80620a;}
    .suggestion-card {background: #f8fbf8; border: 1px solid #dce9df; color: #34453b;}
    .report-card {background: linear-gradient(135deg, #edf8f0, #f7fbf8); border: 1px solid #cfe7d5;
      border-left: 4px solid #43a36b; border-radius: 16px; padding: 1rem 1.15rem;
      color: #246b43; line-height: 1.72;}
    .knowledge-card {background: #f5f4ff; border: 1px solid #dedaf5; color: #514b78;
      border-radius: 16px; padding: .9rem 1.1rem; line-height: 1.72; margin: .55rem 0;}
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
      .structure-card {margin-bottom: .5rem; padding: .85rem;}
      .section-title {font-size: 1.18rem;}
      .result-block-title {font-size: 1.08rem; margin-top: 1.1rem;}
      .result-summary, .praise-card, .issue-card, .suggestion-card, .report-card {line-height: 1.62;}
      div.stButton > button {width: 100%;}
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

completed_steps = range(1, current_step)
completed_css = "\n".join(
    f".step:nth-child({step}) {{background:#edf8f0;color:#2f6f48;border-color:#cfe7d5;}}"
    f".step:nth-child({step}) span {{background:#43a36b;font-size:0;}}"
    f'.step:nth-child({step}) span::after {{content:"✓";font-size:.85rem;}}'
    for step in completed_steps
)
st.markdown(
    f"""<style>
    {completed_css}
    .step:nth-child({current_step}) {{background:#e6f4ea;color:#245f3d;border-color:#96caaa;
      box-shadow:0 4px 14px rgba(46,139,87,.10);}}
    .step:nth-child({current_step}) span {{background:#2e8b57;}}
    </style>""",
    unsafe_allow_html=True,
)

MAX_FILE_SIZE = 10 * 1024 * 1024

def setting(name: str, default: str = "") -> str:
    return os.getenv(name) or str(st.secrets.get(name, default))


token = setting("COZE_API_TOKEN")
workflow_url = setting("COZE_WORKFLOW_URL", "https://nwgs6rtrn3.coze.site/run")
analysis_url = setting("COZE_ANALYSIS_URL", "https://f567znb64x.coze.site/run")

if st.session_state.get("recognition") and not st.session_state.get("analysis"):
    if st.button("↻ 分析另一餐"):
        for key in ("recognition", "analysis", "confirmed_foods", "editable_foods", "foods_editor"):
            st.session_state.pop(key, None)
        st.session_state["uploader_key"] += 1
        st.session_state["editor_version"] += 1
        st.rerun()


def friendly_error(exc: Exception) -> str:
    status_code = getattr(exc, "status_code", None)
    if status_code == 402:
        return "AI 服务当前暂不可用，请稍后再试。"
    if status_code in (401, 403):
        return "AI 服务配置暂时不可用，请联系维护者。"
    if status_code == 429:
        return "当前使用人数较多，请稍后再试。"
    if status_code and status_code >= 500:
        return "AI 服务暂时繁忙，请稍后再试。"
    if isinstance(exc, ValueError):
        return "AI 返回结果暂时无法读取，请再试一次。"
    return "连接 AI 服务时出现问题，请稍后重试。"

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
                st.write("正在查看图片中的餐食，请稍候。")
                result = run_recognition(workflow_url, token, uploaded.getvalue(), uploaded.type)
                st.session_state["recognition"] = result
                st.session_state.pop("analysis", None)
                st.session_state.pop("confirmed_foods", None)
                st.session_state.pop("editable_foods", None)
                st.session_state["editor_version"] += 1
                status.update(label="识别完成", state="complete", expanded=False)
            st.rerun()
        except (CozeAPIError, ValueError) as exc:
            st.error(friendly_error(exc))

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
        st.markdown(
            '<div class="edit-guide"><strong>✏️ 请确认识别结果</strong><br>'
            '点击表格中的食物名称或类别即可修改；需要删除时请勾选该行。'
            '修改名称后，可点击“智能整理类别”让系统重新判断。</div>',
            unsafe_allow_html=True,
        )

        if "editable_foods" not in st.session_state:
            st.session_state["editable_foods"] = normalize_foods(result.get("foods") or [])

        table = pd.DataFrame(st.session_state["editable_foods"], columns=["name", "category", "delete"])
        table.index = range(1, len(table) + 1)
        edited = st.data_editor(
            table,
            hide_index=False,
            num_rows="fixed",
            column_config={
                "_index": st.column_config.NumberColumn("编号", disabled=True),
                "name": st.column_config.TextColumn("食物名称", required=True),
                "category": st.column_config.SelectboxColumn(
                    "类别",
                    options=list(FOOD_CATEGORIES),
                    required=True,
                ),
                "delete": st.column_config.CheckboxColumn("删除", default=False),
            },
            width="stretch",
            key=f"foods_editor_{st.session_state['editor_version']}",
        )

        current_rows = [
            {
                "name": str(row.get("name", "")).strip(),
                "category": str(row.get("category", "其他")).strip() or "其他",
                "delete": bool(row.get("delete", False)),
            }
            for row in edited.fillna("").to_dict("records")
        ]

        organize_col, add_col, delete_col = st.columns(3)
        with organize_col:
            if st.button("✨ 智能整理类别", use_container_width=True):
                changed = 0
                organized = []
                for row in current_rows:
                    inferred = infer_food_category(row["name"], row["category"])
                    changed += int(inferred != row["category"])
                    organized.append({**row, "category": inferred, "delete": False})
                st.session_state["editable_foods"] = organized
                st.session_state["editor_version"] += 1
                st.session_state["editor_notice"] = f"已更新 {changed} 项类别，请再次确认。" if changed else "当前类别无需调整。"
                st.rerun()
        with add_col:
            if st.button("＋ 添加食物", use_container_width=True):
                st.session_state["editable_foods"] = current_rows + [
                    {"name": "", "category": "其他", "delete": False}
                ]
                st.session_state["editor_version"] += 1
                st.rerun()
        with delete_col:
            delete_count = sum(row["delete"] for row in current_rows)
            if st.button(
                f"🗑 删除勾选项{f'（{delete_count}）' if delete_count else ''}",
                use_container_width=True,
                disabled=delete_count == 0,
            ):
                st.session_state["editable_foods"] = [
                    {**row, "delete": False} for row in current_rows if not row["delete"]
                ]
                st.session_state["editor_version"] += 1
                st.session_state["editor_notice"] = f"已删除 {delete_count} 项食物。"
                st.rerun()

        editor_notice = st.session_state.pop("editor_notice", None)
        if editor_notice:
            st.success(editor_notice)

        category_mismatches = [
            (row["name"], row["category"], infer_food_category(row["name"], row["category"]))
            for row in current_rows
            if row["name"]
            and not row["delete"]
            and infer_food_category(row["name"], row["category"]) != row["category"]
        ]
        if category_mismatches:
            names = "、".join(item[0] for item in category_mismatches[:3])
            st.warning(f"检测到 {names} 的名称与当前类别可能不一致，建议点击“智能整理类别”后再确认。")

        uncertain = result.get("uncertain_items") or []
        if uncertain:
            with st.expander(f"有 {len(uncertain)} 项暂时无法确认", expanded=True):
                for item in uncertain:
                    st.write(f"- {item.get('description', '不确定食材')}：{item.get('reason', '无法确认具体种类')}")

        st.info("确认前请检查食物名称与类别。最终分析将以你确认后的列表为准。")
        analysis_exists = bool(st.session_state.get("analysis"))
        action_label = "保存修改并重新分析" if analysis_exists else "确认食物列表，进入分析"
        if st.button(action_label, type="primary"):
            confirmed = [
                {"name": row["name"], "category": row["category"]}
                for row in current_rows
                if row["name"] and not row["delete"]
            ]
            if not confirmed:
                st.warning("请至少保留或添加一项食物后再分析。")
            else:
                try:
                    with st.status("正在分析餐食结构……", expanded=True) as status:
                        st.write("正在整理这餐的结构与建议，请稍候。")
                        analysis = run_analysis(analysis_url, token, analysis_payload(confirmed))
                        st.session_state["confirmed_foods"] = confirmed
                        st.session_state["editable_foods"] = [
                            {**food, "delete": False} for food in confirmed
                        ]
                        st.session_state["analysis"] = analysis
                        status.update(label="分析完成", state="complete", expanded=False)
                    st.rerun()
                except (CozeAPIError, ValueError) as exc:
                    st.error(friendly_error(exc))

analysis = st.session_state.get("analysis")
if analysis:
    confirmed_foods = st.session_state.get("confirmed_foods") or []
    st.divider()
    st.markdown('<div class="section-title">餐食结构分析</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="result-summary">{escape(analysis.get("meal_summary", ""))}</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="result-block-title">🍽️ 本餐食物构成</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="composition-card">{escape(build_meal_composition(confirmed_foods))}</div>',
        unsafe_allow_html=True,
    )

    structure = analysis.get("meal_structure") or {}
    evidence = category_evidence(confirmed_foods)
    state_labels = {
        "present": "已包含",
        "not_obvious": "未明显出现",
        "uncertain": "暂无法判断",
    }
    category_labels = (("主食", "staple"), ("蛋白质", "protein"), ("蔬菜", "vegetables"))
    columns = st.columns(3)
    for column, (label, key) in zip(columns, category_labels):
        value = state_labels.get(structure.get(key), "暂无法判断")
        evidence_text = "、".join(evidence.get(key) or []) or "食物列表中未明显看到"
        column.markdown(
            f'<div class="structure-card"><div class="structure-label">{escape(label)}</div>'
            f'<div class="structure-value">{escape(value)}</div>'
            f'<div class="structure-evidence">{escape(evidence_text)}</div></div>',
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
        st.markdown('<div class="result-block-title">✨ 本餐亮点</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="praise-card"><div class="card-title">搭配得很不错</div>'
            '主食、蛋白质和蔬菜都已包含，基础结构完整，值得继续保持。</div>',
            unsafe_allow_html=True,
        )

    suggestions = analysis.get("suggestions") or []
    if suggestions:
        heading = "💡 一个小建议" if len(suggestions) == 1 else "💡 可以这样调整"
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
        st.markdown('<div class="result-block-title">📝 给你的餐食小结</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="report-card">{escape(friendly_report)}</div>',
            unsafe_allow_html=True,
        )

    knowledge_tips = build_knowledge_tips(confirmed_foods)
    if knowledge_tips:
        st.markdown('<div class="result-block-title">💡 食物小知识</div>', unsafe_allow_html=True)
        for tip in knowledge_tips:
            st.markdown(f'<div class="knowledge-card">{escape(tip)}</div>', unsafe_allow_html=True)

    with st.expander("分析说明与使用范围"):
        if analysis.get("limitations"):
            st.caption(analysis["limitations"])
        if analysis.get("safety_note"):
            st.caption(analysis["safety_note"])

    st.markdown('<div class="result-block-title">接下来</div>', unsafe_allow_html=True)
    back_col, restart_col = st.columns(2)
    with back_col:
        if st.button("返回修改食物", use_container_width=True):
            st.session_state.pop("analysis", None)
            st.rerun()
    with restart_col:
        if st.button("分析另一餐", type="primary", use_container_width=True):
            for key in ("recognition", "analysis", "confirmed_foods", "editable_foods", "foods_editor"):
                st.session_state.pop(key, None)
            st.session_state["uploader_key"] += 1
            st.session_state["editor_version"] += 1
            st.rerun()
