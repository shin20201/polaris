from copy import deepcopy

from app.analysis.model import Analysis
from app.medication_record.schema import MedicationItem
from app.notification.schema import NotificationCreate


SAFETY_NOTICE = "이 앱은 확인이 필요한 항목을 찾아 알려 줍니다. 약을 끊거나 줄이거나 바꾸는 결정은 의사·약사가 합니다."


def build_payload(analysis: Analysis, body: NotificationCreate, subject_name: str) -> dict:
    """분석 당시 데이터 중 사용자가 선택한 항목만 공유합니다. 사진·지도는 제외합니다."""
    payload = {
        "subject_name": subject_name,
        "analyzed_at": analysis.analyzed_at.isoformat(),
        "sharing": {"findings": body.share_findings, "medications": body.share_medications,
                    "map": False, "photos": False},
        "safety_notice": SAFETY_NOTICE,
    }
    if body.share_findings:
        sentences = analysis.result.get("sentences", [])
        findings = []
        for item in analysis.result.get("findings", []):
            finding = {
                "finding_id": item["finding_id"], "rule_type": item["rule_type"],
                "severity": item["severity"], "title": item.get("title") or item["rule_type"],
                "sentences": [],
            }
            for sentence in sentences:
                if sentence.get("finding_id") == item["finding_id"]:
                    finding["sentences"].append({key: sentence[key] for key in ("text", "action_text")
                                                  if isinstance(sentence.get(key), str)})
            # 모델이 제공하지 않은 행동 안내는 생성하지 않습니다.
            if isinstance(item.get("action_text"), str):
                finding["action_text"] = item["action_text"]
            findings.append(finding)
        payload["findings"] = findings
        payload["finding_count"] = len(findings)
        payload["analysis_limitations"] = {key: deepcopy(analysis.result[key]) for key in (
            "is_lower_bound", "lower_bound_reason", "lower_bound_notice",
        ) if key in analysis.result}
    if body.share_medications:
        groups = []
        allowed = set(MedicationItem.model_fields)
        for group in analysis.input_snapshot["medications"]:
            groups.append({"institution_name": group.get("institution_name"), "drugs": [
                {key: deepcopy(value) for key, value in drug.items() if key in allowed}
                for drug in group["drugs"]
            ]})
        payload["medications"] = groups
        payload["medication_count"] = sum(len(group["drugs"]) for group in groups)
        # 기관명이 없는 경우 실제 기관 수를 임의로 추정하지 않습니다.
        payload["institution_count"] = len({group["institution_name"] for group in groups if group["institution_name"]})
        payload["unknown_institution_group_count"] = sum(group["institution_name"] is None for group in groups)
    return payload
