from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import json
import asyncio

from ..database import get_db
from ..services.prompt_optimizer import PromptOptimizer
from ..models import User, LLMModel
from .auth import get_current_user

router = APIRouter(prefix="", tags=["提示词优化"])

class PromptOptimizeRequest(BaseModel):
    prompt: str
    requirements: Optional[str] = ""
    enableDeepReasoning: bool = True
    chatModel: Optional[str] = None
    language: str = "zh-CN"
    modelId: Optional[int] = None  # 添加模型ID字段

class PromptTemplateParameterRequest(BaseModel):
    prompt: str
    language: str = "zh-CN"
    modelId: Optional[int] = None  # 添加模型ID字段

@router.post("/prompt/generate")
async def generate_optimized_prompt(
    request: PromptOptimizeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    生成优化后的提示词 - SSE流式响应
    """
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="提示词不能为空")
    
    # 获取模型实例，确保模型属于当前用户
    llm_model = None
    if request.modelId:
        llm_model = db.query(LLMModel).filter_by(id=request.modelId, user_id=current_user.id, is_deleted=False).first()
        if not llm_model:
            raise HTTPException(status_code=404, detail="指定的模型不存在或无权访问")
    
    # 创建优化器实例
    optimizer = PromptOptimizer(model=request.chatModel, llm_model=llm_model)
    
    async def generate_stream():
        try:
            yield "data: " + json.dumps({"type": "start", "message": "开始优化提示词"}) + "\n\n"
            
            # 传递参数时，如果使用自定义模型，则不传递chat_model参数
            chat_model_param = None if llm_model else request.chatModel
            
            async for chunk in optimizer.optimize_prompt_stream(
                prompt=request.prompt,
                requirements=request.requirements,
                enable_deep_reasoning=request.enableDeepReasoning,
                chat_model=chat_model_param,
                language=request.language,
                optimization_type="general"  # 通用优化类型
            ):
                yield "data: " + json.dumps(chunk) + "\n\n"
                await asyncio.sleep(0.01)  # 小延迟以确保流式传输
            
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            error_data = {"type": "error", "message": f"优化失败: {str(e)}"}
            yield "data: " + json.dumps(error_data) + "\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

@router.post("/prompt/optimize-function-calling")
async def optimize_function_calling_prompt(
    request: PromptOptimizeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    优化Function Calling提示词 - SSE流式响应
    """
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="提示词不能为空")
    
    # 获取模型实例，确保模型属于当前用户
    llm_model = None
    if request.modelId:
        llm_model = db.query(LLMModel).filter_by(id=request.modelId, user_id=current_user.id, is_deleted=False).first()
        if not llm_model:
            raise HTTPException(status_code=404, detail="指定的模型不存在或无权访问")
    
    optimizer = PromptOptimizer(model=request.chatModel, llm_model=llm_model)
    
    async def generate_stream():
        try:
            yield "data: " + json.dumps({"type": "start", "message": "开始优化Function Calling提示词"}) + "\n\n"
            
            # 为Function Calling特化的优化要求
            fc_requirements = f"""
{request.requirements}

特别针对Function Calling场景优化：
1. 确保函数调用指令清晰明确
2. 参数说明详细准确
3. 返回值格式规范
4. 错误处理机制完善
5. 示例调用清晰易懂
"""
            
            # 传递参数时，如果使用自定义模型，则不传递chat_model参数
            chat_model_param = None if llm_model else request.chatModel
            
            async for chunk in optimizer.optimize_prompt_stream(
                prompt=request.prompt,
                requirements=fc_requirements,
                enable_deep_reasoning=request.enableDeepReasoning,
                chat_model=chat_model_param,
                language=request.language,
                optimization_type="function-calling"  # 函数调用优化类型
            ):
                yield "data: " + json.dumps(chunk) + "\n\n"
                await asyncio.sleep(0.01)
            
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            error_data = {"type": "error", "message": f"优化失败: {str(e)}"}
            yield "data: " + json.dumps(error_data) + "\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

