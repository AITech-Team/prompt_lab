import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.models import LLMModel, User
from app.services.model_adapter import ModelAdapter
from app.routers.auth import get_current_user
from typing import List
from pydantic import BaseModel, Field, validator
from sqlalchemy.sql import func

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# 将types路由放在最前面，避免与/{model_id}路由冲突
@router.get("/types")
def get_model_types():
    """获取所有支持的模型类型"""
    try:
        logger.info("获取所有支持的模型类型")
        types = ModelAdapter.get_model_types()
        logger.info(f"返回模型类型: {types}")
        return {"types": types}
    except Exception as e:
        logger.error(f"获取模型类型失败: {str(e)}")
        # 即使出错也返回默认列表
        default_types = ['openai', 'anthropic', 'deepseek', 'qwen', 'doubao', 
            'chatglm', 'zhipu', 'wenxin', 'spark', 'modelscope', 'local']
        logger.info(f"返回默认模型类型: {default_types}")
        return {"types": default_types}

class ModelCreate(BaseModel):
    name: str = Field(..., description="模型名称")
    provider: str = Field(..., description="模型提供商")
    api_key: str = Field(..., description="API密钥")
    base_url: str = Field("", description="API基础URL")

    @validator('provider')
    def validate_provider(cls, v):
        allowed_providers = ModelAdapter.get_model_types()
        if v not in allowed_providers:
            raise ValueError(f"不支持的模型类型，支持的类型有：{', '.join(allowed_providers)}")
        return v

    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError("模型名称不能为空")
        return v.strip()

    @validator('api_key')
    def validate_api_key(cls, v):
        if not v.strip():
            raise ValueError("API密钥不能为空")
        return v.strip()

