from __future__ import annotations

import json
import base64
from typing import Any

import requests


class CozeAPIError(RuntimeError):
    """Raised when the Coze upload or workflow API returns an unusable response."""


def upload_file(file_bytes: bytes, filename: str, mime_type: str, token: str, upload_url: str) -> str:
    response = requests.post(
        upload_url,
        headers={"Authorization": f"Bearer {token}"},
        files={"file": (filename, file_bytes, mime_type)},
        timeout=60,
    )
    _raise_for_status(response, "图片上传失败")
    payload = response.json()
    file_id = (payload.get("data") or {}).get("id") or (payload.get("data") or {}).get("file_id")
    if not file_id:
        raise CozeAPIError(f"图片上传成功，但响应中没有 file_id：{payload}")
    return str(file_id)


def run_recognition(
    workflow_url: str,
    token: str,
    file_bytes: bytes,
    mime_type: str,
) -> dict[str, Any]:
    encoded = base64.b64encode(file_bytes).decode("ascii")
    data_url = f"data:{mime_type};base64,{encoded}"
    response = requests.post(
        workflow_url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={"meal_image": {"url": data_url, "file_type": "image"}},
        timeout=180,
    )
    _raise_for_status(response, "餐食识别失败")
    return normalize_result(response.json(), "analyzable", ("recognition_result", "output", "data"))


def run_analysis(
    workflow_url: str,
    token: str,
    confirmed_foods: list[dict[str, str]],
) -> dict[str, Any]:
    response = requests.post(
        workflow_url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={"confirmed_foods": confirmed_foods},
        timeout=180,
    )
    _raise_for_status(response, "餐食结构分析失败")
    return normalize_result(response.json(), "meal_summary", ("analysis_result", "output", "data"))


def normalize_result(
    payload: Any,
    expected_key: str,
    envelope_keys: tuple[str, ...],
) -> dict[str, Any]:
    """Unwrap common Coze response envelopes and JSON-string outputs."""
    value = payload
    for _ in range(6):
        if isinstance(value, str):
            value = json.loads(value)
            continue
        if not isinstance(value, dict):
            break
        if expected_key in value:
            return value
        for key in envelope_keys:
            if key in value:
                value = value[key]
                break
        else:
            break
    if isinstance(value, dict) and expected_key in value:
        return value
    raise CozeAPIError(f"无法识别工作流返回结构：{payload}")


def _raise_for_status(response: requests.Response, prefix: str) -> None:
    if response.ok:
        return
    body = response.text[:1000]
    raise CozeAPIError(f"{prefix}（HTTP {response.status_code}）：{body}")
