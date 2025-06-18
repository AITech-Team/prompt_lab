from typing import List, Dict
from app.models import LLMModel
from app.services.model_adapter import ModelAdapter
import json
import os
import re
import logging
from app.config import DEFAULT_API_KEY, DEFAULT_PROVIDER, DEFAULT_MODEL_NAME

class ResponseEvaluator:
    def __init__(self, eval_model: LLMModel = None):
        """初始化评估器
        
        Args:
            eval_model: 用于评估的模型，默认使用配置文件中指定的模型
        """
        self.eval_model = eval_model
        if not self.eval_model:
            # 使用默认的ModelScope模型
            self.eval_model = LLMModel(
                provider=DEFAULT_PROVIDER,
                api_key=DEFAULT_API_KEY,
                model_name=DEFAULT_MODEL_NAME
            )
        self._validate_evaluator()
    
    def _validate_evaluator(self):
        """验证评估器配置"""
        if not self.eval_model:
            raise ValueError("未配置评估模型")

    def extract_json(self, text):
        """尝试从文本中提取JSON部分

        Args:
            text: 可能包含JSON的文本

        Returns:
            str: 提取出的JSON字符串
        """
        logger = logging.getLogger(__name__)

        # 检查输入是否为None
        if text is None:
            logger.warning("输入文本为None")
            return "{}"

        # 检查输入是否为空字符串
        if not text or (isinstance(text, str) and not text.strip()):
            logger.warning("输入文本为空")
            return "{}"

        # 确保text是字符串类型
        if not isinstance(text, str):
            logger.warning(f"输入不是字符串类型: {type(text)}")
            text = str(text)
            
        # 预处理文本
        text = text.strip()
        text = re.sub(r'[\u200b\ufeff\u200c]', '', text)  # 删除零宽字符
        text = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', text)  # 删除控制字符
        
        # 首先尝试直接解析
        try:
            json.loads(text)
            logger.info("成功直接解析JSON")
            return text
        except json.JSONDecodeError as e:
            logger.debug(f"直接解析JSON失败: {str(e)}")
        
        # 尝试修复常见的JSON格式问题
        text = re.sub(r',(\s*[}\]])', r'\1', text)  # 删除尾随逗号
        text = re.sub(r'\\([^"])', r'\1', text)  # 处理错误的转义
        text = re.sub(r'(?<!\\)"(\w+)":', r'"\1":', text)  # 修复键的引号
        text = re.sub(r'None', 'null', text)  # 替换Python的None
        text = re.sub(r'True', 'true', text)  # 替换Python的True
        text = re.sub(r'False', 'false', text)  # 替换Python的False
        
        # 尝试提取JSON对象
        patterns = [
            r'(\{[\s\S]*\})',  # 标准JSON对象
            r'(\[[\s\S]*\])',  # JSON数组
            r'```json\s*([\s\S]*?)\s*```',  # Markdown代码块中的JSON
            r'```\s*([\s\S]*?)\s*```',  # 其他代码块
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.MULTILINE)
            for match in matches:
                try:
                    potential_json = match.group(1).strip()
                    # 再次应用格式修复
                    potential_json = re.sub(r',(\s*[}\]])', r'\1', potential_json)
                    potential_json = re.sub(r'\\([^"])', r'\1', potential_json)
                    # 验证JSON
                    json.loads(potential_json)
                    logger.info(f"成功从模式 {pattern} 提取JSON")
                    return potential_json
                except Exception as e:
                    logger.debug(f"从模式 {pattern} 提取JSON失败: {str(e)}")
                    continue
        
        # 如果上述方法都失败，尝试提取最外层的花括号内容
        try:
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1 and start < end:
                potential_json = text[start:end+1]
                # 应用所有格式修复
                potential_json = re.sub(r',(\s*[}\]])', r'\1', potential_json)
                potential_json = re.sub(r'\\([^"])', r'\1', potential_json)
                potential_json = re.sub(r'(?<!\\)"(\w+)":', r'"\1":', potential_json)
                potential_json = re.sub(r'None', 'null', potential_json)
                potential_json = re.sub(r'True', 'true', potential_json)
                potential_json = re.sub(r'False', 'false', potential_json)
                # 验证JSON
                json.loads(potential_json)
                logger.info("成功从最外层花括号提取JSON")
                return potential_json
        except Exception as e:
            logger.error(f"从最外层花括号提取JSON失败: {str(e)}")

        logger.error("所有JSON提取方法都失败")
        logger.debug(f"原始文本内容: {text[:500]}...")  # 记录前500个字符用于调试

        # 返回一个有效的默认JSON结构
        return json.dumps({
            "scores": {
                "relevance": 0,
                "accuracy": 0,
                "completeness": 0,
                "clarity": 0
            },
            "reasons": {
                "relevance": "JSON解析失败",
                "accuracy": "JSON解析失败",
                "completeness": "JSON解析失败",
                "clarity": "JSON解析失败"
            },
            "suggestions": "评估结果解析失败，请检查模型输出格式"
        })

    def evaluate_response(self, prompt: str, response: str, criteria: List[Dict] = None) -> Dict:
        """评估模型响应质量
        
        Args:
            prompt: 原始提示词
            response: 模型响应
            criteria: 评估标准，默认为None使用预设标准
            
        Returns:
            Dict: 评估结果
        """
        logger = logging.getLogger(__name__)
        
        # 检查输入参数
        if not prompt or not response:
            logger.warning("输入参数为空")
            return self._get_default_evaluation("输入参数为空")

        try:
            # 预处理response
            if isinstance(response, dict):
                # 如果response是字典，尝试获取output字段
                if "output" not in response:
                    logger.error("Response字典中缺少output字段")
                    return self._get_default_evaluation("响应格式错误：缺少output字段")
                response = response["output"]
            elif not isinstance(response, str):
                # 如果不是字符串，转换为字符串
                response = str(response)
                
            # 清理response
            response = response.strip()
            response = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', response)  # 移除控制字符
            
            logger.debug(f"处理后的响应内容: {response[:100]}...")
        except Exception as e:
            logger.error(f"处理响应内容时出错: {str(e)}")
            return self._get_default_evaluation(f"响应处理错误: {str(e)}")

        if not criteria:
            criteria = [
                {"name": "relevance", "description": "回答与问题的相关性(1-10)"},
                {"name": "accuracy", "description": "回答的准确性(1-10)"},
                {"name": "completeness", "description": "回答的完整性(1-10)"},
                {"name": "clarity", "description": "表达的清晰度(1-10)"}
            ]

        try:
            if self.eval_model:
                # 使用指定的评估模型
                adapter = ModelAdapter(
                    provider=self.eval_model.provider,
                    api_key=self.eval_model.api_key,
                    base_url=self.eval_model.base_url
                )
                
                logger.debug(f"使用评估模型: {self.eval_model.provider}")
                
                # 根据评估模型类型选择不同的提示词格式
                if self.eval_model.provider == "modelscope":
                    evaluation_prompt = self._get_modelscope_evaluation_prompt(prompt, response)
                else:
                    evaluation_prompt = self._get_default_evaluation_prompt(prompt, response)
                
                result = adapter.send_prompt(evaluation_prompt)
                logger.debug(f"评估模型返回结果: {result}")
                
                # 检查API调用是否成功
                if not result:
                    logger.error("评估模型返回为空")
                    return self._get_default_evaluation("评估模型返回为空")

                # 详细检查result的结构
                if not isinstance(result, dict):
                    logger.error(f"评估模型返回值不是字典类型，实际类型: {type(result)}")
                    return self._get_default_evaluation("评估模型返回格式错误：不是字典类型")

                # 检查是否有错误信息
                if "error" in result and result["error"]:
                    error_msg = result.get("error", "未知错误")
                    logger.error(f"评估模型调用失败: {error_msg}")
                    return self._get_default_evaluation(f"评估模型调用失败: {error_msg}")

                # 检查output字段是否存在
                if "output" not in result:
                    logger.error("评估模型返回格式错误：缺少output字段")
                    logger.debug(f"实际返回的字段: {list(result.keys())}")
                    return self._get_default_evaluation("评估模型返回格式错误：缺少output字段")

                # 检查output是否为None
                if result["output"] is None:
                    logger.error("评估模型返回的output为None")
                    return self._get_default_evaluation("评估模型返回内容为空")

                output = result["output"]

                # 确保output是字符串类型
                if not isinstance(output, str):
                    logger.warning(f"评估模型返回的output不是字符串类型: {type(output)}")
                    output = str(output)
                
                try:
                    logger.debug(f"开始处理评估模型输出: {output[:200]}...")

                    # 尝试从结果中提取JSON
                    cleaned_output = self.extract_json(output)
                    logger.debug(f"清理后的JSON: {cleaned_output[:200]}...")

                    # 尝试解析JSON
                    evaluation = json.loads(cleaned_output)
                    logger.debug(f"解析后的评估结果: {evaluation}")

                    # 验证evaluation不为None
                    if evaluation is None:
                        raise ValueError("评估结果解析为None")

                    # 验证评估结果格式
                    if not isinstance(evaluation, dict):
                        raise ValueError(f"评估结果不是一个有效的JSON对象，实际类型: {type(evaluation)}")

                    # 检查必要字段
                    required_keys = ["scores", "reasons", "suggestions"]
                    missing_keys = []
                    for key in required_keys:
                        if key not in evaluation:
                            missing_keys.append(key)

                    if missing_keys:
                        raise ValueError(f"评估结果缺少必要字段: {missing_keys}")

                    # 安全地验证scores字段的结构
                    scores = evaluation.get("scores")
                    if scores is None:
                        raise ValueError("scores字段为None")
                    if not isinstance(scores, dict):
                        raise ValueError(f"scores字段不是字典类型，实际类型: {type(scores)}")

                    # 安全地验证reasons字段的结构
                    reasons = evaluation.get("reasons")
                    if reasons is None:
                        raise ValueError("reasons字段为None")
                    if not isinstance(reasons, dict):
                        raise ValueError(f"reasons字段不是字典类型，实际类型: {type(reasons)}")

                    logger.info("评估结果验证成功")
                    return evaluation

                except json.JSONDecodeError as e:
                    logger.error(f"JSON解析失败: {str(e)}")
                    logger.debug(f"无法解析的内容: {cleaned_output}")
                    return self._get_default_evaluation(f"JSON解析失败: {str(e)}")
                except Exception as e:
                    logger.error(f"处理评估结果时出错: {str(e)}")
                    logger.debug(f"原始输出: {output}")
                    return self._get_default_evaluation(f"评估结果格式错误: {str(e)}")
            else:
                # 使用默认的OpenAI模型
                adapter = ModelAdapter(
                    provider="openai",
                    api_key=DEFAULT_API_KEY
                )
                
                logger.debug("使用默认OpenAI模型进行评估")
                evaluation_prompt = self._get_default_evaluation_prompt(prompt, response)
                result = adapter.send_prompt(evaluation_prompt)
                logger.debug(f"OpenAI模型返回结果: {result}")
                
                if not result or not isinstance(result, dict) or "output" not in result:
                    logger.error("OpenAI模型返回格式错误")
                    return self._get_default_evaluation("OpenAI模型返回格式错误")
                
                try:
                    cleaned_output = self.extract_json(result["output"])
                    evaluation = json.loads(cleaned_output)

                    # 验证evaluation不为None
                    if evaluation is None:
                        raise ValueError("评估结果解析为None")

                    if not isinstance(evaluation, dict):
                        raise ValueError("评估结果不是一个有效的JSON对象")

                    required_keys = ["scores", "reasons", "suggestions"]
                    for key in required_keys:
                        if key not in evaluation:
                            raise ValueError(f"评估结果缺少必要字段: {key}")

                    # 安全地验证字段结构
                    scores = evaluation.get("scores")
                    if scores is None:
                        raise ValueError("scores字段为None")
                    if not isinstance(scores, dict):
                        raise ValueError(f"scores字段不是字典类型，实际类型: {type(scores)}")

                    reasons = evaluation.get("reasons")
                    if reasons is None:
                        raise ValueError("reasons字段为None")
                    if not isinstance(reasons, dict):
                        raise ValueError(f"reasons字段不是字典类型，实际类型: {type(reasons)}")

                    return evaluation
                    
                except Exception as e:
                    logger.error(f"处理评估结果时出错: {str(e)}")
                    return self._get_default_evaluation(f"评估结果格式错误: {str(e)}")
                    
        except Exception as e:
            logger.error(f"评估过程出现错误: {str(e)}")
            return self._get_default_evaluation(f"评估过程出现错误: {str(e)}")

    def _get_default_evaluation(self, error_msg: str) -> Dict:
        """获取默认的评估结果
        
        Args:
            error_msg: 错误信息
            
        Returns:
            Dict: 默认的评估结果
        """
        return {
            "scores": {
                "relevance": 0,
                "accuracy": 0,
                "completeness": 0,
                "clarity": 0
            },
            "reasons": {
                "relevance": "评估失败",
                "accuracy": "评估失败",
                "completeness": "评估失败",
                "clarity": "评估失败"
            },
            "suggestions": "评估过程中出现错误",
            "error": error_msg
        }

    def _get_modelscope_evaluation_prompt(self, prompt: str, response: str) -> str:
        """获取ModelScope评估模型的提示词
        
        Args:
            prompt: 原始提示词
            response: 模型响应
            
        Returns:
            str: 评估提示词
        """
        return f"""请评估以下AI回答的质量，并返回JSON格式的评估结果。

问题：{prompt}
回答：{response}

请按照以下格式返回评估结果（不要包含任何其他内容）：

{{
    "scores": {{
        "relevance": 相关性分数,
        "accuracy": 准确性分数,
        "completeness": 完整性分数,
        "clarity": 清晰度分数
    }},
    "reasons": {{
        "relevance": "相关性评分理由",
        "accuracy": "准确性评分理由",
        "completeness": "完整性评分理由",
        "clarity": "清晰度评分理由"
    }},
    "suggestions": "改进建议"
}}

要求：
1. 分数必须是1-10的整数
2. 分数不要加引号
3. 使用简洁的中文描述
4. 只返回JSON，不要有其他内容"""

    def _get_default_evaluation_prompt(self, prompt: str, response: str) -> str:
        """获取默认的评估提示词
        
        Args:
            prompt: 原始提示词
            response: 模型响应
            
        Returns:
            str: 评估提示词
        """
        return f"""你是一个专业的AI回答质量评估专家。请评估以下AI回答的质量，并以JSON格式返回评估结果。

评估对象：
问题：{prompt}
回答：{response}

请严格按照以下格式返回评估结果（不要包含任何其他内容）：

{{
    "scores": {{
        "relevance": 8,
        "accuracy": 7,
        "completeness": 9,
        "clarity": 8
    }},
    "reasons": {{
        "relevance": "这里是相关性评分理由",
        "accuracy": "这里是准确性评分理由",
        "completeness": "这里是完整性评分理由",
        "clarity": "这里是清晰度评分理由"
    }},
    "suggestions": "这里是具体的改进建议"
}}

注意：
1. 分数范围必须是1-10的整数
2. 分数不要加引号
3. 理由和建议使用简洁的中文描述
4. 只返回JSON，不要有其他内容"""

    def batch_evaluate(self, prompts: List[str], responses: List[str], criteria: List[Dict] = None) -> List[Dict]:
        """批量评估多个响应"""
        results = []
        for prompt, response in zip(prompts, responses):
            result = self.evaluate_response(prompt, response, criteria)
            results.append(result)
        return results 