@router.get("/")
def list_models(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取当前用户的所有模型"""
    try:
        models = db.query(LLMModel).filter_by(user_id=current_user.id, is_deleted=False).all()
        return [
            {
                "id": m.id,
                "name": m.name,
                "provider": m.provider,
                "base_url": m.base_url,
                "has_api_key": m.has_api_key,
                "created_at": m.created_at.isoformat() if m.created_at else None,
                "updated_at": m.updated_at.isoformat() if m.updated_at else None
            } for m in models
        ]
    except Exception as e:
        logger.error(f"Failed to list models: {str(e)}")
        raise HTTPException(500, f"获取模型列表失败: {str(e)}")

@router.get("/{model_id}")
def get_model(model_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取指定模型详情"""
    try:
        model = db.query(LLMModel).filter_by(id=model_id, user_id=current_user.id, is_deleted=False).first()
        if not model:
            raise HTTPException(404, "模型不存在")
            
        return {
            "id": model.id,
            "name": model.name,
            "provider": model.provider,
            "base_url": model.base_url,
            "api_key": model.api_key,
            "has_api_key": model.has_api_key,
            "created_at": model.created_at.isoformat() if model.created_at else None,
            "updated_at": model.updated_at.isoformat() if model.updated_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get model: {str(e)}")
        raise HTTPException(500, f"获取模型详情失败: {str(e)}")

@router.post("/")
def create_model(model_data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        # 检查是否存在同名未删除模型
        existing_active = db.query(LLMModel).filter_by(
            name=model_data["name"],
            user_id=current_user.id,
            is_deleted=False
        ).first()
        
        if existing_active:
            raise HTTPException(400, "模型名称已存在，请使用其他名称")
            
        # 检查是否存在同名已删除模型
        existing_deleted = db.query(LLMModel).filter_by(
            name=model_data["name"],
            user_id=current_user.id,
            is_deleted=True
        ).first()
        
        if existing_deleted:
            # 如果存在已删除的同名模型，更新它
            for key, value in model_data.items():
                setattr(existing_deleted, key, value)
            existing_deleted.is_deleted = False
            existing_deleted.updated_at = func.now()
            model = existing_deleted
        else:
            # 创建新模型
            model_data["user_id"] = current_user.id
            model = LLMModel(**model_data)
            db.add(model)
            
        db.commit()
        db.refresh(model)
        
        return {
            "id": model.id,
            "name": model.name,
            "message": "创建成功"
        }
        
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Model creation failed (integrity error): {str(e)}")
        raise HTTPException(400, "模型创建失败：数据完整性错误")
        
    except HTTPException as e:
        raise e
        
    except Exception as e:
        db.rollback()
        logger.error(f"Model creation failed: {str(e)}")
        raise HTTPException(500, f"模型创建失败: {str(e)}")

@router.put("/{model_id}")
def update_model(model_id: int, model_data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        model = db.query(LLMModel).filter_by(id=model_id, user_id=current_user.id, is_deleted=False).first()
        if not model:
            raise HTTPException(404, "模型不存在")
            
        # 检查新名称是否与其他模型冲突
        if "name" in model_data and model_data["name"] != model.name:
            existing = db.query(LLMModel).filter_by(
                name=model_data["name"],
                user_id=current_user.id,
                is_deleted=False
            ).first()
            if existing:
                raise HTTPException(400, "模型名称已存在")
        
        # 更新模型
        for key, value in model_data.items():
            if key != "user_id":  # 不允许修改用户ID
                setattr(model, key, value)
            
        db.commit()
        
        return {
            "id": model.id,
            "name": model.name,
            "message": "更新成功"
        }
        
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Model update failed (integrity error): {str(e)}")
        raise HTTPException(400, "模型更新失败：数据完整性错误")
        
    except HTTPException as e:
        raise e
        
    except Exception as e:
        db.rollback()
        logger.error(f"Model update failed: {str(e)}")
        raise HTTPException(500, f"模型更新失败: {str(e)}")

@router.delete("/{model_id}")
def delete_model(model_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        model = db.query(LLMModel).filter_by(id=model_id, user_id=current_user.id, is_deleted=False).first()
        if not model:
            raise HTTPException(404, "模型不存在")
        
        model.is_deleted = True
        db.commit()
        
        return {"message": "删除成功"}
        
    except HTTPException as e:
        raise e
        
    except Exception as e:
        db.rollback()
        logger.error(f"Model deletion failed: {str(e)}")
        raise HTTPException(500, f"删除模型失败: {str(e)}")

@router.post("/{model_id}/test")
def test_model(model_id: int, db: Session = Depends(get_db)):
    try:
        model = db.query(LLMModel).filter_by(id=model_id, is_deleted=False).first()
        if not model:
            raise HTTPException(404, "模型不存在")
        
        try:
            adapter = ModelAdapter(
                provider=model.provider,
                api_key=model.api_key,
                base_url=model.base_url
            )
            
            if not adapter.validate_api_key():
                raise HTTPException(400, "API密钥验证失败")
        except ValueError as e:
            raise HTTPException(400, str(e))
        
        return {"msg": "测试成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to test model: {str(e)}")
        raise HTTPException(500, f"测试模型失败: {str(e)}")

@router.post("/{model_id}/restore")
def restore_model(model_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        model = db.query(LLMModel).filter_by(id=model_id, user_id=current_user.id, is_deleted=True).first()
        if not model:
            raise HTTPException(404, "模型不存在或未被删除")
            
        # 检查是否存在同名未删除模型
        existing = db.query(LLMModel).filter_by(
            name=model.name,
            user_id=current_user.id,
            is_deleted=False
        ).first()
        if existing:
            raise HTTPException(400, "存在同名模型，无法恢复")
        
        model.is_deleted = False
        db.commit()
        
        return {"message": "恢复成功"}
        
    except HTTPException as e:
        raise e
        
    except Exception as e:
        db.rollback()
        logger.error(f"Model restoration failed: {str(e)}")
        raise HTTPException(500, f"恢复模型失败: {str(e)}") 