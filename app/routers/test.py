from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import PromptTemplate, LLMModel, PromptHistory, TestRecord, User
from app.routers.auth import get_current_user
from app.services.model_adapter import ModelAdapter
from app.services.evaluator import ResponseEvaluator
from typing import List, Dict, Optional
import re
import json
import logging
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from io import StringIO
import csv
import datetime

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter()

def render_prompt(template: str, variables: dict):
    def replacer(match):
        var = match.group(1)
        return str(variables.get(var, f"{{{{{var}}}}}"))
    return re.sub(r"\{\{(\w+)\}\}", replacer, template)

class TestPromptRequest(BaseModel):
    content: str
    model_id: int
    variables: Dict = {}
    evaluator_model_id: Optional[int] = None

@router.post("/validate_api_key")
def validate_api_key(data: dict):
    """
    验证API密钥是否有效
    """
    try:
        adapter = ModelAdapter(
            provider=data["provider"],
            api_key=data["api_key"].strip(),
            base_url=data.get("base_url", "").strip()
        )
        
        is_valid = adapter.validate_api_key()
        return {"is_valid": is_valid}
    except Exception as e:
        logger.error(f"Failed to validate API key: {str(e)}")
        raise HTTPException(500, f"验证API密钥失败: {str(e)}")

@router.post("/prompt")
def test_prompt(request: TestPromptRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        # 获取选定的模型
        model = db.query(LLMModel).filter_by(id=request.model_id, is_deleted=False).first()
        if not model:
            logger.error(f"模型不存在: ID={request.model_id}")
            raise HTTPException(404, "模型不存在")

        logger.info(f"使用模型: {model.name} (ID={model.id})")

        # 创建模型适配器
        adapter = ModelAdapter(
            provider=model.provider,
            api_key=model.api_key,
            base_url=model.base_url
        )

        # 确保variables是一个有效的字典
        variables = request.variables if isinstance(request.variables, dict) else {}
        
        # 发送提示词获取响应
        logger.info(f"发送提示词: {request.content[:50]}...")
        result = adapter.send_prompt(request.content, variables)
        
        # 检查API调用是否成功
        if result.get("error"):
            error_message = result.get("output", "未知错误")
            logger.error(f"API调用失败: {error_message}")
            raise HTTPException(500, f"API调用失败: {error_message}")
        
        # 如果指定了评估模型，进行评估
        evaluation = None
        if request.evaluator_model_id:
            evaluator_model = db.query(LLMModel).filter_by(
                id=request.evaluator_model_id, 
                is_deleted=False
            ).first()
            
            if evaluator_model:
                try:
                    logger.info(f"使用评估模型: {evaluator_model.name} (ID={evaluator_model.id})")
                    evaluator = ResponseEvaluator(evaluator_model)
                    evaluation = evaluator.evaluate_response(
                        prompt=request.content,
                        response=result["output"]
                    )
                    
                    # 检查评估结果
                    if evaluation.get("error"):
                        logger.error(f"评估失败: {evaluation['error']}")
                        # 不抛出异常，继续使用带有错误信息的评估结果
                except Exception as e:
                    logger.error(f"评估过程出错: {str(e)}")
                    evaluation = {
                        "error": f"评估过程出错: {str(e)}",
                        "scores": {"relevance": 0, "accuracy": 0, "completeness": 0, "clarity": 0},
                        "reasons": {
                            "relevance": "评估失败",
                            "accuracy": "评估失败",
                            "completeness": "评估失败",
                            "clarity": "评估失败"
                        },
                        "suggestions": "评估过程中出现错误"
                    }

        # 保存测试记录
        test_record = None
        try:
            logger.info("保存测试记录")
            test_record = TestRecord(
                model_id=model.id,
                prompt=request.content,
                variables=variables,
                response=result["output"],
                evaluation=evaluation if isinstance(evaluation, dict) else None,
                user_id=current_user.id
            )
            db.add(test_record)
            db.commit()
            db.refresh(test_record)
            logger.info(f"测试记录保存成功: ID={test_record.id}")
        except Exception as e:
            logger.error(f"保存测试记录失败: {str(e)}")
            db.rollback()
            # 不抛出异常，继续返回测试结果

        response_data = {
            "model": model.name,
            "output": result["output"],
            "evaluation": evaluation,
            "record_id": test_record.id if test_record else None
        }
        
        # 如果是ModelScope模型且包含思考内容，添加到响应中
        if "thinking" in result:
            response_data["thinking"] = result["thinking"]
            
        return response_data

    except HTTPException as he:
        # 重新抛出HTTP异常
        raise he
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise HTTPException(500, f"测试失败: {str(e)}")

@router.get("/records")
def list_test_records(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取测试记录列表"""
    try:
        logger.info("获取测试记录列表")
        records = db.query(TestRecord).filter_by(user_id=current_user.id, is_deleted=False).order_by(TestRecord.created_at.desc()).all()
        logger.info(f"找到 {len(records)} 条测试记录")
        
        result = []
        for record in records:
            try:
                model_name = record.model.name if record.model else None
                template_name = record.template.name if record.template else None
                
                result.append({
                    "id": record.id,
                    "model": model_name,
                    "template": template_name,
                    "prompt": record.prompt,
                    "response": record.response,
                    "evaluation": record.evaluation,
                    "created_at": record.created_at
                })
            except Exception as e:
                logger.error(f"处理记录 {record.id} 时出错: {str(e)}")
        
        return result
    except Exception as e:
        logger.error(f"获取测试记录列表失败: {str(e)}")
        raise HTTPException(500, f"获取测试记录列表失败: {str(e)}")

@router.get("/records/export_csv")
def export_test_records_csv(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """导出测试记录为CSV（使用不会与路径参数冲突的路径）"""
    records = db.query(TestRecord).filter_by(user_id=current_user.id, is_deleted=False).all()
    
    output = StringIO()
    # 添加BOM头，使Excel能正确识别UTF-8编码的中文
    output.write('\ufeff')
    writer = csv.writer(output)
    
    # 写入表头
    writer.writerow([
        "ID", "模型", "模板", "提示词", "响应", "评估结果", "创建时间"
    ])
    
    # 写入数据
    for record in records:
        writer.writerow([
            record.id,
            record.model.name if record.model else "",
            record.template.name if record.template else "",
            record.prompt,
            record.response,
            json.dumps(record.evaluation, ensure_ascii=False) if record.evaluation else "",
            record.created_at.strftime("%Y-%m-%d %H:%M:%S") if record.created_at else ""
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8-sig",
        headers={"Content-Disposition": f"attachment; filename=test_records_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
    )

@router.get("/records/{record_id}")
def get_test_record(record_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取单个测试记录详情"""
    record = db.query(TestRecord).filter_by(id=record_id, user_id=current_user.id, is_deleted=False).first()
    if not record:
        raise HTTPException(404, "记录不存在或无权访问")
        
    model_name = record.model.name if record.model else None
    template_name = record.template.name if record.template else None
    
    return {
        "id": record.id,
        "model": model_name,
        "template": template_name,
        "prompt": record.prompt,
        "response": record.response,
        "evaluation": record.evaluation,
        "created_at": record.created_at
    }

@router.delete("/records/{record_id}")
def delete_test_record(record_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """删除测试记录"""
    record = db.query(TestRecord).filter_by(id=record_id, user_id=current_user.id).first()
    if not record:
        raise HTTPException(404, "记录不存在或无权访问")
    record.is_deleted = True
    db.commit()
    return {"message": "删除成功"}

@router.get("/records/export_all")
def export_all_test_records(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """导出所有测试记录为CSV（避免路由冲突）"""
    records = db.query(TestRecord).filter_by(user_id=current_user.id, is_deleted=False).all()
    
    output = StringIO()
    # 添加BOM头，使Excel能正确识别UTF-8编码的中文
    output.write('\ufeff')
    writer = csv.writer(output)
    
    # 写入表头
    writer.writerow([
        "ID", "模型", "模板", "提示词", "响应", "评估结果", "创建时间"
    ])
    
    # 写入数据
    for record in records:
        writer.writerow([
            record.id,
            record.model.name if record.model else "",
            record.template.name if record.template else "",
            record.prompt,
            record.response,
            json.dumps(record.evaluation, ensure_ascii=False) if record.evaluation else "",
            record.created_at.strftime("%Y-%m-%d %H:%M:%S") if record.created_at else ""
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8-sig",
        headers={"Content-Disposition": f"attachment; filename=test_records_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
    ) 