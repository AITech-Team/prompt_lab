from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import PromptEvaluation, PromptHistory
from typing import List

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/")
def evaluate_response(data: dict, db: Session = Depends(get_db)):
    history_id = data["history_id"]
    score = data["score"]
    comment = data.get("comment", "")
    evaluator = data.get("evaluator", "user")
    history = db.query(PromptHistory).filter_by(id=history_id).first()
    if not history:
        raise HTTPException(404, "历史记录不存在")
    evaluation = PromptEvaluation(
        history_id=history_id,
        score=score,
        comment=comment,
        evaluator=evaluator
    )
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)
    return {"id": evaluation.id}

@router.get("/history/{history_id}", response_model=List[dict])
def get_evaluations(history_id: int, db: Session = Depends(get_db)):
    evaluations = db.query(PromptEvaluation).filter_by(history_id=history_id).all()
    return [
        {"id": e.id, "score": e.score, "comment": e.comment, "evaluator": e.evaluator, "created_at": e.created_at} for e in evaluations
    ] 