@router.post("/prompt/optimizeimageprompt")
async def optimize_image_prompt(
    request: PromptOptimizeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    优化图像生成提示词 - SSE流式响应
    """
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="提示词不能为空")
    
    # 获取模型实例，确保模型属于当前用户
    llm_model = None
    if request.modelId:
        llm_model = db.query(LLMModel).filter_by(id=request.modelId, user_id=current_user.id, is_deleted=False).first()
        if not llm_model:
            raise HTTPException(status_code=404, detail="指定的模型不存在或无权访问")
    
    optimizer = PromptOptimizer(model=request.chatModel, llm_model=llm_model)
    
    async def generate_stream():
        try:
            yield "data: " + json.dumps({"type": "start", "message": "开始优化图像生成提示词"}) + "\n\n"
            
            # 为图像生成特化的优化要求
            image_requirements = f"""
{request.requirements}

特别针对图像生成场景优化：
1. 视觉元素描述详细具体
2. 艺术风格明确清晰
3. 构图和色彩指导准确
4. 技术参数设置合理
5. 避免模糊和歧义表达
6. 增强视觉冲击力
"""
            
            # 传递参数时，如果使用自定义模型，则不传递chat_model参数
            chat_model_param = None if llm_model else request.chatModel
            
            async for chunk in optimizer.optimize_prompt_stream(
                prompt=request.prompt,
                requirements=image_requirements,
                enable_deep_reasoning=request.enableDeepReasoning,
                chat_model=chat_model_param,
                language=request.language,
                optimization_type="image"  # 图像生成优化类型
            ):
                yield "data: " + json.dumps(chunk) + "\n\n"
                await asyncio.sleep(0.01)
            
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            error_data = {"type": "error", "message": f"优化失败: {str(e)}"}
            yield "data: " + json.dumps(error_data) + "\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

@router.post("/prompt/generateprompttemplateparameters")
async def generate_prompt_template_parameters(
    request: PromptTemplateParameterRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    生成提示词模板参数（标题、描述、标签）
    """
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="提示词不能为空")
    
    # 获取模型实例，确保模型属于当前用户
    llm_model = None
    if request.modelId:
        llm_model = db.query(LLMModel).filter_by(id=request.modelId, user_id=current_user.id, is_deleted=False).first()
        if not llm_model:
            raise HTTPException(status_code=404, detail="指定的模型不存在或无权访问")
    
    optimizer = PromptOptimizer(llm_model=llm_model)
    
    try:
        # 构建生成模板参数的提示词
        if request.language == "zh-CN":
            system_prompt = f"""
请为以下提示词生成合适的模板参数：

提示词内容：
{request.prompt}

请生成以下信息并以JSON格式返回：
1. title: 简洁明确的标题（不超过50字）
2. description: 详细的描述说明（100-200字）
3. tags: 相关标签（用逗号分隔，3-5个标签）

返回格式：
{{
    "title": "标题",
    "description": "描述",
    "tags": "标签1,标签2,标签3"
}}
"""
        else:
            system_prompt = f"""
Please generate appropriate template parameters for the following prompt:

Prompt Content:
{request.prompt}

Please generate the following information and return in JSON format:
1. title: Concise and clear title (no more than 50 characters)
2. description: Detailed description (100-200 characters)
3. tags: Relevant tags (comma-separated, 3-5 tags)

Return format:
{{
    "title": "Title",
    "description": "Description", 
    "tags": "tag1,tag2,tag3"
}}
"""
        
        # 如果有配置模型，则使用模型生成参数
        if optimizer.adapter:
            result = optimizer.adapter.send_prompt(system_prompt)
            if result and "output" in result:
                # 尝试解析JSON
                try:
                    output = result["output"]
                    # 查找JSON部分
                    import re
                    json_match = re.search(r'\{.*\}', output, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(0)
                        params = json.loads(json_str)
                        return params
                except Exception as e:
                    # 解析失败，返回默认值
                    return {
                        "title": f"优化提示词 - {request.prompt[:20]}...",
                        "description": "通过AI智能分析生成的优化提示词模板，提供更好的指令清晰度和执行效果。",
                        "tags": "AI优化,提示词,智能生成",
                        "error": f"解析失败: {str(e)}"
                    }
        
        # 默认返回
        return {
            "title": f"优化提示词 - {request.prompt[:20]}...",
            "description": "通过AI智能分析生成的优化提示词模板，提供更好的指令清晰度和执行效果。",
            "tags": "AI优化,提示词,智能生成"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"生成模板参数失败: {str(e)}"
        )
