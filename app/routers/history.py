from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import PromptHistory, PromptTemplate, LLMModel, User
from app.routers.auth import get_current_user
from typing import List
import csv
import io

router = APIRouter()

@router.get("/", response_model=List[dict])
def list_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    history = db.query(PromptHistory).filter_by(user_id=current_user.id).all()
    return [
        {
            "id": h.id,
            "template_id": h.template_id,
            "template_name": h.template.name if h.template else None,
            "variables": h.variables,
            "rendered_prompt": h.rendered_prompt,
            "model_id": h.model_id,
            "model_name": h.model.name if h.model else None,
            "response": h.response,
            "created_at": h.created_at.isoformat() if h.created_at else None
        } for h in history
    ]

@router.get("/export")
def export_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    history = db.query(PromptHistory).filter_by(user_id=current_user.id).all()
    output = io.StringIO()
    # 添加BOM头，使Excel能正确识别UTF-8编码的中文
    output.write('\ufeff')
    writer = csv.writer(output)
    writer.writerow(["ID", "模板", "变量", "渲染后Prompt", "模型", "响应", "时间"])
    for h in history:
        writer.writerow([
            h.id,
            h.template.name if h.template else "",
            str(h.variables),
            h.rendered_prompt,
            h.model.name if h.model else "",
            h.response,
            h.created_at
        ])
    return Response(
        content=output.getvalue(), 
        media_type="text/csv; charset=utf-8-sig",
        headers={"Content-Disposition": f"attachment; filename=prompt_history.csv"}
    )

@router.get("/{history_id}")
def get_history(history_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    h = db.query(PromptHistory).filter_by(id=history_id, user_id=current_user.id).first()
    if not h:
        raise HTTPException(404, "历史记录不存在或无权访问")
    return {
        "id": h.id,
        "template_id": h.template_id,
        "template_name": h.template.name if h.template else None,
        "variables": h.variables,
        "rendered_prompt": h.rendered_prompt,
        "model_id": h.model_id,
        "model_name": h.model.name if h.model else None,
        "response": h.response,
        "created_at": h.created_at
    } 