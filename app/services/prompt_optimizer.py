import asyncio
import json
import re
from typing import AsyncGenerator, Dict, Any, Optional
from ..models import LLMModel
from .model_adapter import ModelAdapter
from ..config import DEFAULT_API_KEY, DEFAULT_PROVIDER, DEFAULT_MODEL_NAME

class PromptOptimizer:
    def __init__(self, api_key: str = None, model: str = None, llm_model: LLMModel = None):
        self.model_name = model or DEFAULT_MODEL_NAME
        self.llm_model = llm_model
        
        # 创建ModelAdapter实例
        if self.llm_model:
            # 如果提供了LLMModel实例，使用它的配置
            self.adapter = ModelAdapter(
                provider=self.llm_model.provider,
                api_key=self.llm_model.api_key,
                base_url=self.llm_model.base_url
            )
        elif api_key:
            # 如果提供了API密钥，使用默认的提供商配置
            self.adapter = ModelAdapter(
                provider=DEFAULT_PROVIDER,
                api_key=api_key
            )
        elif DEFAULT_API_KEY:
            # 使用配置文件中的默认API密钥和提供商
            self.adapter = ModelAdapter(
                provider=DEFAULT_PROVIDER,
                api_key=DEFAULT_API_KEY
            )
        else:
            self.adapter = None
    
    async def optimize_prompt_stream(
        self,
        prompt: str,
        requirements: str = "",
        enable_deep_reasoning: bool = True,
        chat_model: str = None,
        language: str = "zh-CN",
        optimization_type: str = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式优化提示词
        """
        if not self.adapter:
            yield {"type": "error", "message": "未配置模型API密钥"}
            return
        
        # 如果有自定义模型实例，优先使用自定义模型的名称
        model = None
        if self.llm_model:
            model = self.llm_model.name
        else:
            model = chat_model or self.model_name
        
        try:
            # 第一阶段：深度推理（如果启用）
            deep_reasoning_content = ""
            if enable_deep_reasoning:
                yield {"type": "deep-reasoning-start"}
                
                reasoning_content = await self._deep_reasoning(prompt, requirements, model, language)
                deep_reasoning_content = reasoning_content
                
                # 模拟流式输出，将结果分成小块发送
                chunks = self._split_text_into_chunks(reasoning_content, 20)  # 每块约20个字符
                for chunk in chunks:
                    yield {"type": "deep-reasoning", "message": chunk}
                    await asyncio.sleep(0.01)  # 小延迟以模拟流式传输
                
                yield {"type": "deep-reasoning-end"}
            
            # 第二阶段：生成优化后的提示词
            yield {"type": "optimize-start"}
            
            optimized_content = await self._optimize_prompt(prompt, requirements, deep_reasoning_content, model, language, optimization_type)
            
            # 模拟流式输出
            chunks = self._split_text_into_chunks(optimized_content, 20)
            for chunk in chunks:
                yield {"type": "message", "message": chunk}
                await asyncio.sleep(0.01)
            
            yield {"type": "optimize-end"}
            
            # 第三阶段：评估优化结果
            yield {"type": "evaluate-start"}
            
            evaluation_content = await self._evaluate_optimization(prompt, requirements, model, language)
            
            # 模拟流式输出
            chunks = self._split_text_into_chunks(evaluation_content, 20)
            for chunk in chunks:
                yield {"type": "evaluate", "message": chunk}
                await asyncio.sleep(0.01)
            
            yield {"type": "evaluate-end"}
            yield {"type": "done", "done": True}
            
        except Exception as e:
            yield {"type": "error", "message": f"优化过程中发生错误: {str(e)}"}
    
    def _split_text_into_chunks(self, text: str, chunk_size: int) -> list:
        """将文本分割成小块，用于模拟流式输出"""
        if not text:
            return []
        return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    
    async def _deep_reasoning(
        self, prompt: str, requirements: str, model: str, language: str
    ) -> str:
        """深度推理阶段"""
        reasoning_prompt = self._build_deep_reasoning_prompt(prompt, requirements, language)
        
        try:
            # 使用ModelAdapter发送请求
            result = self.adapter.send_prompt(reasoning_prompt, {"model": model})
            if result and "output" in result:
                return result["output"]
            else:
                error_msg = result.get("error", "未知错误")
                return f"深度推理过程中发生错误: {error_msg}"
                    
        except Exception as e:
            return f"深度推理过程中发生错误: {str(e)}"
    
    async def _optimize_prompt(
        self, prompt: str, requirements: str, reasoning: str, model: str, language: str, optimization_type: str = None
    ) -> str:
        """优化提示词阶段"""
        optimize_prompt = self._build_optimize_prompt(prompt, requirements, reasoning, language, optimization_type)
        
        try:
            # 使用ModelAdapter发送请求
            result = self.adapter.send_prompt(optimize_prompt, {"model": model})
            if result and "output" in result:
                output = result["output"]
                
                # 检查返回内容是否是JSON格式的评估结果
                if output.strip().startswith('{') and output.strip().endswith('}'):
                    try:
                        # 尝试解析JSON
                        json_data = json.loads(output)
                        # 如果包含评分和理由字段，说明返回了评估结果而非优化提示词
                        if "评分" in json_data or "分数" in json_data or "score" in json_data or "rating" in json_data:
                            # 重新发送请求，强调返回优化后的提示词
                            retry_prompt = optimize_prompt + "\n\n请注意：你必须返回优化后的提示词文本，不要返回任何JSON格式的评估结果。直接输出优化后的提示词内容。"
                            retry_result = self.adapter.send_prompt(retry_prompt, {"model": model})
                            if retry_result and "output" in retry_result:
                                return retry_result["output"]
                    except:
                        # 如果JSON解析失败，说明不是JSON格式，直接返回原始输出
                        pass
                
                return output
            else:
                error_msg = result.get("error", "未知错误")
                return f"优化过程中发生错误: {error_msg}"
                    
        except Exception as e:
            return f"优化过程中发生错误: {str(e)}"
    
    def _build_optimize_prompt(self, prompt: str, requirements: str, reasoning: str, language: str, optimization_type: str = None) -> str:
        """构建优化提示词"""
        if language == "zh-CN":
            # 优先使用传入的优化类型，如果没有则进行关键词检测
            if optimization_type == "function-calling":
                is_function_calling = True
            else:
                # 检查是否是函数调用相关的提示词
                is_function_calling = any(keyword in requirements.lower() for keyword in [
                    "函数调用", "function calling", "函数", "function", "api调用", "api call"
                ])
            
            # 如果是函数调用相关提示词，使用更具体的优化指导
            if is_function_calling:
                return f"""
基于以下深度分析结果，请优化原始提示词，使其更适合函数调用场景：

深度分析结果：
{reasoning}

原始提示词：
{prompt}

优化要求：
{requirements}

请根据分析结果，从以下方面优化提示词：
1. 提高函数调用指令的清晰度和准确性
2. 确保参数说明详细准确
3. 使返回值格式规范明确
4. 完善错误处理机制描述
5. 提供清晰易懂的示例调用
6. 优化整体结构和逻辑

请直接输出优化后的完整提示词，不要包含任何额外说明。只需输出优化后的提示词文本本身。
严禁返回评估结果或评分，必须返回优化后的提示词原文。
"""
            # 否则使用通用优化指导
            else:
                return f"""
基于以下深度分析结果，请优化原始提示词：

深度分析结果：
{reasoning}

原始提示词：
{prompt}

优化要求：
{requirements}

请根据分析结果，从以下方面优化提示词：
1. 提高清晰度和准确性
2. 增强指令的完整性
3. 消除潜在歧义
4. 优化结构和逻辑
5. 满足特定要求

请直接输出优化后的提示词，不需要额外说明。
严禁返回评估结果或评分，必须返回优化后的提示词原文。
"""
        else:
            # 英文版本的函数调用优化指导
            if optimization_type == "function-calling":
                is_function_calling = True
            else:
                is_function_calling = any(keyword in requirements.lower() for keyword in [
                    "函数调用", "function calling", "函数", "function", "api调用", "api call"
                ])
            
            if is_function_calling:
                return f"""
Based on the following deep analysis results, please optimize the original prompt for function calling scenarios:

Deep Analysis Results:
{reasoning}

Original Prompt:
{prompt}

Optimization Requirements:
{requirements}

Please optimize the prompt from the following aspects based on the analysis results:
1. Improve clarity and accuracy of function calling instructions
2. Ensure detailed and accurate parameter descriptions
3. Make return value format clear and standardized
4. Improve error handling mechanism descriptions
5. Provide clear and understandable example calls
6. Optimize overall structure and logic

Please output the optimized prompt directly without any additional explanations. Only output the optimized prompt text itself.
DO NOT return evaluation results or scores. You MUST return the optimized prompt text only.
"""
            else:
                return f"""
Based on the following deep analysis results, please optimize the original prompt:

Deep Analysis Results:
{reasoning}

Original Prompt:
{prompt}

Optimization Requirements:
{requirements}

Please optimize the prompt from the following aspects based on the analysis results:
1. Improve clarity and accuracy
2. Enhance instruction completeness
3. Eliminate potential ambiguities
4. Optimize structure and logic
5. Meet specific requirements

Please output the optimized prompt directly without additional explanations.
DO NOT return evaluation results or scores. You MUST return the optimized prompt text only.
"""
    
    async def _evaluate_optimization(
        self, original_prompt: str, requirements: str, model: str, language: str
    ) -> str:
        """评估优化结果阶段"""
        evaluation_prompt = self._build_evaluation_prompt(original_prompt, requirements, language)
        
        try:
            # 使用ModelAdapter发送请求
            result = self.adapter.send_prompt(evaluation_prompt, {"model": model})
            if result and "output" in result:
                return result["output"]
            else:
                error_msg = result.get("error", "未知错误")
                return f"评估过程中发生错误: {error_msg}"
                    
        except Exception as e:
            return f"评估过程中发生错误: {str(e)}"
    
    def _build_deep_reasoning_prompt(self, prompt: str, requirements: str, language: str) -> str:
        """构建深度推理提示词"""
        if language == "zh-CN":
            return f"""
作为一个专业的提示词工程师，请对以下提示词进行深度分析和推理：

原始提示词：
{prompt}

优化要求：
{requirements}

请从以下维度进行深度分析：
1. 提示词的结构分析
2. 语义清晰度评估
3. 指令完整性检查
4. 潜在歧义识别
5. 改进方向建议

请详细分析每个维度，为后续优化提供理论基础。
"""
        else:
            return f"""
As a professional prompt engineer, please conduct a deep analysis and reasoning of the following prompt:

Original Prompt:
{prompt}

Optimization Requirements:
{requirements}

Please analyze from the following dimensions:
1. Structural analysis of the prompt
2. Semantic clarity assessment
3. Instruction completeness check
4. Potential ambiguity identification
5. Improvement direction suggestions

Please analyze each dimension in detail to provide a theoretical foundation for subsequent optimization.
"""
    
    def _build_evaluation_prompt(self, original_prompt: str, requirements: str, language: str) -> str:
        """构建评估提示词"""
        if language == "zh-CN":
            return f"""
请对提示词优化结果进行评估：

原始提示词：
{original_prompt}

优化要求：
{requirements}

请从以下维度进行评估并给出分数（1-10分）：

## 评估维度

### 1. 清晰度 (Clarity)
- 指令是否清晰明确
- 语言表达是否准确

### 2. 完整性 (Completeness)
- 是否包含所有必要信息
- 指令是否完整

### 3. 准确性 (Accuracy)
- 指令是否准确无误
- 是否避免了歧义

### 4. 可执行性 (Executability)
- AI是否能够准确理解并执行
- 指令是否具有可操作性

### 5. 优化效果 (Optimization Effect)
- 相比原始提示词的改进程度
- 是否满足优化要求

请以表格形式输出评估结果，并给出总体评价和建议。
"""
        else:
            return f"""
Please evaluate the prompt optimization results:

Original Prompt:
{original_prompt}

Optimization Requirements:
{requirements}

Please evaluate and score (1-10 points) from the following dimensions:

## Evaluation Dimensions

### 1. Clarity
- Are the instructions clear and explicit
- Is the language expression accurate

### 2. Completeness
- Does it contain all necessary information
- Are the instructions complete

### 3. Accuracy
- Are the instructions accurate and error-free
- Are ambiguities avoided

### 4. Executability
- Can AI accurately understand and execute
- Are the instructions actionable

### 5. Optimization Effect
- Degree of improvement compared to the original prompt
- Does it meet optimization requirements

Please output the evaluation results in table format and provide overall evaluation and suggestions.
"""
