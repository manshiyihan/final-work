import re
import json
from pathlib import Path
from typing import Dict

from app.core.config import RISK_PROFILE_PATH


def _load_risk_profile() -> Dict:
    try:
        with open(RISK_PROFILE_PATH, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return {
            "rules": {
                "spoof_label_values": ["spoof"],
                "unknown_speaker_values": ["unknown", "未知"],
            },
            "scores": {"fraud_risk": 0.9, "identity_unknown": 0.7, "pass": 0.1},
        }

def extract_speaker_name(mfa_output: str) -> str:
    text = (mfa_output or "").strip()
    if not text:
        return "unknown"
    if "不在库中" in text:
        return "unknown"

    match = re.search(r"匹配人员[:：]\s*([^\r\n]+)", text)
    if match:
        name = match.group(1).strip()
        return name or "unknown"

    match_en = re.search(r"matched\s*speaker[:：]\s*([^\r\n]+)", text, flags=re.IGNORECASE)
    if match_en:
        name = match_en.group(1).strip()
        return name or "unknown"

    return "unknown"


def parse_outputs(mfa_output: str, rawgat_output: str, mfa_json: Dict = None, rawgat_json: Dict = None) -> Dict[str, str]:
    mfa_json = mfa_json or {}
    rawgat_json = rawgat_json or {}
    profile = _load_risk_profile()
    spoof_values = set(profile.get("rules", {}).get("spoof_label_values", ["spoof"]))
    unknown_values = set(profile.get("rules", {}).get("unknown_speaker_values", ["unknown", "未知"]))
    scores = profile.get("scores", {})

    mfa_lower = mfa_output.lower()
    raw_lower = rawgat_output.lower()

    speaker_result = mfa_json.get("speaker_name") or extract_speaker_name(mfa_output)

    raw_label = str(rawgat_json.get("label", "")).lower().strip()
    if raw_label in spoof_values or any(token in raw_lower for token in ["fake", "spoof", "伪造", "虚假"]):
        spoof_result = "spoof"
    elif rawgat_output.strip():
        spoof_result = "bonafide"
    else:
        spoof_result = "unknown"

    if spoof_result == "spoof":
        risk_score = float(scores.get("fraud_risk", 0.9))
        final_label = "fraud_risk"
    elif speaker_result in unknown_values:
        risk_score = float(scores.get("identity_unknown", 0.7))
        final_label = "identity_unknown"
    else:
        risk_score = float(scores.get("pass", 0.1))
        final_label = "pass"

    return {
        "speaker_result": speaker_result,
        "spoof_result": spoof_result,
        "risk_score": risk_score,
        "final_label": final_label,
    }
