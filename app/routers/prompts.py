from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Prompt, LLMModel, PromptTemplate, User
from app.routers.auth import get_current_user
from app.services.model_adapter import ModelAdapter
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
def list_prompts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        prompts = db.query(Prompt).filter_by(user_id=current_user.id, is_deleted=False).all()
        return [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "content": p.content,
                "variables": p.variables,
                "model_id": p.model_id,
                "template_id": p.template_id,
                "created_at": p.created_at,
                "updated_at": p.updated_at
            } for p in prompts
        ]
    except Exception as e:
        logger.error(f"Failed to list prompts: {str(e)}")
        raise HTTPException(500, f"获取提示词列表失败: {str(e)}")

@router.get("/{prompt_id}")
def get_prompt(prompt_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取指定提示词详情"""
    try:
        prompt = db.query(Prompt).filter_by(id=prompt_id, user_id=current_user.id, is_deleted=False).first()
        if not prompt:
            raise HTTPException(404, "提示词不存在")
            
        return {
            "id": prompt.id,
            "name": prompt.name,
            "description": prompt.description,
            "content": prompt.content,
            "variables": prompt.variables,
            "model_id": prompt.model_id,
            "template_id": prompt.template_id,
            "created_at": prompt.created_at,
            "updated_at": prompt.updated_at
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get prompt: {str(e)}")
        raise HTTPException(500, f"获取提示词详情失败: {str(e)}")

@router.post("/")
def create_prompt(data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        if db.query(Prompt).filter_by(name=data["name"], user_id=current_user.id, is_deleted=False).first():
            raise HTTPException(400, "提示词名称已存在")
        
        # 验证模型是否存在且属于当前用户
        model = None
        if "model_id" in data:
            model = db.query(LLMModel).filter_by(id=data["model_id"], user_id=current_user.id, is_deleted=False).first()
            if not model:
                raise HTTPException(404, "模型不存在或无权访问")
        
        # 验证模板是否存在且属于当前用户
        template = None
        if "template_id" in data:
            template = db.query(PromptTemplate).filter_by(id=data["template_id"], user_id=current_user.id, is_deleted=False).first()
            if not template:
                raise HTTPException(404, "模板不存在或无权访问")
        
        prompt = Prompt(
            name=data["name"],
            description=data.get("description", ""),
            content=data["content"],
            variables=data.get("variables", {}),
            model_id=data.get("model_id"),
            template_id=data.get("template_id"),
            user_id=current_user.id
        )
        
        db.add(prompt)
        db.commit()
        db.refresh(prompt)
        return {"id": prompt.id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create prompt: {str(e)}")
        db.rollback()
        raise HTTPException(500, f"创建提示词失败: {str(e)}")

@router.put("/{prompt_id}")
def update_prompt(prompt_id: int, data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        prompt = db.query(Prompt).filter_by(id=prompt_id, user_id=current_user.id, is_deleted=False).first()
        if not prompt:
            raise HTTPException(404, "提示词不存在或无权访问")
        
        if "name" in data and data["name"] != prompt.name:
            if db.query(Prompt).filter_by(name=data["name"], user_id=current_user.id, is_deleted=False).first():
                raise HTTPException(400, "提示词名称已存在")
            prompt.name = data["name"]
        
        if "model_id" in data:
            model = db.query(LLMModel).filter_by(id=data["model_id"], user_id=current_user.id, is_deleted=False).first()
            if not model:
                raise HTTPException(404, "模型不存在或无权访问")
            prompt.model_id = data["model_id"]
        
        if "template_id" in data:
            template = db.query(PromptTemplate).filter_by(id=data["template_id"], user_id=current_user.id, is_deleted=False).first()
            if not template:
                raise HTTPException(404, "模板不存在或无权访问")
            prompt.template_id = data["template_id"]
        
        if "description" in data:
            prompt.description = data["description"]
        if "content" in data:
            prompt.content = data["content"]
        if "variables" in data:
            prompt.variables = data["variables"]
        
        db.commit()
        db.refresh(prompt)
        return {"msg": "更新成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update prompt: {str(e)}")
        db.rollback()
        raise HTTPException(500, f"更新提示词失败: {str(e)}")

@router.delete("/{prompt_id}")
def delete_prompt(prompt_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        prompt = db.query(Prompt).filter_by(id=prompt_id, user_id=current_user.id, is_deleted=False).first()
        if not prompt:
            raise HTTPException(404, "提示词不存在或无权访问")
        
        prompt.is_deleted = True
        db.commit()
        return {"msg": "删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete prompt: {str(e)}")
        db.rollback()
        raise HTTPException(500, f"删除提示词失败: {str(e)}")

@router.post("/{prompt_id}/test")
def test_prompt(prompt_id: int, data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        prompt = db.query(Prompt).filter_by(id=prompt_id, user_id=current_user.id, is_deleted=False).first()
        if not prompt:
            raise HTTPException(404, "提示词不存在或无权访问")
        
        if not prompt.model_id:
            raise HTTPException(400, "未指定模型")
        
        model = db.query(LLMModel).filter_by(id=prompt.model_id, user_id=current_user.id, is_deleted=False).first()
        if not model:
            raise HTTPException(404, "模型不存在或无权访问")
        
        # 创建模型适配器
        adapter = ModelAdapter(
            provider=model.provider,
            api_key=model.api_key,
            base_url=model.base_url
        )
        
        # 验证API密钥
        if not adapter.validate_api_key():
            raise HTTPException(400, "API密钥验证失败")
        
        # 准备提示词内容
        content = prompt.content
        if prompt.template_id:
            template = db.query(PromptTemplate).filter_by(id=prompt.template_id, user_id=current_user.id, is_deleted=False).first()
            if template:
                content = template.content
        
        # 替换变量
        variables = data.get("variables", {})
        for key, value in variables.items():
            content = content.replace(f"{{{key}}}", str(value))
        
        # 发送请求
        response = adapter.send_prompt(content)
        
        # 评估响应
        evaluator = ResponseEvaluator()
        evaluation = evaluator.evaluate_response(content, response)
        
        return {
            "content": response,
            "evaluation": evaluation
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to test prompt: {str(e)}")
        raise HTTPException(500, f"测试提示词失败: {str(e)}")

@router.post("/export")
def export_prompts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        prompts = db.query(Prompt).filter_by(user_id=current_user.id, is_deleted=False).all()
        
        # 准备CSV数据
        output = StringIO()
        writer = csv.writer(output)
        
        # 写入表头
        writer.writerow([
            "ID", "名称", "描述", "内容", "变量", 
            "模型ID", "模板ID", "创建时间", "更新时间"
        ])
        
        # 写入数据
        for p in prompts:
            writer.writerow([
                p.id, p.name, p.description, p.content,
                json.dumps(p.variables, ensure_ascii=False),
                p.model_id, p.template_id,
                p.created_at, p.updated_at
            ])
        
        # 准备响应
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment;filename=prompts.csv"}
        )
    except Exception as e:
        logger.error(f"Failed to export prompts: {str(e)}")
        raise HTTPException(500, f"导出提示词失败: {str(e)}") 