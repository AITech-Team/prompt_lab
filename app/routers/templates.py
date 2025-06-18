from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.models import PromptTemplate, User
from app.routers.auth import get_current_user
from app.websocket import manager
from typing import List
import logging
import json
from sqlalchemy.sql import func

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", response_model=List[dict])
def list_templates(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        templates = db.query(PromptTemplate).filter_by(user_id=current_user.id, is_deleted=False).all()
        return [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "content": t.content,
                "variables": t.variables,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "updated_at": t.updated_at.isoformat() if t.updated_at else None
            } for t in templates
        ]
    except Exception as e:
        logger.error(f"Failed to list templates: {str(e)}")
        raise HTTPException(500, f"获取模板列表失败: {str(e)}")

@router.get("/{template_id}")
def get_template(template_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取指定模板详情"""
    try:
        template = db.query(PromptTemplate).filter_by(id=template_id, user_id=current_user.id, is_deleted=False).first()
        if not template:
            raise HTTPException(404, "模板不存在")
            
        return {
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "content": template.content,
            "variables": template.variables,
            "created_at": template.created_at.isoformat() if template.created_at else None,
            "updated_at": template.updated_at.isoformat() if template.updated_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get template: {str(e)}")
        raise HTTPException(500, f"获取模板详情失败: {str(e)}")

@router.post("/")
async def create_template(template_data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        # 检查是否存在同名未删除模板
        existing_active = db.query(PromptTemplate).filter_by(
            name=template_data["name"],
            user_id=current_user.id,
            is_deleted=False
        ).first()
        
        if existing_active:
            raise HTTPException(400, "模板名称已存在，请使用其他名称")
            
        # 检查是否存在同名已删除模板
        existing_deleted = db.query(PromptTemplate).filter_by(
            name=template_data["name"],
            user_id=current_user.id,
            is_deleted=True
        ).first()
        
        if existing_deleted:
            # 如果存在已删除的同名模板，更新它
            for key, value in template_data.items():
                setattr(existing_deleted, key, value)
            existing_deleted.is_deleted = False
            existing_deleted.updated_at = func.now()
            template = existing_deleted
        else:
            # 创建新模板
            template_data["user_id"] = current_user.id
            template = PromptTemplate(**template_data)
            db.add(template)
            
        db.commit()
        db.refresh(template)
        
        # 广播创建消息
        try:
            await manager.broadcast_json({
                "type": "template_created",
                "data": {
                    "id": template.id,
                    "name": template.name,
                    "user_id": current_user.id
                }
            })
        except Exception as e:
            logger.error(f"Failed to broadcast template creation: {str(e)}")
        
        return {
            "id": template.id,
            "name": template.name,
            "message": "创建成功"
        }
        
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Template creation failed (integrity error): {str(e)}")
        raise HTTPException(400, "模板创建失败：数据完整性错误")
        
    except HTTPException as e:
        raise e
        
    except Exception as e:
        db.rollback()
        logger.error(f"Template creation failed: {str(e)}")
        raise HTTPException(500, f"模板创建失败: {str(e)}")

@router.put("/{template_id}")
async def update_template(template_id: int, template_data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        template = db.query(PromptTemplate).filter_by(id=template_id, user_id=current_user.id, is_deleted=False).first()
        if not template:
            raise HTTPException(404, "模板不存在")
            
        # 检查新名称是否与其他模板冲突
        if "name" in template_data and template_data["name"] != template.name:
            existing = db.query(PromptTemplate).filter_by(
                name=template_data["name"],
                user_id=current_user.id,
                is_deleted=False
            ).first()
            if existing:
                raise HTTPException(400, "模板名称已存在")
        
        # 更新模板
        for key, value in template_data.items():
            if key != "user_id":  # 不允许修改用户ID
                setattr(template, key, value)
            
        db.commit()
        
        # 广播更新消息
        try:
            await manager.broadcast_json({
                "type": "template_updated",
                "data": {
                    "id": template.id,
                    "name": template.name,
                    "user_id": current_user.id
                }
            })
        except Exception as e:
            logger.error(f"Failed to broadcast template update: {str(e)}")
        
        return {
            "id": template.id,
            "name": template.name,
            "message": "更新成功"
        }
        
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Template update failed (integrity error): {str(e)}")
        raise HTTPException(400, "模板更新失败：数据完整性错误")
        
    except HTTPException as e:
        raise e
        
    except Exception as e:
        db.rollback()
        logger.error(f"Template update failed: {str(e)}")
        raise HTTPException(500, f"模板更新失败: {str(e)}")

@router.delete("/{template_id}")
async def delete_template(template_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        template = db.query(PromptTemplate).filter_by(id=template_id, user_id=current_user.id, is_deleted=False).first()
        if not template:
            raise HTTPException(404, "模板不存在")
        
        template.is_deleted = True
        db.commit()

        # 广播删除消息
        try:
            await manager.broadcast_json({
                "type": "template_deleted",
                "data": {
                    "id": template_id,
                    "name": template.name,
                    "user_id": current_user.id
                }
            })
        except Exception as e:
            logger.error(f"Failed to broadcast template deletion: {str(e)}")
        
        return {"message": "删除成功"}
        
    except HTTPException as e:
        raise e
        
    except Exception as e:
        db.rollback()
        logger.error(f"Template deletion failed: {str(e)}")
        raise HTTPException(500, f"删除模板失败: {str(e)}")

@router.post("/{template_id}/restore")
async def restore_template(template_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        template = db.query(PromptTemplate).filter_by(id=template_id, user_id=current_user.id, is_deleted=True).first()
        if not template:
            raise HTTPException(404, "模板不存在或未被删除")
            
        # 检查是否存在同名未删除模板
        existing = db.query(PromptTemplate).filter_by(
            name=template.name,
            user_id=current_user.id,
            is_deleted=False
        ).first()
        if existing:
            raise HTTPException(400, "存在同名模板，无法恢复")
        
        template.is_deleted = False
        db.commit()

        # 广播恢复消息
        try:
            await manager.broadcast_json({
                "type": "template_restored",
                "data": {
                    "id": template_id,
                    "name": template.name,
                    "user_id": current_user.id
                }
            })
        except Exception as e:
            logger.error(f"Failed to broadcast template restoration: {str(e)}")
        
        return {"message": "恢复成功"}
        
    except HTTPException as e:
        raise e
        
    except Exception as e:
        db.rollback()
        logger.error(f"Template restoration failed: {str(e)}")
        raise HTTPException(500, f"恢复模板失败: {str(e)}") 