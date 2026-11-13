from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.analysis.model import Analysis
from app.analysis.model_gateway import AnalysisModel
from app.analysis.schema import AnalysisRequest, ModelOutput
from app.finding.model import Finding
from app.finding_medication.model import FindingMedication
from app.medication_record.schema import MedicationRecordCreate
from app.medication_record.service import create_record


def get_owned(db: Session, user_id: int, analysis_id: int) -> Analysis:
    analysis = db.scalar(select(Analysis).where(Analysis.analysis_id == analysis_id, Analysis.user_id == user_id))
    if analysis is None:
        raise HTTPException(404, "분석 기록을 찾을 수 없습니다.")
    return analysis


def analyze(db: Session, user_id: int | None, body: AnalysisRequest, model: AnalysisModel,
            guest_session_id: int | None = None) -> Analysis:
    try:
        output = ModelOutput.model_validate(model.analyze(body))
        snapshot = body.model_dump(mode="json")
        valid_keys = {(item.line_no, item.source_index) for group in body.medications for item in group.drugs}
        for finding in output.result.findings:
            keys = [(ref.line_no, ref.source_index) for ref in finding.medication_refs]
            if len(keys) != len(set(keys)) or not set(keys).issubset(valid_keys):
                raise ValueError("모델이 존재하지 않거나 중복된 약을 참조했습니다.")
    except (ValidationError, ValueError, TypeError) as exc:
        raise HTTPException(502, "모델 분석 결과 형식 또는 약 연결 정보가 올바르지 않습니다.") from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(502, "분석 모델 실행에 실패했습니다.") from exc
    # 모델 성공 및 참조 검증 후에만 기록을 생성하고 한 트랜잭션으로 저장합니다.
    try:
        if guest_session_id is not None:
            from datetime import datetime, timezone
            from app.guest.model import GuestSession
            guest = db.get(GuestSession, guest_session_id)
            if guest is None or guest.expires_at <= datetime.now(timezone.utc):
                raise HTTPException(401, "비회원 이용 시간이 만료되었습니다.")
        record = create_record(db, user_id, MedicationRecordCreate(medications=body.medications), guest_session_id)
        analysis = Analysis(user_id=user_id, guest_session_id=guest_session_id, medication_record_id=record.medication_record_id,
                            rule_version=output.rule_version, input_snapshot=snapshot,
                            result=output.result.model_dump(mode="json"))
        db.add(analysis)
        db.flush()
        for item in output.result.findings:
            finding = Finding(analysis_id=analysis.analysis_id, result_finding_id=item.finding_id,
                              rule_type=item.rule_type, severity=item.severity,
                              details=item.model_dump(mode="json", exclude={"finding_id", "rule_type", "severity", "medication_refs"}))
            db.add(finding)
            db.flush()
            for ref in item.medication_refs:
                db.add(FindingMedication(finding_id=finding.finding_id,
                       medication_record_id=record.medication_record_id,
                       line_no=ref.line_no, source_index=ref.source_index))
        db.commit()
        db.refresh(analysis)
        return analysis
    except Exception:
        db.rollback()
        raise


def delete_all(db: Session, user_id: int):
    db.execute(delete(Analysis).where(Analysis.user_id == user_id))
    db.commit()
