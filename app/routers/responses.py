from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Response, Prompt, User
from app.routers.auth import get_current_user
from app.services.evaluator import ResponseEvaluator
from typing import List
import logging
import json
import csv
from io import StringIO
from fastapi.responses import StreamingResponse

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", response_model=List[dict])
def list_responses(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        responses = db.query(Response).filter_by(user_id=current_user.id, is_deleted=False).all()
        return [
            {
                "id": r.id,
                "prompt_id": r.prompt_id,
                "content": r.content,
                "evaluation": r.evaluation,
                "created_at": r.created_at,
                "updated_at": r.updated_at
            } for r in responses
        ]
    except Exception as e:
        logger.error(f"Failed to list responses: {str(e)}")
        raise HTTPException(500, f"获取响应列表失败: {str(e)}")

@router.get("/{response_id}")
def get_response(response_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取指定响应详情"""
    try:
        response = db.query(Response).filter_by(id=response_id, user_id=current_user.id, is_deleted=False).first()
        if not response:
            raise HTTPException(404, "响应不存在或无权访问")
            
        return {
            "id": response.id,
            "prompt_id": response.prompt_id,
            "content": response.content,
            "evaluation": response.evaluation,
            "created_at": response.created_at,
            "updated_at": response.updated_at
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get response: {str(e)}")
        raise HTTPException(500, f"获取响应详情失败: {str(e)}")

@router.post("/")
def create_response(data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        # 验证提示词是否存在且属于当前用户
        prompt = None
        if "prompt_id" in data:
            prompt = db.query(Prompt).filter_by(id=data["prompt_id"], user_id=current_user.id, is_deleted=False).first()
            if not prompt:
                raise HTTPException(404, "提示词不存在或无权访问")
        
        # 评估响应
        evaluator = ResponseEvaluator()
        # 如果有关联的提示词，使用提示词内容；否则使用默认提示词
        prompt_content = prompt.content if prompt else "请评估以下内容的质量"
        evaluation = evaluator.evaluate_response(prompt_content, data["content"])
        
        response = Response(
            prompt_id=data.get("prompt_id"),
            content=data["content"],
            evaluation=evaluation,
            user_id=current_user.id
        )
        
        db.add(response)
        db.commit()
        db.refresh(response)
        return {"id": response.id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create response: {str(e)}")
        db.rollback()
        raise HTTPException(500, f"创建响应失败: {str(e)}")

@router.put("/{response_id}")
def update_response(response_id: int, data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        response = db.query(Response).filter_by(id=response_id, user_id=current_user.id, is_deleted=False).first()
        if not response:
            raise HTTPException(404, "响应不存在或无权访问")
        
        if "prompt_id" in data:
            prompt = db.query(Prompt).filter_by(id=data["prompt_id"], user_id=current_user.id, is_deleted=False).first()
            if not prompt:
                raise HTTPException(404, "提示词不存在或无权访问")
            response.prompt_id = data["prompt_id"]
        
        if "content" in data:
            response.content = data["content"]
            # 重新评估响应
            evaluator = ResponseEvaluator()
            # 获取关联的提示词内容
            prompt = db.query(Prompt).filter_by(id=response.prompt_id, user_id=current_user.id, is_deleted=False).first() if response.prompt_id else None
            prompt_content = prompt.content if prompt else "请评估以下内容的质量"
            response.evaluation = evaluator.evaluate_response(prompt_content, data["content"])
        
        db.commit()
        db.refresh(response)
        return {"msg": "更新成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update response: {str(e)}")
        db.rollback()
        raise HTTPException(500, f"更新响应失败: {str(e)}")

@router.delete("/{response_id}")
def delete_response(response_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        response = db.query(Response).filter_by(id=response_id, user_id=current_user.id, is_deleted=False).first()
        if not response:
            raise HTTPException(404, "响应不存在或无权访问")
        
        response.is_deleted = True
        db.commit()
        return {"msg": "删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete response: {str(e)}")
        db.rollback()
        raise HTTPException(500, f"删除响应失败: {str(e)}")

@router.get("/export")
def export_responses(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        responses = db.query(Response).filter_by(user_id=current_user.id, is_deleted=False).all()
        
        # 准备CSV数据
        output = StringIO()
        writer = csv.writer(output)
        
        # 写入表头
        writer.writerow([
            "ID", "提示词ID", "内容", "评估结果",
            "创建时间", "更新时间"
        ])
        
        # 写入数据
        for r in responses:
            writer.writerow([
                r.id, r.prompt_id, r.content,
                json.dumps(r.evaluation, ensure_ascii=False),
                r.created_at, r.updated_at
            ])
        
        # 准备响应
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment;filename=responses.csv"}
        )
    except Exception as e:
        logger.error(f"Failed to export responses: {str(e)}")
        raise HTTPException(500, f"导出响应失败: {str(e)}") 